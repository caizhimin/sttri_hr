# coding: utf8
from __future__ import unicode_literals
import datetime
import json
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from wechat_user.models import WXUser, Leave
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from django.http import HttpResponseServerError, HttpResponseNotFound
from util.qiniu_upload import my_qiniu
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
from util.wechat_oauth import send_msg
from util.date import get_work_days


LEAVE_TYPE_LIST = (
    (0, u'法定年假'),
    (8, u'企业年假'),
    (9, u'积点兑换年假'),
    (1, u'事假'),
    (2, u'病假'),
    (3, u'产假'),
    (4, u'会议'),
    (5, u'培训'),
    (6, u'出差'),
    (7, u'其他'),
)

LEAVE_TYPE_DICT = dict(LEAVE_TYPE_LIST)


# Create your views here.
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
                       '<span style="color:red">申请已通过</span>, 请您前往手机微信客户端进行查看。</div>'
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
        print(day_status)
        if isinstance(day_status, dict):  # several days
            counter = Counter(v for k, v in day_status.items())
            print(counter.get('1'), counter.get('2'))
            # 不以周末或者法定节假日开始或者结束的情况
            leave_days_count = counter.get('0')
            if not day_status.get(day_list[0]) in (1, 2) and not day_status.get(day_list[-1]) in (1, 2):
                if (start_time == '08:30' and end_time == '13:30') or (start_time == '11:00' and end_time == '17:00'):
                    leave_days_count -= 0.5
                elif start_time == '11:00' and end_time == '13:30':
                    leave_days_count -= 1
            elif day_status.get(day_list[0]) in (1, 2) and day_status.get(day_list[-1]) == 0:  # 以周末或者法定节假日开始的情况
                if end_time == '13:30':
                    leave_days_count -= 0.5
            elif day_status.get(day_list[-1]) in (1, 2) and day_status.get(day_list[0]) == 0:  # 以周末或者法定节假日结束的情况
                if start_time == '11:00':
                    leave_days_count -= 0.5
            else:  # 开始结束 全都是周末或者法定节假日
                leave_days_count = 0
        else:  # single day
            if day_status in (1, 2):  # single day (weekend or vacation)
                leave_days_count = 0
            else:  # working day
                if (start_time == '08:30' and end_time == '13:30') or (start_time == '11:00' and end_time == '17:00'):
                    leave_days_count = 0.5
                elif start_time == '11:00' and end_time == '13:30':
                    leave_days_count = 0
                elif start_time == '08:30' and end_time == '17:00':
                    leave_days_count = 1
                else:
                    leave_days_count = 0
    else:
        leave_days_count = 0
    return HttpResponse(leave_days_count)

# if (start_time == '08:30' and end_time == '13:30') or (start_time == '11:00' and end_time == '17:00'):
#                     leave_days_count -= 0.5
#                 elif start_time == '11:00' and end_time == '13:30':
#                     leave_days_count -= 1

