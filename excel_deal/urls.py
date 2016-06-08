__author__ = 'cai'
from django.conf.urls import url
from excel_deal import views

urlpatterns = [
    url(r'^index', views.index, name='index'),
    url(r'^upload_simple_record', views.upload_simple_record, name='upload_simple_record'),
    url(r'^split_original_data_view', views.split_original_data_view, name='split_original_data_view'),
    url(r'^write_all_duty_record_table_view', views.write_all_duty_record_table_view, name='write_all_duty_record_table_view'),
    url(r'^split_duty_record_data_view', views.split_duty_record_data_view, name='split_duty_record_data_view')
]