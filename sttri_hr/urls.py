# coding: utf8
from __future__ import unicode_literals
"""sttri_hr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
import os
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from wechat_user.models import WXUser, Leave


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def binding(request):
    if request.method == 'POST':
        open_id = '11111'
        name = request.POST.get('name')
        work_num = request.POST.get('work_num')
        cell_phone = request.POST.get('cell_phone')
        if WXUser.objects.filter(name=name, work_num=work_num, cell_phone=cell_phone).exists():
            user = WXUser.objects.get(name=name, work_num=work_num, cell_phone=cell_phone)
            user.wx_openid = open_id
            user.save()
            return HttpResponse('Success')
        else:
            return HttpResponse('Fail')
    open_id = '111'
    if WXUser.objects.filter(wx_openid=open_id).exists():
        return render_to_response('binding.html', {'banded': 'banded'})
    # if request.GET.get('code'):
    #     code = request.GET.get('code')
    #     open_id = get_openid_by_oauth(code)
    #     request.session['open_id'] = open_id
    #     # request.session['open_id'] = '8881'  # todo 先弄死了
    #     Member.objects.get_or_create(open_id=request.session.get('open_id'))
    #     return render_to_response('index.html')
    # REDIRECT_URI = 'http%3a%2f%2fcommandor0.oicp.net%2findex'  # 要用urlcode编码
    # URL = CODE_URL.replace('APPID', APPID).replace('REDIRECT_URI', REDIRECT_URI).replace('SCOPE', SCOPE).replace('STATE', '1')
    # # return HttpResponseRedirect(URL)
    # request.session['open_id'] = 'oknWFt6btKyvj_sKgD65Mq3OHCn4'
    return render_to_response('binding.html', context_instance=RequestContext(request))


def leave(request):
    """
    请假页面
    :param request:
    :return:
    """
    request.session['open_id'] = '8888'  # todo delete later
    open_id = request.session.get('open_id')
    current_user = WXUser.objects.get(wx_openid=open_id)
    return render_to_response('leave.html', {'current_user': current_user}, context_instance=RequestContext(request))


def out(request):
    """
    外出页面
    :param request:
    :return:
    """
    request.session['open_id'] = '8888'  # todo delete later
    open_id = request.session.get('open_id')
    current_user = WXUser.objects.get(wx_openid=open_id)
    return render_to_response('out.html', {'current_user': current_user}, context_instance=RequestContext(request))


def success(request, submit_type):
    """
    提交，审批成功页面
    :param request:
    :param submit_type:
    :return:
    """
    if submit_type == 'leave':
        submit_type = '请假'
    elif submit_type == 'out':
        submit_type = '外出'
    else:
        submit_type = ''
    return render_to_response('success.html', {'type': submit_type})


def approve(request):
    """
    审批页面
    :param request:
    :return:
    """
    request.session['open_id'] = '9999'  # todo delete later
    open_id = request.session.get('open_id')
    current_user = WXUser.objects.get(wx_openid=open_id)
    approve_leaves = Leave.objects.filter(next_dealer_id=current_user, status=1).order_by('-create_time')  # 审核中的请假/外出记录
    return render_to_response('approve.html', {'approve_leaves': approve_leaves})


def my_leaves(request):
    """
    每人的请假记录页面
    :param request:
    :return:
    """
    request.session['open_id'] = '8888'  # todo delete later
    open_id = request.session.get('open_id')
    leaves = Leave.objects.filter(applicant_openid=open_id).order_by('-create_time')
    return render_to_response('my_leaves.html', {'leaves': leaves})

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^binding/$', binding, name='index'),
    url(r'^leave/$', leave, name='leave'),
    url(r'^out/$', out, name='out'),
    url(r'^approve/$', approve, name='approve_page'),
    url(r'^my_leaves/$', my_leaves, name='my_leaves'),
    url(r'^success/(?P<submit_type>.*)/', success, name='success'),
    url(r'^leave/', include('leave.urls')),

]

# urlpatterns += patterns('', url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
#                                 {'document_root': BASE_DIR + '/static'}),
#                             url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
#                                 {'document_root': '/Volumes/hd/project/LearnSkill_MEDIA_FILES'}),)
