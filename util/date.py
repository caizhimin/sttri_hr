# coding: utf8
__author__ = 'cai'
import requests
import json
from util.logger import log

# HOLIDAY_API_KEY = '24e16647f7490e170d68de37bc7254fc'   # baidu
HOLIDAY_API_KEY = '50e929681e924ddd6f53e5603780b23d'   # sina

# headers = {'apikey': HOLIDAY_API_KEY}  # baidu
headers = {'apix-key': HOLIDAY_API_KEY}  # sina


# 0 工作日
# 1 休息日
# 2 节假日


def get_work_days(days_list):
    """
    :param days_list:  ['20160101', '20160202']
    :return: if single days_list, return 0 or 1 or 2 ,
             if multiple days_list, return {"20130101":"2","20130103":"2",,"20130201":"0"}
    """
    # url = 'http://apis.baidu.com/xiaogg/holiday/holiday?d='  # baidu
    # url = 'http://a.apix.cn/tbip/sinaapp/?d='  # damn it!
    url = 'http://www.easybots.cn/api/holiday.php?d='

    prefix = ','.join(days_list)
    try:
        response = requests.get('%s%s' % (url, prefix))
        if len(days_list) == 1:
            return json.loads(response.text)[days_list[0]]
        else:
            return json.loads(response.text)
    except Exception, e:
        log.error(e)
        return None
