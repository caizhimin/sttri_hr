# coding: utf8

from __future__ import unicode_literals
import os
import io
import StringIO
import zipfile
from django.core.wsgi import get_wsgi_application
os.environ['DJANGO_SETTINGS_MODULE'] = 'sttri_hr.settings'
application = get_wsgi_application()
import xlwt
import xlrd
import json
import calendar
import datetime
from xlutils.copy import copy as excel_copy
from django.shortcuts import render_to_response
from django.http.response import HttpResponse
from util.qiniu_upload import my_qiniu
from util.date import get_work_days
from wechat_user.models import Leave
from django.views.decorators.csrf import csrf_exempt


# Create your views here.

alignment = xlwt.Alignment()  # Create Alignment
alignment.horz = xlwt.Alignment.HORZ_CENTER

style = xlwt.XFStyle()  # Create Style
style.alignment = alignment  # Add Alignment to Style



# green_style = xlwt.XFStyle()
# pattern = xlwt.Pattern()
# pattern.pattern = xlwt.Pattern.SOLID_PATTERN
# pattern.pattern_fore_colour = xlwt.Style.colour_map['custom_green']
# green_style.pattern = pattern


def GetRunTime(func):
    def check(*args, **args2):
        startTime = datetime.datetime.now()
        f = func(*args, **args2)
        endTime = datetime.datetime.now()
        print(endTime-startTime)
        return f

    return check


def index(request):
    years = xrange(2016, 2200)
    months = xrange(1, 13)
    return render_to_response('index.html', {'years': years, 'months': months})

@csrf_exempt
def upload_simple_record(request):
    """
    生成原始记录表view
    :param request:
    :return:
    """
    year = request.POST.get('year')
    month = request.POST.get('month')
    simple_record = request.FILES.get('simple_record')
    print(simple_record)
    aaa = xlrd.open_workbook(file_contents=simple_record.read())
    wb, wb_name = deal_original_data(year, month, aaa)  # wb为写入excel obj, wb_name为其文件名
    # # wb = xlwt.Workbook()
    # # ws = wb.add_sheet('Sheetname')
    # #
    # # response = HttpResponse(content_type="application/ms-excel")
    # # response['Content-Disposition'] ='attachment; filename=%s' % ('111.xls')
    # # wb.save(response)
    b = io.BytesIO()
    wb.save(b)  # 存入缓存
    excel_bytes = b.getvalue()  # 获得二进制文本
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    url = my_qiniu.excel_upload(excel_bytes, wb_name)
    return HttpResponse(url)

@csrf_exempt
def split_original_data_view(request):
    """
    拆分原始记录总表view
    :param request:
    :return:
    """
    year = request.POST.get('year')
    month = request.POST.get('month')
    original_data = request.FILES.get('original_data_table')
    aaa = xlrd.open_workbook(file_contents=original_data.read())
    split_zip = split_original_data(year, month, aaa)
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    url = my_qiniu.zip_upload(split_zip, '%s年%s月原始记录表拆分压缩包.zip' % (year, month))
    # print url
    return HttpResponse(url)

LEAVE_TYPE_LIST = (
    (0, '法定年假'),
    (1, '事假'),
    (2, '病假'),
    (3, '产假'),
    (4, '会议'),
    (5, '培训'),
    (6, '出差'),
    (7, '其他'),
    (8, '企业年假')
)

LEAVE_TYPE_DICT = dict(LEAVE_TYPE_LIST)


