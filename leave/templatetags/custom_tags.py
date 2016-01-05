# coding: utf8
from __future__ import unicode_literals
__author__ = 'cai'
from django import template

register = template.Library()


def multiply_ten_thousand(value):
    """
    自定义标签 将数字乘10000
    :param value:
    :return:
    """
    return int(float(value)*10000)

register.filter('multiply_ten_thousand', multiply_ten_thousand)


def get_value_by_key(dictionary, key):
    """
    根据键返回字典 对应的值
    :param dictionary:
    :param key:
    :return:
    """
    try:
        value = dictionary[key]
    except KeyError:
        value = 0
    return value

register.filter('get_value_by_key', get_value_by_key)


def get_sick_level_img(attach_photo):
    """
    :param attach_photo:
    :return:
    """
    try:
        return eval(attach_photo).get('sick_level_img')
    except Exception:
        return ''

register.filter('get_sick_level_img', get_sick_level_img)


def get_sick_history_img(attach_photo):
    """
    :param attach_photo:
    :return:
    """
    try:
        return eval(attach_photo).get('sick_history_img')
    except Exception:
        return ''

register.filter('get_sick_history_img', get_sick_history_img)