# counter = Counter(v for k, v in day_status.items())


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
    user_id = request.session.get('user_id')
    # user_id = 'caizm'  # todo  delete
    wxuser = WXUser.objects.get(wx_openid=user_id)
    create_time = datetime.datetime.now()
    leave_start_datetime = start_date + ' ' + start_time
    leave_end_datetime = end_date + ' ' + end_time
    try:
        department_timekeeper = WXUser.objects.get(department=wxuser.department, is_timekeeper=1)
    except Exception, error:
        print ('error', error)
        department_timekeeper = WXUser.objects.get(id=999)
    # send Email
    direct_director = WXUser.objects.get(pk=wxuser.direct_director.pk)
    direct_director_email = direct_director.email
    direct_director_name = direct_director.name
    # send_email('jack_czm@vip.sina.com', direct_director_email, direct_director_name, wxuser.name, leave_start_datetime,
    #            leave_end_datetime, leave_days, '请假', 'apply')

    last_leave = Leave.objects.filter(applicant_openid=user_id).exclude(status=0).last()  # 最后的leave（未取消）
    if last_leave:
        last_leave_start_time = last_leave.leave_start_datetime
        last_leave_end_time = last_leave.leave_end_datetime
        start_datetime = datetime.datetime.strptime(start_date + ' ' + start_time, '%Y-%m-%d %H:%M')
        end_datetime = datetime.datetime.strptime(end_date + ' ' + end_time, '%Y-%m-%d %H:%M')

        # 申请开始时间或者结束时间在最后条记录中,不能再申请
        if not ((end_datetime < last_leave_start_time) or (start_datetime > last_leave_end_time)):
            return HttpResponse(json.dumps({'leave_type': 'Not Allowed'}))
        # # 存在未销假的假期
        # if Leave.objects.filter(applicant_openid=user_id, status=3, group=1).exists():
        #     return HttpResponse(json.dumps({'leave_type': 'Exists leave not completed'}))

    if group == '1' and leave_type in ('2', '3'):  # 病假or产假 , 返回新增leave_id用于上传图片页面
        if leave_days >= 5:  # 病假超5天或者产假通知李赫
            send_msg('lih', applicant_name=wxuser.department+'部门'+wxuser.name, start_datetime=str(leave_start_datetime),
                     end_datetime=str(leave_end_datetime), _type=LEAVE_TYPE_DICT[int(leave_type)],
                     days=leave_days, msg_type='长病假/产假')
        new_leave_id = Leave.objects.create(department=wxuser.department, group=int(group), type=leave_type,
                                            leave_start_datetime=leave_start_datetime,
                                            leave_end_datetime=leave_end_datetime, create_time=create_time,
                                            leave_days=leave_days, leave_reason=message, remark='',
                                            applicant_name=wxuser.name, applicant_openid=wxuser.wx_openid,
                                            status=1,
                                            next_dealer=department_timekeeper,
                                            refuse_reason='').id
        # 病产假通知部门考勤员准备查看申请资料
        send_msg(receive_open_id=department_timekeeper.wx_openid, applicant_name=wxuser.name,
                 start_datetime=str(leave_start_datetime),
                 end_datetime=str(leave_end_datetime), _type=LEAVE_TYPE_DICT[int(leave_type)],
                 days=leave_days, msg_type='sick_apply' if leave_type == '2' else 'pregnant_apply')
        if leave_type == '2':
            return HttpResponse(json.dumps({'leave_type': 'sick_leave', 'new_leave_id': new_leave_id}))
        else:
            return HttpResponse(json.dumps({'leave_type': 'pregnant_leave', 'new_leave_id': new_leave_id}))

    elif leave_type in ('0', '1', '8', '9'):  # 事假or年假or积点兑换年假
        Leave.objects.create(department=wxuser.department, group=int(group), type=leave_type,
                             leave_start_datetime=leave_start_datetime,
                             leave_end_datetime=leave_end_datetime, create_time=create_time, leave_days=leave_days,
                             leave_reason=message, remark='', applicant_name=wxuser.name,
                             applicant_openid=wxuser.wx_openid,
                             status=1, next_dealer=wxuser.direct_director, refuse_reason='')
        # minus vacation days
        if leave_type == '0':  # 申请法定年假
            wxuser.legal_vacation_days -= leave_days
        elif leave_type == '8':  # 申请企业年假
            wxuser.company_vacation_days -= leave_days
        elif leave_type == '9':  # 申请积点兑换年假
            wxuser.flexible_vacation_days -= leave_days
        wxuser.save()
        send_msg(receive_open_id=direct_director.wx_openid, applicant_name=wxuser.name,
                 start_datetime=str(leave_start_datetime),
                 end_datetime=str(leave_end_datetime), _type=LEAVE_TYPE_DICT[leave_type], days=leave_days, msg_type='apply')

    else:  # 其他假期通知李赫
        Leave.objects.create(department=wxuser.department, group=int(group), type=leave_type,
                             leave_start_datetime=leave_start_datetime,
                             leave_end_datetime=leave_end_datetime, create_time=create_time, leave_days=leave_days,
                             leave_reason=message, remark='', applicant_name=wxuser.name,
                             applicant_openid=wxuser.wx_openid,
                             status=1, next_dealer=wxuser.direct_director, refuse_reason='')
        send_msg(receive_open_id=direct_director.wx_openid, applicant_name=wxuser.name,
                 start_datetime=str(leave_start_datetime),
                 end_datetime=str(leave_end_datetime), _type='其他请假'+'(理由:'+message+')',
                 days=leave_days, msg_type='apply_other_leave')
    return HttpResponse(json.dumps({'leave_type': 'leaves'}))


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
    user_id = request.session.get('user_id')
    wxuser = WXUser.objects.get(wx_openid=user_id)
    create_time = datetime.datetime.now()
    leave_start_datetime = start_date + ' ' + start_time
    leave_end_datetime = end_date + ' ' + end_time

    last_leave = Leave.objects.filter(applicant_openid=user_id).exclude(status=0).last()  # 最后的leave（未取消）
    if last_leave:
        last_leave_start_time = last_leave.leave_start_datetime
        last_leave_end_time = last_leave.leave_end_datetime
        start_datetime = datetime.datetime.strptime(start_date + ' ' + start_time, '%Y-%m-%d %H:%M')
        end_datetime = datetime.datetime.strptime(end_date + ' ' + end_time, '%Y-%m-%d %H:%M')

        # 申请开始时间或者结束时间在最后条记录中,不能再申请
        if not ((end_datetime < last_leave_start_time) or (start_datetime > last_leave_end_time)):
            return HttpResponse(json.dumps({'leave_type': 'Not Allowed'}))

    # 存在未销假的假期
    # if Leave.objects.filter(applicant_openid=user_id, status=3, group=1).exists():
    #     return HttpResponse(json.dumps({'leave_type': 'Exists leave not completed'}))

    Leave.objects.create(department=wxuser.department, group=int(group), type=leave_type, leave_start_datetime=leave_start_datetime,
                         leave_end_datetime=leave_end_datetime, create_time=create_time, leave_days=leave_days,
                         leave_reason=message, remark='', applicant_name=wxuser.name, applicant_openid=wxuser.wx_openid,
                         status=1, next_dealer=wxuser.direct_director, refuse_reason='')

    # send Email
    direct_director = WXUser.objects.get(pk=wxuser.direct_director.pk)
    direct_director_email = direct_director.email
    direct_director_name = direct_director.name
    # send_email('jack_czm@vip.sina.com', direct_director_email, direct_director_name, wxuser.name, leave_start_datetime,
    #            leave_end_datetime, leave_days, '外出', 'apply')
    send_msg(receive_open_id=direct_director.wx_openid, applicant_name=wxuser.name,
             start_datetime=str(leave_start_datetime),
             end_datetime=str(leave_end_datetime), _type='外出' + LEAVE_TYPE_DICT[int(leave_type)], days=leave_days,
             msg_type='apply')
    return HttpResponse(json.dumps({'leave_type': 'Success'}))


