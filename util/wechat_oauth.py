# coding: utf8
from __future__ import unicode_literals
import requests
import json
from django.core.cache import cache
from urllib import quote_plus

__author__ = 'cai'

corpid = 'wxae4465686cf99af4'  # AppID

corpsecret = '_z4tV2xkFwKRIoacIg114aTVUqdUeHMlbKox5e0T6Fd4L8PFTLXCGU9g1W6DlQxj'  # AppSecret

ACCESS_TOKEN_URL = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s'

CODE_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize?' \
           'appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_base&state=1#wechat_redirect'

USER_ID_URL = 'https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=%s&code=%s&agentid=%s'

AGENT_ID = 6

SEND_MSG_URL = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s'


def get_access_token():
    """
    返回access_token
    :return:
    """
    if not cache.get('access_token'):
        url = ACCESS_TOKEN_URL % (corpid, corpsecret)
        response = requests.get(url)  # requests模块请求URL获得状态码（<Response [200]>）
        access_token_json_data = response.text  # 获取access_token_json对象
        data = json.loads(access_token_json_data)  # 返回成python 字典
        access_token = data['access_token']
        cache.set('access_token', access_token, 7200)
        return access_token
    else:
        return cache.get('access_token')


def get_code_url(redirect_uri):
    """
    返回code url
    :param redirect_uri: 授权后重定向的回调链接地址，请使用urlencode对链接进行处理
    :return:
    """
    urlencode_redirect_uri = quote_plus(redirect_uri).lower()
    return CODE_URL % (corpid, urlencode_redirect_uri)


def get_user_id(code):
    """
    返回user_id
    :param code:
    :return:
    """
    access_token = get_access_token()
    response = requests.get(USER_ID_URL % (access_token, code, AGENT_ID))
    data = json.loads(response.text)
    if data.get('UserId'):
        user_id = data.get('UserId')
    else:
        user_id = ''
    return user_id


def send_msg(receive_open_id, applicant_name, start_datetime, end_datetime, _type, days, msg_type):
    """

    :param receive_open_id: 接受者的open_id
    :param applicant_name:  申请者姓名
    :param _type: 外出OR请假
    :param msg_type: 消息类型， 申请, 同意，拒绝
    :return:
    """
    access_token = get_access_token()
    if msg_type == 'approve':
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "1%s, 您好。您的%s申请 %s 至 %s 共 %s 天已通过，请点击申请记录进行查看"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, _type, start_datetime, end_datetime, days)
    elif msg_type in ('apply', 'agree'):
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "2您的部门同事%s申请%s至%s %s 共 %s 天, 请您点击审批按钮进行批准。"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, start_datetime, end_datetime, _type, days)
    elif msg_type == 'apply_other_leave':
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "3%s申请%s至%s %s 共 %s 天。"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, start_datetime, end_datetime, _type, days)
    elif _type == '病假' and days >= 5:
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "4%s申请%s至%s %s 共 %s 天, 请注意！"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, start_datetime, end_datetime, _type, days)
    elif msg_type in ('sick_apply', 'pregnant_apply'):
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "5您的部门同事%s申请%s至%s %s 共 %s 天, 请等待该同事上传%s材料后进行审核。"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, start_datetime, end_datetime, _type,  days, _type)
    elif msg_type == '病假审核材料' or msg_type == '产假审核材料':
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "6您的部门同事%s申请%s至%s %s 共 %s 天, 已上传%s材料，请您点击审批按钮进行材料审核。"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, start_datetime, end_datetime,
                        _type,  days, _type)

    else:  # 拒绝
        content = """
                {
                   "touser": "%s",
                   "msgtype": "text",
                   "agentid": %s,
                   "text": {
                       "content": "7%s, 您好。您的%s申请 %s 至 %s 共 %s 天未通过, 请点击申请记录进行查看。"
                   },
                   "safe":"0"
                }
                 """ % (receive_open_id, AGENT_ID, applicant_name, _type, start_datetime, end_datetime, days)
    print content.encode('utf-8')
    requests.post(SEND_MSG_URL % access_token, data=content.encode('utf-8'))







