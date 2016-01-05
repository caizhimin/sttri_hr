# coding: utf8
from __future__ import unicode_literals
import requests
import datetime
import json
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from wechat_user.models import WXUser, Leave
from collections import Counter
from util.logger import log
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from django.http import HttpResponseServerError, HttpResponseNotFound
from util.qiniu_upload import my_qiniu
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
# Create your views here.


HOLIDAY_API_KEY = '24e16647f7490e170d68de37bc7254fc'

headers = {'apikey': HOLIDAY_API_KEY}


# 0 工作日
# 1 休息日
# 2 节假日


def get_work_days(days_list):
    """
    :param days_list:  ['20160101', '20160202']
    :return: if single days_list, return 0 or 1 or 2 ,
             if multiple days_list, return {"20130101":2,"20130103":2,,"20130201":"0"}
    """
    url = 'http://apis.baidu.com/xiaogg/holiday/holiday?d='
    prefix = ','.join(days_list)
    print '%s%s' % (url, prefix)
    try:
        response = requests.get('%s%s' % (url, prefix), headers=headers)
        return json.loads(response.text)
    except Exception, e:
        log.error(e)
        return None


def send_email(sender_email, receiver_email, receiver_name, applicant_name, leave_start_datetime, leave_end_datetime,
               leave_days, leave_type, email_type):
    """

    :param sender_email: 系统发件邮箱地址
    :param receiver_email: 收件者邮箱地址
    :param receiver_name: 收件者姓名
    :param applicant_name: 申请者姓名
    :param leave_start_datetime: 开始时间
    :param leave_end_datetime: 结束时间
    :param leave_days: 请假/外出天数
    :param leave_type :请假类型
    :param email_type: 邮件类型(通知批准or通知批准完成or通知拒绝)
    :return:
    """
    sender_email = 'jack_czm@vip.sina.com'
    # receiver_email = receiver.email
    # receiver_name = receiver.name

    # smtpserver = 'smtp.163.com'
    username = 'jack_czm@vip.sina.com'
    password = '64757687'
    if email_type == 'apply':
        subject = '%s%s申请通知' % (applicant_name, leave_type)
        msg = MIMEText('<html><h3>%s, 您好:</h3><div>您的部门同事%s申请%s至%s %s %s 天, 请您前往手机微信客户端进行批准。</div>'
                       '<br><div style="color:red">此为系统邮件, 请勿回复</div></html>' %
                       (receiver_name, applicant_name, leave_start_datetime, leave_end_datetime, leave_type,
                        leave_days), 'html', 'utf-8')
    if email_type == 'agree':
        subject = '%s%s申请通过' % (applicant_name, leave_type)
        msg = MIMEText('<html><h3>%s, 您好:</h3><div>您的%s申请%s至%s %s  天'
                       '<span style="color:red">申请未通过</span>, 请您前往手机微信客户端进行查看。</div>'
                       '<br><div style="color:red">此为系统邮件, 请勿回复</div></html>' %
                       (applicant_name, leave_type, leave_start_datetime, leave_end_datetime,
                        leave_days), 'html', 'utf-8')

    if email_type == 'reject':
        subject = '%s%s申请未通过' % (applicant_name, leave_type)
        msg = MIMEText('<html><h3>%s, 您好:</h3><div>您的%s申请%s至%s %s  天'
                       '<span style="color:red">申请未通过</span>, 请您前往手机微信客户端进行查看。</div>'
                       '<br><div style="color:red">此为系统邮件, 请勿回复</div></html>' %
                       (applicant_name, leave_type, leave_start_datetime, leave_end_datetime,
                        leave_days), 'html', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')


    smtp = smtplib.SMTP()
    smtp.connect('smtp.vip.sina.com')
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.set_debuglevel(1)
    smtp.login(username, password)
    smtp.sendmail(sender_email, receiver_email, msg.as_string())
    smtp.quit()


def calculate_leave_day(request):
    """
    计算请假开始日期至结束日期之间的工作日天数
    :param request:
    :return:
    """
    start_date = request.POST.get('start_date', '').replace('-', '')
    end_date = request.POST.get('end_date', '').replace('-', '')
    start_time = request.POST.get('start_time', '')
    end_time = request.POST.get('end_time', '')
    if start_date and end_date and start_time and end_time:
        start_datetime = datetime.datetime.strptime(start_date, "%Y%m%d").date()
        end_datetime = datetime.datetime.strptime(end_date, "%Y%m%d").date()
        day_list = [str(start_datetime+datetime.timedelta(days=i)).replace('-', '')
                    for i in xrange((end_datetime - start_datetime).days+1)]
        day_status = get_work_days(day_list)
        if day_status:
            print day_list
            print(day_status)
            if isinstance(day_status, dict):
                leave_days_count = Counter(v for k, v in day_status.items())[0]
            else:
                leave_days_count = 1
        else:
            leave_days_count = 1
        if (start_time == '08:30' and end_time == '13:00') or (start_time == '13:00' and end_time == '17:00'):
            leave_days_count -= 0.5
        elif start_time == '13:00' and end_time == '13:00':
            leave_days_count -= 1
        if day_status == '1' or day_status == '2':  # single day
                leave_days_count = 0
    else:
        leave_days_count = 0
    return HttpResponse(leave_days_count)


def leave_apply(request):
    """
    请假post提交
    :param request:
    :return:
    """
    group = request.POST.get('group')
    leave_type = request.POST.get('leave_type', '')
    message = request.POST.get('message', '')
    start_date = request.POST.get('start_date', '')
    end_date = request.POST.get('end_date', '')
    start_time = request.POST.get('start_time', '')
    end_time = request.POST.get('end_time', '')
    leave_days = float(request.POST.get('leave_days_count', 0))
    open_id = request.session.get('open_id')
    wxuser = WXUser.objects.get(wx_openid=open_id)
    create_time = datetime.datetime.now()
    leave_start_datetime = start_date + ' ' + start_time
    leave_end_datetime = end_date + ' ' + end_time

    # send Email
    direct_director = WXUser.objects.get(pk=wxuser.direct_director.pk)
    direct_director_email = direct_director.email
    direct_director_name = direct_director.name
    send_email('jack_czm@vip.sina.com', direct_director_email, direct_director_name, wxuser.name, leave_start_datetime,
               leave_end_datetime, leave_days, '请假', 'apply')

    if group == '1' and leave_type in ('2', '3'):  # 病假or产假 , 返回新增leave_id用于上传图片页面
        new_leave_id = Leave.objects.get_or_create(group=int(group), type=leave_type,
                                                   leave_start_datetime=leave_start_datetime,
                                                   leave_end_datetime=leave_end_datetime, create_time=create_time,
                                                   leave_days=leave_days, leave_reason=message, remark='',
                                                   applicant_name=wxuser.name, applicant_openid=wxuser.wx_openid,
                                                   status=1, next_dealer=wxuser.direct_director, refuse_reason='')[0].id
        if leave_type == '2':
            return HttpResponse(json.dumps({'leave_type': 'sick_leave', 'new_leave_id': new_leave_id}))
        else:
            return HttpResponse(json.dumps({'leave_type': 'pregnant_leave', 'new_leave_id': new_leave_id}))
    else:  # 事假or年假

        Leave.objects.create(group=int(group), type=leave_type, leave_start_datetime=leave_start_datetime,
                             leave_end_datetime=leave_end_datetime, create_time=create_time, leave_days=leave_days,
                             leave_reason=message, remark='', applicant_name=wxuser.name,
                             applicant_openid=wxuser.wx_openid,
                             status=1, next_dealer=wxuser.direct_director, refuse_reason='')
        # minus vacation days
        if wxuser.legal_vacation_days >= leave_days:  # 优先扣除法定年假，再扣企业年假
            wxuser.legal_vacation_days -= leave_days
        else:
            wxuser.company_vacation_days -= (leave_days - wxuser.legal_vacation_days)
            wxuser.legal_vacation_days = 0
        wxuser.save()
    return HttpResponse('Success')


def out_apply(request):
    """
    外出post提交
    :param request:
    :return:
    """
    group = request.POST.get('group')
    leave_type = request.POST.get('leave_type', '')
    message = request.POST.get('message', '')
    start_date = request.POST.get('start_date', '')
    end_date = request.POST.get('end_date', '')
    start_time = request.POST.get('start_time', '')
    end_time = request.POST.get('end_time', '')
    leave_days = float(request.POST.get('leave_days_count', 0))
    open_id = request.session.get('open_id')
    wxuser = WXUser.objects.get(wx_openid=open_id)
    create_time = datetime.datetime.now()
    leave_start_datetime = start_date + ' ' + start_time
    leave_end_datetime = end_date + ' ' + end_time
    Leave.objects.create(group=int(group), type=leave_type, leave_start_datetime=leave_start_datetime,
                         leave_end_datetime=leave_end_datetime, create_time=create_time, leave_days=leave_days,
                         leave_reason=message, remark='', applicant_name=wxuser.name, applicant_openid=wxuser.wx_openid,
                         status=1, next_dealer=wxuser.direct_director, refuse_reason='')

    # send Email
    direct_director = WXUser.objects.get(pk=wxuser.direct_director.pk)
    direct_director_email = direct_director.email
    direct_director_name = direct_director.name
    send_email('jack_czm@vip.sina.com', direct_director_email, direct_director_name, wxuser.name, leave_start_datetime,
               leave_end_datetime, leave_days, '请假', 'apply')

    return HttpResponse('Success')


def approve(request):
    """
    批准
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    next_dealer_id = int(request.POST.get('next_dealer_id'))
    applicant_wx_openid = request.POST.get('applicant_wx_openid', '')
    result = request.POST.get('result', '')
    refuse_reason = request.POST.get('refuse_reason', '')
    applicant_wx_user = WXUser.objects.get(wx_openid=applicant_wx_openid)
    leave = Leave.objects.get(pk=leave_id)
    print('result', result)
    if result == 'agree':  # 同意
        if int(applicant_wx_user.direct_director_id) == next_dealer_id:  # 第一级审批, 即直接主管审批
            dept_leader_id = applicant_wx_user.dept_leader_id
            dept_leader = WXUser.objects.get(pk=dept_leader_id)
            leave.next_dealer_id = dept_leader_id
            # 发邮件给直接主管审批
            send_email('jack_czm@vip.sina.com', dept_leader.email, dept_leader.name, applicant_wx_user.name,
                       leave.leave_start_datetime, leave.leave_end_datetime, leave.leave_days,
                       '请假' if leave.group == 1 else '外出', 'apply')

        if int(applicant_wx_user.dept_leader_id) == next_dealer_id:  # 第二级审批, 即部门领导审批
            if leave.leave_days > 1 and leave.type == 1:  # 如果是事假且大于1天，通知HR部门审批
                leave.next_dealer_id = 999  # todo 先假设HR审批账号id为999
                send_email('jack_czm@vip.sina.com', 'HR@com', applicant_wx_user.name,  # todo HR邮箱待填写
                           applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                           leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
            else:
                leave.next_dealer_id = None
                leave.status = 3
                leave.deal_end_time = datetime.datetime.now()
                # 发邮件给申请者, 通知审批通过
                send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name,
                           applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                           leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')

        if leave.next_dealer_id == 999 and leave.type == 1:  # todo HR审批大于1天的事假
            leave.next_dealer_id = None
            leave.status = 3
            leave.deal_end_time = datetime.datetime.now()
            # 发邮件给申请者, 通知审批通过
            send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name,
                       applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                       leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
        leave.save()
        return HttpResponse('Agree')

    else:
        # 拒绝
        # 发邮件给申请者, 通知审批未通过
        send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name, applicant_wx_user.name,
                   leave.leave_start_datetime, leave.leave_end_datetime, leave.leave_days,
                   '请假' if leave.group == 1 else '外出', 'reject')
        leave.next_dealer_id = None
        leave.status = 2
        leave.deal_end_time = datetime.datetime.now()
        leave.refuse_reason = refuse_reason
        leave.save()
        return HttpResponse('Reject')


def cancel(request):
    """
    取消自己的请假/外出申请
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    leave = Leave.objects.get(pk=leave_id)
    leave.status = 0
    leave.save()
    return HttpResponse('Success')


def done(request):
    """
    注销自己的请假
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    actual_level_days = float(request.POST.get('actual_level_days'))
    leave = Leave.objects.get(pk=leave_id)
    apply_leave_days = float(leave.leave_days)
    if actual_level_days > apply_leave_days:  # 销假天数大于申请天数
        return HttpResponse('Fail')
    else:
        # 申请人 法定年假 需 补上  申请天数-销假天数
        applicant_openid = leave.applicant_openid
        applicant = WXUser.objects.get(wx_openid=applicant_openid)
        redundant_leave_days = apply_leave_days - actual_level_days
        applicant.legal_vacation_days += redundant_leave_days
        applicant.save()
        leave.status = 4
    leave.save()
    return HttpResponse('Success')


@csrf_exempt
def sick_leave_img_upload_page(request, pk):
    """
    病假证明上传页面
    :param request:
    :return:
    """
    if request.method == 'POST':
        img_str = request.POST.get('img_str')
        sick_leave = Leave.objects.get(pk=pk)
        if img_str and sick_leave:
            sick_leave.attach_photo = img_str
            sick_leave.save()
            return HttpResponse('Success')
        else:
            return HttpResponseServerError()
    return render_to_response('sick_leave_img_upload.html',  context_instance=RequestContext(request))


@csrf_exempt
def pregnant_leave_img_upload_page(request, pk):
    """
    产假证明上传页面
    :param request:
    :return:
    """
    if request.method == 'POST':
        img_str = request.POST.get('img_str')
        sick_leave = Leave.objects.get(pk=pk)
        if img_str and sick_leave:
            sick_leave.attach_photo = img_str
            sick_leave.save()
            return HttpResponse('Success')
        else:
            return HttpResponseServerError()
    return render_to_response('pregnant_leave_img_upload.html',  context_instance=RequestContext(request))


def img_upload(request):
    """
    上传单张图片到七牛，返回url
    :param request:
    :return:
    """
    img = request.FILES.get('img')
    i_img = Image.open(img)
    i_img.thumbnail((500, 500), Image.ANTIALIAS)
    b = io.BytesIO()
    i_img.save(b, 'JPEG')  # 存入缓存
    image_bytes = b.getvalue()  # 获得二进制文本
    url = my_qiniu.image_upload(image_bytes)
    return HttpResponse(url)





