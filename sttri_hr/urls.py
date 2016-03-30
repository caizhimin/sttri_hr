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
import datetime
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from wechat_user.models import WXUser, Leave
from util.wechat_oauth import get_user_id, get_code_url


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def binding(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        print('user_id', user_id)
        name = request.POST.get('name')
        work_num = request.POST.get('work_num')
        cell_phone = request.POST.get('cell_phone')
        if WXUser.objects.filter(name=name, work_num=work_num, cell_phone=cell_phone).exists():
            user = WXUser.objects.get(name=name, work_num=work_num, cell_phone=cell_phone)
            user.wx_openid = user_id
            user.save()
            return HttpResponse('Success')
        else:
            return HttpResponse('Fail')
    user_id = request.session.get('user_id', '')
    if WXUser.objects.filter(wx_openid=user_id).exists():
        return render_to_response('binding.html', {'banded': 'banded'})
    else:
        return render_to_response('binding.html', context_instance=RequestContext(request))


def leave(request):
    """
    请假页面
    :param request:
    :return:
    """
    if request.GET.get('code') or request.session.get('user_id', ''):
        user_id = request.session.get('user_id', '')
        if not user_id:
            user_id = get_user_id(request.GET.get('code'))
        request.session['user_id'] = user_id
        if not WXUser.objects.filter(wx_openid=user_id).exists():
            return HttpResponseRedirect('/binding')
        else:
            current_user = WXUser.objects.get(wx_openid=user_id)
        return render_to_response('leave.html', {'current_user': current_user},
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(get_code_url('http://wachat.sttri.com.cn/leave'))

    # request.session['open_id'] = '8888'  # todo delete later
    # open_id = request.session.get('open_id')
    # current_user = WXUser.objects.get(wx_openid=open_id)
    # return render_to_response('leave.html', {'current_user': current_user}, context_instance=RequestContext(request))


def out(request):
    """
    外出页面
    :param request:
    :return:
    """
    if request.GET.get('code') or request.session.get('user_id', ''):
        user_id = request.session.get('user_id', '')
        if not user_id:
            user_id = get_user_id(request.GET.get('code'))
        request.session['user_id'] = user_id
        if not WXUser.objects.filter(wx_openid=user_id).exists():
            return HttpResponseRedirect('/binding')
        else:
            current_user = WXUser.objects.get(wx_openid=user_id)
        return render_to_response('out.html', {'current_user': current_user},
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(get_code_url('http://wachat.sttri.com.cn/out'))

    #
    # request.session['open_id'] = '8888'  # todo delete later
    # open_id = request.session.get('open_id')
    # current_user = WXUser.objects.get(wx_openid=open_id)
    # return render_to_response('out.html', {'current_user': current_user}, context_instance=RequestContext(request))


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

    if request.GET.get('code') or request.session.get('user_id', ''):
        user_id = request.session.get('user_id', '')
        if not user_id:
            user_id = get_user_id(request.GET.get('code'))
        request.session['user_id'] = user_id
        if not WXUser.objects.filter(wx_openid=user_id).exists():
            return HttpResponseRedirect('/binding')
        else:
            current_user = WXUser.objects.get(wx_openid=user_id)
            # 审核中的请假/外出记录
            approve_leaves = Leave.objects.filter(next_dealer_id=current_user, status=1).order_by('-create_time')
        return render_to_response('approve.html', {'approve_leaves': approve_leaves},
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(get_code_url('http://wachat.sttri.com.cn/approve'))


    # request.session['open_id'] = '9999'  # todo delete later
    # open_id = request.session.get('open_id')
    # current_user = WXUser.objects.get(wx_openid=open_id)
    # approve_leaves = Leave.objects.filter(next_dealer_id=current_user, status=1).order_by('-create_time')  # 审核中的请假/外出记录
    # return render_to_response('approve.html', {'approve_leaves': approve_leaves})

def approved_record(request):
    """
    审批记录页面
    :param request:
    :return:
    """
    if request.GET.get('code') or request.session.get('user_id', ''):
        user_id = request.session.get('user_id', '')
        if not user_id:
            user_id = get_user_id(request.GET.get('code'))
        request.session['user_id'] = user_id
        if not WXUser.objects.filter(wx_openid=user_id).exists():
            return HttpResponseRedirect('/binding')
        else:
            current_user = WXUser.objects.get(wx_openid=user_id)
            # 审批过的中的请假/外出记录
            approved_leaves = Leave.objects.filter(all_dealers__contains=user_id).order_by('-create_time')
        return render_to_response('approve_record.html', {'approved_leaves': approved_leaves},
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(get_code_url('http://wachat.sttri.com.cn/approve'))

    # request.session['open_id'] = '8888'  # todo delete later
    # open_id = request.session.get('open_id')
    # current_user = WXUser.objects.get(wx_openid=open_id)
    # approved_leaves = Leave.objects.filter(all_dealers__contains=open_id).order_by('-create_time')  # 审核中的请假/外出记录
    # return render_to_response('approve_record.html', {'approved_leaves': approved_leaves})


def my_leaves(request):
    """
    每人的请假记录页面
    :param request:
    :return:
    """
    if request.GET.get('code') or request.session.get('user_id', ''):
        user_id = request.session.get('user_id', '')
        if not user_id:
            user_id = get_user_id(request.GET.get('code'))
        request.session['user_id'] = user_id
        if not WXUser.objects.filter(wx_openid=user_id).exists():
            return HttpResponseRedirect('/binding')
        else:
                leaves = Leave.objects.filter(applicant_openid=user_id).order_by('-create_time')
        return render_to_response('my_leaves.html', {'leaves': leaves},
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(get_code_url('http://wachat.sttri.com.cn/my_leaves'))

    #
    # request.session['open_id'] = '8888'  # todo delete later
    # open_id = request.session.get('open_id')
    # leaves = Leave.objects.filter(applicant_openid=open_id).order_by('-create_time')
    # return render_to_response('my_leaves.html', {'leaves': leaves})

urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/', include(admin.site.urls)),
    url(r'^binding/$', binding, name='index'),
    url(r'^leave/$', leave, name='leave'),
    url(r'^out/$', out, name='out'),
    url(r'^approve/$', approve, name='approve_page'),
    url(r'^approved_record/$', approved_record, name='approved_record'),
    url(r'^my_leaves/$', my_leaves, name='my_leaves'),
    url(r'^success/(?P<submit_type>.*)/', success, name='success'),
    url(r'^leave/', include('leave.urls')),
    url(r'^excel_deal/', include('excel_deal.urls'))

]

# urlpatterns += patterns('', url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
#                                 {'document_root': BASE_DIR + '/static'}),
#                             url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
#                                 {'document_root': '/Volumes/hd/project/LearnSkill_MEDIA_FILES'}),)
