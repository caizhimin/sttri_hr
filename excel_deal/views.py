# coding: utf8

from __future__ import unicode_literals
import os
import io
import xlwt
import xlrd
from django.core.wsgi import get_wsgi_application
from django.shortcuts import render_to_response
from django.http.response import HttpResponse
from util.qiniu_upload import my_qiniu
from util.date import get_work_days
from wechat_user.models import Leave
from django.views.decorators.csrf import csrf_exempt
from excel_deal_func import deal_original_data, split_original_data, write_duty_summary_data, split_duty_record_data, \
    write_all_duty_record_table
os.environ['DJANGO_SETTINGS_MODULE'] = 'sttri_hr.settings'
application = get_wsgi_application()


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


@csrf_exempt
def write_all_duty_record_table_view(request):
    """
    生成当月员工考勤记录总表view
    :param request:
    :return:
    """
    year = request.POST.get('year')
    month = request.POST.get('month')
    original_data = request.FILES.get('original_data_table_a')
    aaa = xlrd.open_workbook(file_contents=original_data.read())
    wb, wb_name = write_all_duty_record_table(year, month, aaa)  # wb为写入excel obj, wb_name为其文件名
    b = io.BytesIO()
    wb.save(b)  # 存入缓存
    excel_bytes = b.getvalue()  # 获得二进制文本
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    url = my_qiniu.excel_upload(excel_bytes, wb_name)
    return HttpResponse(url)









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
