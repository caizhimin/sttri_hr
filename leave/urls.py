__author__ = 'cai'

from django.conf.urls import url, patterns
from leave import views

urlpatterns = [
    url(r'^calculate_leave_day$', views.calculate_leave_day, name='calculate_leave_day'),
    url(r'^leave_apply$', views.leave_apply, name='leave_apply'),
    url(r'^out_apply$', views.out_apply, name='out_apply'),
    url(r'^approve$', views.approve, name='approve'),
    url(r'^cancel$', views.cancel, name='cancel'),
    url(r'^done$', views.done, name='done'),
    url(r'^out_done', views.out_done, name='out_done'),
    url(r'^sick_leave_img_upload_page/(?P<pk>\d+)$', views.sick_leave_img_upload_page,
        name='sick_leave_img_upload_page'),
    url(r'^pregnant_leave_img_upload_page/(?P<pk>\d+)$', views.pregnant_leave_img_upload_page,
        name='pregnant_leave_img_upload_page'),
    url(r'^img_upload$', views.img_upload, name='img_upload')

]