def approve(request):
    """
    批准
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    next_dealer_id = int(request.POST.get('next_dealer_id'))
    next_dealer = WXUser.objects.get(pk=next_dealer_id)
    applicant_wx_openid = request.POST.get('applicant_wx_openid', '')
    result = request.POST.get('result', '')
    refuse_reason = request.POST.get('refuse_reason', '')
    applicant_wx_user = WXUser.objects.get(wx_openid=applicant_wx_openid)
    direct_director_id = applicant_wx_user.direct_director_id
    direct_director = WXUser.objects.get(pk=direct_director_id)
    dept_leader_id = applicant_wx_user.dept_leader_id
    dept_leader = WXUser.objects.get(pk=dept_leader_id)
    leave = Leave.objects.get(pk=leave_id)
    if result == 'agree':  # 同意
        if leave.group == 1:  # 同意请假
            if leave.type in (2, 3) and WXUser.objects.get(id=next_dealer_id).is_timekeeper == 1:
                # 考勤员审核病产假通过后传给直接主管

                leave.next_dealer_id = direct_director
                send_msg(receive_open_id=direct_director.wx_openid, applicant_name=applicant_wx_user.name,
                         start_datetime=str(leave.leave_start_datetime),
                         end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                         days=leave.leave_days,  msg_type='agree')
            # 先判断是不是部门领导，如果判断是的话就直接通过了，有可能部门领导和直接主管是同一人
            elif int(applicant_wx_user.dept_leader_id) == next_dealer_id:  # 第二级审批, 即部门领导审批
                if leave.leave_days > 1 and leave.type == 1:  # 部门领导审批通过, 如果是事假且大于1天，跳转通知HR部门审批
                    leave.next_dealer_id = 999  # todo 先假设HR审批账号id为999
                    # send_email('jack_czm@vip.sina.com', 'HR@com', applicant_wx_user.name,  # todo HR邮箱待填写
                    #            applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                    #            leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
                    send_msg(receive_open_id='lih', applicant_name=applicant_wx_user.name,
                             start_datetime=str(leave.leave_start_datetime),
                             end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                             days=leave.leave_days,  msg_type='agree')

                # 部门领导审批通过
                else:
                    leave.next_dealer_id = None
                    leave.status = 3
                    leave.deal_end_time = datetime.datetime.now()
                    # 发邮件给申请者, 通知审批通过
                    # send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name,
                    #            applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                    #            leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
                    send_msg(receive_open_id=applicant_wx_user.wx_openid, applicant_name=applicant_wx_user.name,
                             start_datetime=str(leave.leave_start_datetime),
                             end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                             days=leave.leave_days,  msg_type='approve')

            elif int(applicant_wx_user.direct_director_id) == next_dealer_id:  # 第一级审批, 即直接主管审批
                leave.next_dealer_id = dept_leader_id
                # 发邮件给直接主管审批
                # send_email('jack_czm@vip.sina.com', dept_leader.email, dept_leader.name, applicant_wx_user.name,
                #            leave.leave_start_datetime, leave.leave_end_datetime, leave.leave_days,
                #            '请假' if leave.group == 1 else '外出', 'apply')
                send_msg(receive_open_id=dept_leader.wx_openid, applicant_name=applicant_wx_user.name,
                         start_datetime=str(leave.leave_start_datetime),
                         end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                         days=leave.leave_days,  msg_type='agree')

            elif leave.next_dealer_id == 999 and leave.type == 1:  # todo HR审批大于1天的事假
                leave.next_dealer_id = None
                leave.status = 3
                leave.deal_end_time = datetime.datetime.now()
                # 发邮件给申请者, 通知审批通过
                # send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name,
                #            applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                #            leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')

                send_msg(receive_open_id=applicant_wx_user.wx_openid, applicant_name=applicant_wx_user.name,
                         start_datetime=str(leave.leave_start_datetime),
                         end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                         days=leave.leave_days,  msg_type='approve')

        else:  # 同意外出

            leave.next_dealer_id = None
            leave.status = 3
            leave.deal_end_time = datetime.datetime.now()
            # 发邮件给申请者, 通知审批通过
            # send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name,
            #            applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
            #            leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
            send_msg(receive_open_id=applicant_wx_user.wx_openid, applicant_name=applicant_wx_user.name,
                     start_datetime=str(leave.leave_start_datetime),
                     end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                     days=leave.leave_days,  msg_type='approve')

            if applicant_wx_user.is_leader == 1:  # 中层领导外出需发邮件给HR
                # send_email('jack_czm@vip.sina.com', 'HR@com', applicant_wx_user.name,  # todo HR邮箱待填写
                #            applicant_wx_user.name, leave.leave_start_datetime, leave.leave_end_datetime,
                #            leave.leave_days, '请假' if leave.group == 1 else '外出', 'agree')
                send_msg(receive_open_id='lih', applicant_name=applicant_wx_user.name,
                         start_datetime=str(leave.leave_start_datetime),
                         end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                         days=leave.leave_days,  msg_type='approve')
        # 同意后加入 all_dealers
        leave.all_dealers += (next_dealer.wx_openid + ' ')
        leave.save()
        return HttpResponse('Agree')

    else:
        # 拒绝
        # 发邮件给申请者, 通知审批未通过
        # send_email('jack_czm@vip.sina.com', applicant_wx_user.email, applicant_wx_user.name, applicant_wx_user.name,
        #            leave.leave_start_datetime, leave.leave_end_datetime, leave.leave_days,
        #            '请假' if leave.group == 1 else '外出', 'reject')
        send_msg(receive_open_id=applicant_wx_user.wx_openid, applicant_name=applicant_wx_user.name,
                 start_datetime=str(leave.leave_start_datetime),
                 end_datetime=str(leave.leave_end_datetime), _type='请假' if leave.group == 1 else '外出',
                 days=leave.leave_days,  msg_type='reject')

        # 拒绝后加入 all_dealers

        leave.all_dealers += (next_dealer.wx_openid + ' ')

        leave.next_dealer_id = None
        leave.status = 2
        leave.deal_end_time = datetime.datetime.now()
        leave.refuse_reason = refuse_reason
        leave.save()
        if leave.type == 0:  # 拒绝年假后需给申请者补上年假数
            applicant_wx_user.legal_vacation_days += leave.leave_days  # todo 这里没有考虑补企业年假OR法定年假，待修改
            applicant_wx_user.save()
        return HttpResponse('Reject')


def cancel(request):
    """
    取消自己的请假/外出申请
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    leave = Leave.objects.get(pk=leave_id)
    all_dealers = leave.all_dealers
    next_dealer_id = leave.next_dealer_id
    leave_days = leave.leave_days
    if leave.type in (0, 8, 9):
        applicant = WXUser.objects.get(wx_openid=leave.applicant_openid)
        if leave.type == 0:
            applicant.legal_vacation_days += leave_days
        if leave.type == 8:
            applicant.company_vacation_days += leave_days
        if leave.type == 9:
            applicant.flexible_vacation_days += leave_days
        applicant.save()
    if next_dealer_id:  # 通知下一个审批者
        next_dealer_user_id = WXUser.objects.get(pk=next_dealer_id).wx_openid
        send_msg(next_dealer_user_id, leave.applicant_name, leave.leave_start_datetime,
                 leave.leave_end_datetime, leave.type, leave.leave_days, 'cancel')
    if all_dealers:  # 通知审批过的人
        for i in all_dealers.split(' '):  # ['test', 'lih']
            send_msg(i, leave.applicant_name, leave.leave_start_datetime,
                     leave.leave_end_datetime, leave.type, leave.leave_days, 'cancel')
    leave.status = 0
    leave.next_dealer_id = None
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
        if leave.type == 0:
            applicant.legal_vacation_days += redundant_leave_days
        elif leave.type == 8:
            applicant.company_vacation_days += redundant_leave_days
        elif leave.type == 9:
            applicant.flexible_vacation_days += redundant_leave_days
        applicant.save()
        if actual_level_days != 0:
            leave.status = 4
        else:
            leave.status = 0
    leave.save()
    return HttpResponse('Success')