@GetRunTime
def deal_original_data(year, month, excel_obj):
    """
    处理原始考勤总记录，补充公休假日，法定假日，请假/外出记录，迟到 晚签到 早退 缺勤
    :return:
    """
    month_days = calendar.monthrange(int(year), int(month))[1]
    start_datetime = datetime.datetime.strptime('%s%s01' % (year, month), "%Y%m%d").date()
    end_datetime = datetime.datetime.strptime('%s%s%s' % (year, month, month_days), "%Y%m%d").date()
    day_list = [str(start_datetime+datetime.timedelta(days=i)).replace('-', '')
                for i in xrange((end_datetime - start_datetime).days+1)]
    day_status = get_work_days(day_list)
    print day_status
    # excel_obj = xlrd.open_workbook('/Users/cai/Documents/考勤系统需求说明书及附件/new_test_data.xls')

    wb = excel_copy(excel_obj)

    # 0: 合同制; 1: 项目合作; 2: 实习生

    for j in [0, 1, 2]:
        table0 = excel_obj.sheet_by_index(j)  # 通过索引顺序获取
        ws = wb.get_sheet(j)
        ws.write(0, 5 if j != 1 else 6, '备注1')
        tmp = 0  # 晚签到计数器
        for i in xrange(1, table0.nrows):
            if table0.cell(i, 1).value != table0.cell(i-1, 1).value:
                tmp = 0  # 不同员工的 晚签到计数器重置为0

            duty_time = table0.cell(i, 4 if j != 1 else 5).value
            name = table0.cell(i, 1).value
            # print(duty_time)
            day = table0.cell(i, 3 if j != 1 else 4).value.split('-')  # 2016-1-1  need to change to 20160101
            format_day = '%s%s%s' % (day[0], day[1] if int(day[1]) >= 10 else '0%s' % day[1],
                                     day[2] if int(day[2]) >= 10 else '0%s' % day[2])
            if day_status[format_day] == '1':
                ws.write(i, 5 if j != 1 else 6, '公休假日')
            elif day_status[format_day] == '2':
                print i
                ws.write(i, 5 if j != 1 else 6, '法定假日')
            else:  # 工作日
                start_time = datetime.datetime(int(day[0]), int(day[1]), int(day[2]), 8, 30)  # todo 这里要修改 不是按整天请假的查询不出
                end_time = datetime.datetime(int(day[0]), int(day[1]), int(day[2]), 17, 00)
                if duty_time == '':  # 没考勤记录
                    # print(day)
                    leaves = Leave.objects.filter(leave_start_datetime__lte=start_time,
                                                  leave_end_datetime__gte=end_time,
                                                  applicant_name=name).exclude(status=0)
                    # leaves = Leave.objects.filter(leave_start_datetime__year=int(day[0]),
                    #                               leave_start_datetime__month=int(day[1]),
                    #                               leave_start_datetime__day=int(day[2]),
                    #                               applicant_name=name).exclude(status=0)
                    if leaves:  # 当天存在请假/外出记录
                        leave_days = leaves.first().leave_days
                        if leaves.first().group == 1:  # 请假
                            ws.write(i, 5 if j != 1 else 6, '请假(%s)%s天' % (LEAVE_TYPE_DICT[leaves.first().type], leave_days))
                        else:  # 外出
                            ws.write(i, 5 if j != 1 else 6, '外出(%s)%s天' % (LEAVE_TYPE_DICT[leaves.first().type], leave_days))
                    else:
                        ws.write(i, 5 if j != 1 else 6, '缺勤一天')

                elif len(duty_time.split(' ')) == 1:  # 只有一次考勤记录
                    leaves = Leave.objects.filter(leave_start_datetime__lte=start_time, leave_end_datetime__gte=end_time,
                                                  applicant_name=name).exclude(status=0)
                    if leaves:
                        leave_days = leaves.first().leave_days
                        if leaves.first().group == 1:  # 请假
                                ws.write(i, 5 if j != 1 else 6, '请假(%s)%s天' % (LEAVE_TYPE_DICT[leaves.first().type], leave_days))
                        else:  # 外出
                            ws.write(i, 5 if j != 1 else 6, '外出(%s)%s天' % (LEAVE_TYPE_DICT[leaves.first().type], leave_days))
                    else:  # 当天没有请假/外出记录
                        ws.write(i, 5 if j != 1 else 6, '缺勤一天')

                else:  # 有两次以上的考勤记录
                    # todo  有两次也要查请假记录
                    on_duty_time = duty_time.split(' ')[0].split(':')  # ['08', '23']
                    off_duty_time = duty_time.split(' ')[-1].split(':')  # ['08', '23']
                    content = ''

                    # print tmp
                    if datetime.time(8, 30) < datetime.time(int(on_duty_time[0]), int(on_duty_time[1])) <= datetime.time(8, 45):
                        content = '晚签到'
                        tmp += 1

                        if tmp > 2:  # 晚签第三次以后为迟到
                            content = '迟到'

                    elif datetime.time(8, 46) <= datetime.time(int(on_duty_time[0]), int(on_duty_time[1])) <= datetime.time(10, 30):
                        content = '迟到'
                    elif datetime.time(10, 31) <= datetime.time(int(on_duty_time[0]), int(on_duty_time[1])) <= datetime.time(12, 30):
                        content = '缺勤上午'
                    elif datetime.time(12, 31) <= datetime.time(int(on_duty_time[0]), int(on_duty_time[1])):
                        content = '缺勤一天'

                    if datetime.time(15, 00) <= datetime.time(int(off_duty_time[0]), int(off_duty_time[1])) < datetime.time(17, 00):
                        content += '早退'
                    elif datetime.time(13, 00) <= datetime.time(int(off_duty_time[0]), int(off_duty_time[1])) < datetime.time(15, 00):
                        content += '缺勤下午'
                    elif datetime.time(int(off_duty_time[0]), int(off_duty_time[1])) < datetime.time(13, 00):
                        content = '缺勤一天'

                    if content == '缺勤上午缺勤下午':
                        content = '缺勤一天'
                    if '缺勤一天' in content:
                        content = '缺勤一天'

                    ws.write(i, 5 if j != 1 else 6, content)

                    pass
        ws.col(4).width = 5000  # 第五列的宽度
        ws.col(5).width = 5000
        ws.col(6).width = 5000
    return wb, '%s年%s月原始记录总表.xls' % (year, month)
    # wb.save('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel.xls')



