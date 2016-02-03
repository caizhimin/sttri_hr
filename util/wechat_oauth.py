# coding: utf8
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

AGENT_id = 6

def get_access_token():
    """
    返回access_token
    :return:
    """
    if not cache.get('access_token'):
        url = ACCESS_TOKEN_URL % (corpid, corpsecret)
        response = requests.get(url)  # requests模块请求URL获得状态码（<Response [200]>）
        access_token_json_data = response.text  # 获取access_token_json对象
        data = json.loads(access_token_json_data)   # 返回成python 字典
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
    print('CODE_URL', CODE_URL % (corpid, urlencode_redirect_uri))
    return CODE_URL % (corpid, urlencode_redirect_uri)


def get_user_id(code):
    """
    返回user_id
    :param code:
    :return:
    """
    access_token = get_access_token()
    print('dad', USER_ID_URL % (access_token, code, AGENT_id))
    response = requests.get(USER_ID_URL % (access_token, code, AGENT_id))
    data = json.loads(response.text)
    if data.get('UserId'):
        user_id = data.get('UserId')
    else:
        user_id = ''
    return user_id