def out_done(request):
    """
    外出提前返回
    :param request:
    :return:
    """
    leave_id = request.POST.get('leave_id', '')
    out_actual_level_days = float(request.POST.get('out_actual_level_days'))
    leave = Leave.objects.get(pk=leave_id)
    apply_leave_days = float(leave.leave_days)
    if out_actual_level_days > apply_leave_days:  # 提前返回天数大于申请天数
        return HttpResponse('Fail')
    else:
        leave.leave_days -= out_actual_level_days
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
            # 通知部门考勤员
            applicant_user_id = sick_leave.applicant_openid
            applicant = WXUser.objects.get(wx_openid=applicant_user_id)
            try:
                department_timekeeper = WXUser.objects.get(department=applicant.department, is_timekeeper=1)
                send_msg(receive_open_id=department_timekeeper.wx_openid, applicant_name=applicant.name,
                         start_datetime=sick_leave.leave_start_datetime, end_datetime=sick_leave.leave_end_datetime,
                         _type='病假', days=sick_leave.leave_days, msg_type='病假审核材料')
            except Exception, error:
                print(error)
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
            # 通知部门考勤员
            applicant_user_id = sick_leave.applicant_openid
            applicant = WXUser.objects.get(wx_openid=applicant_user_id)
            try:
                department_timekeeper = WXUser.objects.get(department=applicant.department, is_timekeeper=1)
                send_msg(receive_open_id=department_timekeeper.wx_openid, applicant_name=applicant.name,
                         start_datetime=sick_leave.leave_start_datetime, end_datetime=sick_leave.leave_end_datetime,
                         _type='产假', days=sick_leave.leave_days, msg_type='产假审核材料')
            except Exception, error:
                print(error)
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
    print(i_img)
    i_img.thumbnail((500, 500), Image.ANTIALIAS)
    b = io.BytesIO()
    i_img.save(b, 'JPEG')  # 存入缓存
    image_bytes = b.getvalue()  # 获得二进制文本
    url = my_qiniu.image_upload(image_bytes)
    return HttpResponse(url)