@GetRunTime
def write_all_duty_record_table():
    year = '2016'
    month = '01'
    work_book = xlwt.Workbook()  # 创建工作簿
    sheet_name = {0: '合同制', 1: '项目合作', 2: '实习生'}
    for j in [0, 1, 2]:
        sheet1 = work_book.add_sheet(sheet_name[j], cell_overwrite_ok=True)  # 创建sheet
        title = '研究院%s年%s月全体员工考勤记录表' % (year, month)
        sheet1.write(0, 0, title)  # 先行后列
        if j == 1:
            sheet1.write(1, 0, '公司')
            sheet1.write(1, 1, '部门')
            sheet1.write(1, 2, '员工工号')
            sheet1.write(1, 3, '日期姓名')
        else:
            sheet1.write(1, 0, '部门')
            sheet1.write(1, 1, '员工工号')
            sheet1.write(1, 2, '日期姓名')
        month_days = calendar.monthrange(int(year), int(month))[1]
        for day in xrange(1, month_days+1):  # 写入日期
            sheet1.write(1, (2 if j != 1 else 3)+day, day, style)

        original_data_excel = xlrd.open_workbook('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel.xls')
        table = original_data_excel.sheet_by_index(j)  # 通过索引顺序获取
        cols = table.col_values(0)[1:]  # 获取第一列内容
        # staff_no_list = []
        for i in xrange(1, table.nrows):
            if j == 1:
                staff_no = table.cell(i, 0).value  # 工号
                staff_name = table.cell(i, 1).value  # 姓名
                staff_dept = table.cell(i, 3).value  # 部门
                staff_company = table.cell(i, 2).value  # 外协公司
                duty_status = table.cell(i, 6).value
            else:
                staff_no = table.cell(i, 0).value  # 工号
                staff_name = table.cell(i, 1).value  # 姓名
                staff_dept = table.cell(i, 2).value  # 部门
                duty_status = table.cell(i, 5).value

            if i != table.nrows - 1:
                if j == 1:
                    sheet1.write(2*(i/month_days)+2, 0, staff_company)  # 2 stand odd col, 3 stand even col
                    sheet1.write(2*(i/month_days)+2, 1, staff_dept)
                    sheet1.write(2*(i/month_days)+2, 2, staff_no)
                    sheet1.write(2*(i/month_days)+2, 3, staff_name)
                    sheet1.write(2*(i/month_days)+3, 0, staff_company)
                    sheet1.write(2*(i/month_days)+3, 1, staff_dept)
                    sheet1.write(2*(i/month_days)+3, 2, staff_no)
                    sheet1.write(2*(i/month_days)+3, 3, staff_name)
                else:
                    sheet1.write(2*(i/month_days)+2, 0, staff_dept)  # 2 stand odd col, 3 stand even col
                    sheet1.write(2*(i/month_days)+2, 1, staff_no)
                    sheet1.write(2*(i/month_days)+2, 2, staff_name)
                    sheet1.write(2*(i/month_days)+3, 0, staff_dept)
                    sheet1.write(2*(i/month_days)+3, 1, staff_no)
                    sheet1.write(2*(i/month_days)+3, 2, staff_name)

            am_duty_content = '8'
            pm_duty_content = '8'
            if duty_status == '':  # 当天全勤
                am_duty_content = pm_duty_content = '8'
            elif duty_status in ('法定假日', '公休假日'):
                am_duty_content = pm_duty_content = '/'
            elif duty_status == '缺勤一天':
                am_duty_content = pm_duty_content = '缺勤'
            elif '请假' in duty_status or '外出' in duty_status:
                if ('企业' in duty_status) or ('法定' in duty_status):
                    am_duty_content = pm_duty_content = duty_status[0: 8]  # 请假(法定年假)1.0天
                else:
                    am_duty_content = pm_duty_content = duty_status[0: 6]  # 请假(年假)1.0天 取括号中的
            elif '晚签到' in duty_status:
                am_duty_content = '晚签到'
            elif '迟到' in duty_status:
                am_duty_content = '迟到'
            elif '缺勤上午' in duty_status:
                am_duty_content = '缺勤'
            elif '缺勤下午' in duty_status:
                pm_duty_content = '缺勤'
            elif '早退' in duty_status:
                pm_duty_content = '早退'
            sheet1.write(2*((i-1)/month_days)+2, (2 if j != 1 else 3) + (month_days if i % month_days == 0 else i % month_days),
                         am_duty_content)
            sheet1.write(2*((i-1)/month_days)+3, (2 if j != 1 else 3) + (month_days if i % month_days == 0 else i % month_days),
                         pm_duty_content)

    work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel2222.xls')  # 保存文件


@GetRunTime
def split_original_data(year, month, excel_obj):
    """
    拆分原始记录表
    :return:
    """
    # original_data_excel = xlrd.open_workbook('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel.xls')
    original_data_excel = excel_obj
    # 合同制和管理序列处理
    table = original_data_excel.sheet_by_index(0)  # 通过索引顺序获取
    buff = StringIO.StringIO()
    z = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    staff_dept_list = set(table.col_values(2)[1:])  # 获取所有的部门列表
    for i in staff_dept_list:

        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'合同制', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '考勤号码')
        sheet1.write(0, 1, '姓名')
        sheet1.write(0, 2, '部门')
        sheet1.write(0, 3, '日期')
        sheet1.write(0, 4, '时间')
        sheet1.write(0, 5, '备注1')
        if i != '管理序列':
            index_list = []
            for j in xrange(1, table.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
                staff_dept = table.cell(j, 2).value  # 部门
                if i == staff_dept:
                    index_list.append(j)
            for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
                staff_no = table.cell(index_list[k], 0).value  # 工号
                staff_name = table.cell(index_list[k], 1).value  # 姓名
                staff_dept = table.cell(index_list[k], 2).value  # 部门
                duty_date = table.cell(index_list[k], 3).value  # 日期
                duty_time = table.cell(index_list[k], 4).value  # 时间
                duty_status = table.cell(index_list[k], 5).value
                sheet1.write(k+1, 0, staff_no)
                sheet1.write(k+1, 1, staff_name)
                sheet1.write(k+1, 2, staff_dept)
                sheet1.write(k+1, 3, duty_date)
                sheet1.write(k+1, 4, duty_time)
                sheet1.write(k+1, 5, duty_status)

            # work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分原始记录/%s年%s年%%s月合同制%s原始记录.xls' %
            #                (year, month, i))  # 保存文件
            b = io.BytesIO()
            work_book.save(b)  # 存入缓存
            z.writestr('%s年%s月合同制%s原始记录.xls' % (year, month, i), b.getvalue())
        else:  # 管理序列处理
            leader_name_list = []
            for j in xrange(1, table.nrows):
                if table.cell(j, 2).value == '管理序列':
                    leader_name = table.cell(j, 1).value
                    if leader_name not in leader_name_list:
                        leader_name_list.append(leader_name)
            all_index = []  # 管理序列姓名对应的index 字典 list
            # [{u'index': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31], u'name': u'\u9886\u5bfcB'}, {u'index': [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62], u'name': u'\u9886\u5bfcA'}]

            for m in leader_name_list:
                leader_index = []
                for n in xrange(1, table.nrows):
                    if m == table.cell(n, 1).value:
                        leader_index.append(n)
                all_index.append({'name': m, 'index': leader_index})
            for o in all_index:
                leader_index = o['index']
                name = o['name']
                for p in xrange(0, len(leader_index)):
                    staff_no = table.cell(leader_index[p], 0).value  # 工号
                    staff_name = table.cell(leader_index[p], 1).value  # 姓名
                    staff_dept = table.cell(leader_index[p], 2).value  # 部门
                    duty_date = table.cell(leader_index[p], 3).value  # 日期
                    duty_time = table.cell(leader_index[p], 4).value  # 时间
                    duty_status = table.cell(leader_index[p], 5).value
                    sheet1.write(p+1, 0, staff_no)
                    sheet1.write(p+1, 1, staff_name)
                    sheet1.write(p+1, 2, staff_dept)
                    sheet1.write(p+1, 3, duty_date)
                    sheet1.write(p+1, 4, duty_time)
                    sheet1.write(p+1, 5, duty_status)

                # work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分原始记录/%s年%s月管理序列%s原始记录.xls' %
                #                (year, month, name))  # 保存文件
                b = io.BytesIO()
                work_book.save(b)  # 存入缓存
                z.writestr('%s年%s月管理序列%s原始记录.xls' % (year, month, name), b.getvalue())

    # 项目合作处理
    # 按 公司拆分
    table1 = original_data_excel.sheet_by_index(1)  # 通过索引顺序获取
    staff_company_list = set(table1.col_values(2)[1:])  # 获取所有的部门列表
    for i in staff_company_list:

        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'项目合作', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '考勤号码')
        sheet1.write(0, 1, '姓名')
        sheet1.write(0, 2, '公司')
        sheet1.write(0, 3, '部门')
        sheet1.write(0, 4, '日期')
        sheet1.write(0, 5, '时间')
        sheet1.write(0, 6, '备注1')
        index_list = []
        for j in xrange(1, table1.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table1.cell(j, 2).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_no = table1.cell(index_list[k], 0).value  # 工号
            staff_name = table1.cell(index_list[k], 1).value  # 姓名
            staff_company = table1.cell(index_list[k], 2).value # 项目合作公司
            staff_dept = table1.cell(index_list[k], 3).value  # 部门
            duty_date = table1.cell(index_list[k], 4).value  # 日期
            duty_time = table1.cell(index_list[k], 5).value  # 时间
            duty_status = table1.cell(index_list[k], 6).value
            sheet1.write(k+1, 0, staff_no)
            sheet1.write(k+1, 1, staff_name)
            sheet1.write(k+1, 2, staff_company)
            sheet1.write(k+1, 3, staff_dept)
            sheet1.write(k+1, 4, duty_date)
            sheet1.write(k+1, 5, duty_time)
            sheet1.write(k+1, 6, duty_status)

        # work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分原始记录/%s年%s月%s公司原始记录.xls' %
        #                (year, month, i))  # 保存文件
        b = io.BytesIO()
        work_book.save(b)  # 存入缓存
        z.writestr('%s年%s月%s公司原始记录.xls' % (year, month, i), b.getvalue())

    #  按部门拆分
    staff_dept_list = set(table1.col_values(3)[1:])  # 获取所有的部门列表
    for i in staff_dept_list:

        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'项目合作', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '考勤号码')
        sheet1.write(0, 1, '姓名')
        sheet1.write(0, 2, '公司')
        sheet1.write(0, 3, '部门')
        sheet1.write(0, 4, '日期')
        sheet1.write(0, 5, '时间')
        sheet1.write(0, 6, '备注1')
        index_list = []
        for j in xrange(1, table1.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table1.cell(j, 3).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_no = table1.cell(index_list[k], 0).value  # 工号
            staff_name = table1.cell(index_list[k], 1).value  # 姓名
            staff_company = table1.cell(index_list[k], 2).value # 项目合作公司
            staff_dept = table1.cell(index_list[k], 3).value  # 部门
            duty_date = table1.cell(index_list[k], 4).value  # 日期
            duty_time = table1.cell(index_list[k], 5).value  # 时间
            duty_status = table1.cell(index_list[k], 6).value
            sheet1.write(k+1, 0, staff_no)
            sheet1.write(k+1, 1, staff_name)
            sheet1.write(k+1, 2, staff_company)
            sheet1.write(k+1, 3, staff_dept)
            sheet1.write(k+1, 4, duty_date)
            sheet1.write(k+1, 5, duty_time)
            sheet1.write(k+1, 6, duty_status)

        # work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分原始记录/%s年%s月项目合作%s部门原始记录.xls' %
        #                (year, month, i))  # 保存文件
        b = io.BytesIO()
        work_book.save(b)  # 存入缓存
        z.writestr('%s年%s月项目合作%s部门原始记录.xls' % (year, month, i), b.getvalue())

    #  实习生处理 按部门分
    table2 = original_data_excel.sheet_by_index(2)
    staff_dept_list = set(table2.col_values(2)[1:])  # 获取所有的部门列表
    for i in staff_dept_list:

        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'实习生', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '考勤号码')
        sheet1.write(0, 1, '姓名')
        sheet1.write(0, 2, '部门')
        sheet1.write(0, 3, '日期')
        sheet1.write(0, 4, '时间')
        sheet1.write(0, 5, '备注1')
        index_list = []
        for j in xrange(1, table2.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table2.cell(j, 2).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_no = table2.cell(index_list[k], 0).value  # 工号
            staff_name = table2.cell(index_list[k], 1).value  # 姓名
            staff_dept = table2.cell(index_list[k], 2).value  # 部门
            duty_date = table2.cell(index_list[k], 3).value  # 日期
            duty_time = table2.cell(index_list[k], 4).value  # 时间
            duty_status = table2.cell(index_list[k], 5).value
            sheet1.write(k+1, 0, staff_no)
            sheet1.write(k+1, 1, staff_name)
            sheet1.write(k+1, 2, staff_dept)
            sheet1.write(k+1, 3, duty_date)
            sheet1.write(k+1, 4, duty_time)
            sheet1.write(k+1, 5, duty_status)

        # work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分原始记录/%s年%s月实习生%s部门原始记录.xls' %
        #                (year, month, i))  # 保存文件
        b = io.BytesIO()
        work_book.save(b)  # 存入缓存
        z.writestr('%s年%s月实习生%s部门原始记录.xls' % (year, month, i), b.getvalue())
    z.close()
    # buff.flush()
    ret_zip = buff.getvalue()
    buff.close()
    return ret_zip

@GetRunTime
def split_duty_record_data():
    """
    拆分总考勤记录表
    :return:
    """
    year = '2016'
    month = '01'
    month_days = calendar.monthrange(int(year), int(month))[1]
    original_data_excel = xlrd.open_workbook('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel2222.xls')
    table0 = original_data_excel.sheet_by_index(0)  # 通过索引顺序获取
    staff_dept_list = set(table0.col_values(0)[1:])  # 获取所有的部门列表
    for i in staff_dept_list:
        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'合同制', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '研究院%s年%s月合同制%s员工考勤记录表' % (year, month, i))
        sheet1.write(1, 0, '部门')
        sheet1.write(1, 1, '员工工号')
        sheet1.write(1, 2, '日期姓名')
        if i != '管理序列':
            index_list = []
            for j in xrange(1, table0.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
                staff_dept = table0.cell(j, 0).value  # 部门
                if i == staff_dept:
                    index_list.append(j)
            for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
                staff_dept = table0.cell(index_list[k], 0).value  # 部门
                staff_no = table0.cell(index_list[k], 1).value  # 工号
                staff_name = table0.cell(index_list[k], 2).value  # 姓名
                sheet1.write(k+2, 0, staff_dept)
                sheet1.write(k+2, 1, staff_no)
                sheet1.write(k+2, 2, staff_name)
                for l in xrange(0, month_days):
                    sheet1.write(1, l+3, l+1, style)
                    status = table0.cell(index_list[k], l+3).value  # 考勤状态
                    sheet1.write(k+2, l+3, status)

            work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分考勤记录表/%s年%s月合同制%s考勤记录表.xls' %
                           (year, month, i))  # 保存文件
        else:  # 管理序列处理
            leader_name_list = []
            for j in xrange(1, table0.nrows):
                if table0.cell(j, 0).value == '管理序列':
                    leader_name = table0.cell(j, 2).value
                    if leader_name not in leader_name_list:
                        leader_name_list.append(leader_name)
            all_index = []  # 管理序列姓名对应的index 字典 list
            # [{u'index': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31], u'name': u'\u9886\u5bfcB'}, {u'index': [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62], u'name': u'\u9886\u5bfcA'}]
            for m in leader_name_list:
                leader_index = []
                for n in xrange(1, table0.nrows):
                    if m == table0.cell(n, 2).value:
                        leader_index.append(n)
                all_index.append({'name': m, 'index': leader_index})
            for o in all_index:
                leader_index = o['index']
                name = o['name']
                for p in xrange(0, len(leader_index)):
                    staff_dept = table0.cell(leader_index[p], 0).value  # 部门
                    staff_no = table0.cell(leader_index[p], 1).value  # 工号
                    staff_name = table0.cell(leader_index[p], 2).value  # 姓名
                    sheet1.write(p+2, 0, staff_dept)
                    sheet1.write(p+2, 1, staff_no)
                    sheet1.write(p+2, 2, staff_name)
                    for l in xrange(0, month_days):
                        sheet1.write(1, l+3, l+1, style)
                        status = table0.cell(leader_index[p], l+3).value  # 考勤状态
                        sheet1.write(p+2, l+3, status)
                    work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分考勤记录表/%s年%s月管理序列%s考勤记录表.xls' %
                                   (year, month, name))  # 保存文件
    # 项目合作处理
    # 按 公司拆分
    table1 = original_data_excel.sheet_by_index(1)  # 通过索引顺序获取
    staff_company_list = set(table1.col_values(0)[2:])  # 获取所有的部门列表
    for i in staff_company_list:
        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'项目合作', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '研究院%s年%s月%s公司员工考勤记录表' % (year, month, i))
        sheet1.write(1, 0, '公司')
        sheet1.write(1, 1, '部门')
        sheet1.write(1, 2, '员工工号')
        sheet1.write(1, 3, '日期姓名')
        index_list = []
        for j in xrange(1, table1.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table1.cell(j, 0).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_company = table1.cell(index_list[k], 0).value  # 公司
            staff_dept = table1.cell(index_list[k], 1).value  # 部门
            staff_no = table1.cell(index_list[k], 2).value  # 工号
            staff_name = table1.cell(index_list[k], 3).value  # 姓名
            sheet1.write(k+2, 0, staff_company)
            sheet1.write(k+2, 1, staff_dept)
            sheet1.write(k+2, 2, staff_no)
            sheet1.write(k+2, 3, staff_name)
            for l in xrange(0, month_days):
                sheet1.write(1, l+4, l+1, style)
                status = table0.cell(index_list[k], l+3).value  # 考勤状态
                sheet1.write(k+2, l+4, status)

        work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分考勤记录表/%s年%s月%s公司考勤记录表.xls' %
                       (year, month, i))  # 保存文件
    # 按 部门拆分
    staff_dept_list = set(table1.col_values(1)[2:])  # 获取所有的部门列表
    for i in staff_dept_list:
        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'项目合作', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '研究院%s年%s月项目协作%s员工考勤记录表' % (year, month, i))
        sheet1.write(1, 0, '公司')
        sheet1.write(1, 1, '部门')
        sheet1.write(1, 2, '员工工号')
        sheet1.write(1, 3, '日期姓名')
        index_list = []
        for j in xrange(1, table1.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table1.cell(j, 1).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_company = table1.cell(index_list[k], 0).value  # 公司
            staff_dept = table1.cell(index_list[k], 1).value  # 部门
            staff_no = table1.cell(index_list[k], 2).value  # 工号
            staff_name = table1.cell(index_list[k], 3).value  # 姓名
            sheet1.write(k+2, 0, staff_company)
            sheet1.write(k+2, 1, staff_dept)
            sheet1.write(k+2, 2, staff_no)
            sheet1.write(k+2, 3, staff_name)
            for l in xrange(0, month_days):
                sheet1.write(1, l+4, l+1, style)
                status = table0.cell(index_list[k], l+3).value  # 考勤状态
                sheet1.write(k+2, l+4, status)

        work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分考勤记录表/%s年%s月项目协作%s员工考勤记录表.xls' %
                       (year, month, i))  # 保存文件

    #  实习生 按部门分
    table2 = original_data_excel.sheet_by_index(2)
    staff_dept_list = set(table2.col_values(0)[1:])  # 获取所有的部门列表
    for i in staff_dept_list:
        work_book = xlwt.Workbook()  # 创建工作簿
        sheet1 = work_book.add_sheet(u'实习生', cell_overwrite_ok=True)  # 创建sheet
        sheet1.write(0, 0, '研究院%s年%s月实习生%s考勤记录表' % (year, month, i))
        sheet1.write(1, 0, '部门')
        sheet1.write(1, 1, '员工工号')
        sheet1.write(1, 2, '日期姓名')
        index_list = []
        for j in xrange(1, table2.nrows):  # 为了找出同一个部门所在原始记录表的首和尾,方便计算length
            staff_dept = table2.cell(j, 0).value  # 部门
            if i == staff_dept:
                index_list.append(j)
        for k in xrange(0, len(index_list)):  # 根据一个部门的length, 插入数据
            staff_dept = table2.cell(index_list[k], 0).value  # 部门
            staff_no = table2.cell(index_list[k], 1).value  # 工号
            staff_name = table2.cell(index_list[k], 2).value  # 姓名
            sheet1.write(k+2, 0, staff_dept)
            sheet1.write(k+2, 1, staff_no)
            sheet1.write(k+2, 2, staff_name)
            for l in xrange(0, month_days):
                sheet1.write(1, l+3, l+1, style)
                status = table0.cell(index_list[k], l+3).value  # 考勤状态
                sheet1.write(k+2, l+3, status)

        work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/拆分考勤记录表/%s年%s月实习生%s部门考勤记录表.xls' %
                       (year, month, i))  # 保存文件


@GetRunTime
def write_duty_summary_data():
    """
    考勤汇总总表
    :return:
    """
    year = '2016'
    month = '01'
    month_days = calendar.monthrange(int(year), int(month))[1]
    original_data_excel = xlrd.open_workbook('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel2222.xls')
    table0 = original_data_excel.sheet_by_index(0)  # 通过索引顺序获取
    work_book = xlwt.Workbook()  # 创建工作簿

    # set custom color
    xlwt.add_palette_colour('custom_green', 0x21)
    work_book.set_colour_RGB(0x21, 203, 255, 200)
    green_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['custom_green']
    green_style.pattern = pattern

    sheet1 = work_book.add_sheet(u'合同制', cell_overwrite_ok=True)  # 创建sheet
    sheet1.write(0, 0, '研究院%s年%s月员工考勤汇总总表' % (year, month))
    sheet1.write(1, 0, '序号')
    sheet1.write(1, 1, '部门序号')
    sheet1.write(1, 2, '组织单位')
    sheet1.write(1, 3, '人员编号')
    sheet1.write(1, 4, '人员姓名')
    duty_list = ['全勤', '出差、会议、培训等出勤情况', '迟到', '早退', '缺勤', '法定年休假', '企业年休假', '病假', '事假', '产假',
                 '其他假期(如:婚假、丧假等)']
    for i in xrange(2, 13):
        sheet1.write(1, 2*i+1, duty_list[i-2])
        sheet1.write(1, 2*i+2, duty_list[i-2])
        if i != 11:
            sheet1.write(2, 2*i+1, '天数', green_style)
        else:
            sheet1.write(2, 2*i+1, '天数日历日', green_style)
        sheet1.write(2, 2*i+2, '说明')

    for i in xrange(2, table0.nrows, 2):  # 步进2
        staff_name = table0.cell(i, 2).value
        staff_no = table0.cell(i, 1).value
        staff_dept = table0.cell(i, 0).value
        if staff_dept != table0.cell(i-2, 0).value:
            dept_count = 1
        else:
            dept_count += 1
        present_days = 0  # 全勤天数
        out_days = 0  # 外出天数
        legal_leave_days = 0  # 法定年假天数
        legal_leave_string = ''  # 法定年假说明
        company_leave_days = 0  # 企业年假天数
        company_leave_string = ''  # 企业年假说明
        sick_leave_days = 0  # 病假天数
        sick_leave_string = ''  # 病假天数说明
        personal_leave_days = 0  # 事假天数
        personal_leave_string = ''  # 事假天数说明
        pregnant_leave_days = 0  # 产假
        other_leave_days = 0  # 其他假期
        late_count = 0  # 迟到次数
        late_days_string = ''   # 迟到天数说明
        leave_early_count = 0  # 早退次数
        leave_early_string = ''  # 早退天数说明
        absence_count = 0  # 缺勤次数
        absence_string = ''  # 缺勤天数说明
        for j in xrange(0, month_days):
            am_duty = table0.cell(i, 3+j).value    # 上午考勤情况
            pm_duty = table0.cell(i+1, 3+j).value  # 下午考勤情况
            # 判断上午情况
            if am_duty == '8':
                present_days += 0.5
            elif '请假' in am_duty:
                if '法定年假' in am_duty:
                    legal_leave_days += 0.5
                    legal_leave_string += '%s-%s-%s上;' % (year, month, j)
                elif '企业年假' in am_duty:
                    company_leave_days += 0.5
                    company_leave_string += '%s-%s-%s上;' % (year, month, j)
                elif '病假' in am_duty:
                    sick_leave_days += 0.5
                    sick_leave_string += '%s-%s-%s上;' % (year, month, j)
                elif '事假' in am_duty:
                    personal_leave_days += 0.5
                    personal_leave_string += '%s-%s-%s上;' % (year, month, j)
                elif '产假' in am_duty:
                    pregnant_leave_days += 0.5
                elif '其他' in am_duty:
                    other_leave_days += 0.5
            elif '外出' in am_duty:
                out_days += 0.5
            elif '晚签到' in am_duty:
                present_days += 0.5
            elif '迟到' in am_duty:
                late_count += 1
                late_days_string += '%s-%s-%s;' % (year, month, j)
            elif '缺勤' in am_duty:
                absence_count += 0.5
                absence_string += '%s-%s-%s上;' % (year, month, j)
            # 判断下午情况
            if pm_duty == '8':
                present_days += 0.5
            elif '请假' in pm_duty:
                if '法定年假' in pm_duty:
                    legal_leave_days += 0.5
                    legal_leave_string += '%s-%s-%s下;' % (year, month, j)
                elif '企业年假' in pm_duty:
                    company_leave_days += 0.5
                    company_leave_string += '%s-%s-%s下;' % (year, month, j)
                elif '病假' in pm_duty:
                    sick_leave_days += 0.5
                    sick_leave_string += '%s-%s-%s下;' % (year, month, j)
                elif '事假' in pm_duty:
                    personal_leave_days += 0.5
                    personal_leave_string += '%s-%s-%s下;' % (year, month, j)
                elif '产假' in pm_duty:
                    pregnant_leave_days += 0.5
                elif '其他' in pm_duty:
                    other_leave_days += 0.5
            elif '外出' in pm_duty:
                out_days += 0.5
            elif '晚签到' in pm_duty:
                present_days += 0.5
            elif '早退' in pm_duty:
                leave_early_count += 1
                leave_early_string += '%s-%s-%s;' % (year, month, j)
            elif '缺勤' in pm_duty:
                absence_count += 0.5
                absence_string += '%s-%s-%s下;' % (year, month, j)

        sheet1.write(i/2+2, 0, i/2)  # index
        sheet1.write(i/2+2, 1, dept_count)
        sheet1.write(i/2+2, 4, staff_name)
        sheet1.write(i/2+2, 3, staff_no)
        sheet1.write(i/2+2, 2, staff_dept)
        sheet1.write(i/2+2, 5, present_days, green_style)
        sheet1.write(i/2+2, 7, out_days, green_style)
        sheet1.write(i/2+2, 9, late_count, green_style)
        sheet1.write(i/2+2, 10, late_days_string)
        sheet1.write(i/2+2, 11, leave_early_count, green_style)
        sheet1.write(i/2+2, 12, leave_early_string)
        sheet1.write(i/2+2, 13, absence_count, green_style)
        sheet1.write(i/2+2, 14, absence_string, green_style)
        sheet1.write(i/2+2, 15, legal_leave_days, green_style)
        sheet1.write(i/2+2, 16, legal_leave_string)
        sheet1.write(i/2+2, 17, company_leave_days, green_style)
        sheet1.write(i/2+2, 18, company_leave_string)
        sheet1.write(i/2+2, 19, sick_leave_days, green_style)
        sheet1.write(i/2+2, 20, sick_leave_string)
        sheet1.write(i/2+2, 21, personal_leave_days, green_style)
        sheet1.write(i/2+2, 22, personal_leave_string)
        sheet1.write(i/2+2, 23, pregnant_leave_days, green_style)
        sheet1.write(i/2+2, 25, other_leave_days, green_style)

    work_book.save('/Users/cai/Documents/考勤系统需求说明书及附件/test_excel3333.xls')  # 保存文件



# b = io.BytesIO()
# wb.save(b)  # 存入缓存
# excel_bytes = b.getvalue()  # 获得二进制文本
# url = my_qiniu.excel_upload(excel_byte s, '11133.xls')
# timeit.timeit('main()', number=1)

# deal_original_data()

# write_all_duty_record_table()

# split_original_data()

# split_duty_record_data()
# write_duty_summary_data()
# 0 工作日
# 1 休息日(公休假日)
# 2 节假日(法定假日)
