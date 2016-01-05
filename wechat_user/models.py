# coding: utf8
from __future__ import unicode_literals

from django.db import models

# Create your models here.


MALE = '0'
FEMALE = '1'
SEX_LIST = (
    (MALE, '男'),
    (FEMALE, '女'),
)
LEAVE_GROUP_LIST = (
    ('1', u'请假'),
    ('2', u'外出')
)

LEAVE_TYPE_LIST = (
    ('0', u'年假'),
    ('1', u'事假'),
    ('2', u'病假'),
    ('3', u'产假'),
    ('4', u'会议'),
    ('5', u'培训'),
    ('6', u'出差'),
    ('7', u'其他'),
)

LEAVE_MESSAGE_STATUS = (
    ('0', u'取消'),
    ('1', u'审核中'),
    ('2', u'未通过', ),
    ('3', u'通过'),
    ('4', u'已完成'),
)


class WXUser(models.Model):
    department = models.CharField(max_length=30, blank=True, verbose_name='部门')
    work_num = models.CharField(max_length=30, verbose_name='工号')
    name = models.CharField(max_length=20, verbose_name='姓名')
    cell_phone = models.CharField(max_length=20, verbose_name='手机')
    email = models.CharField(max_length=100, verbose_name='邮箱')
    wx_openid = models.CharField(max_length=50, blank=True, verbose_name='用户微信openid')
    wx_nickname = models.CharField(max_length=100, blank=True, verbose_name='wx昵称')
    sex = models.CharField(max_length=2, choices=SEX_LIST, blank=True, verbose_name='性别')
    direct_director = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='直接主管',
                                        related_name='director')
    dept_leader = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='部门领导',
                                    related_name='leader')
    working_years = models.IntegerField(verbose_name='工作年限')
    company_working_years = models.IntegerField(verbose_name='企业工作年限')
    legal_vacation_days = models.FloatField(default=5, verbose_name='剩余法定年假数')
    company_vacation_days = models.FloatField(default=0, verbose_name='剩余企业年假数')

    def __unicode__(self):
        return self.name


class Leave(models.Model):
    group = models.IntegerField(choices=LEAVE_GROUP_LIST, verbose_name='请假/外出')
    type = models.IntegerField(choices=LEAVE_TYPE_LIST, verbose_name='具体类别')
    leave_start_datetime = models.DateTimeField(verbose_name='开始时间')
    leave_end_datetime = models.DateTimeField(verbose_name='结束时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    leave_days = models.FloatField(verbose_name='天数')
    leave_reason = models.TextField(verbose_name='原因')
    remark = models.TextField(blank=True, verbose_name='备注')
    applicant_name = models.CharField(max_length=20, verbose_name='申请人姓名')
    applicant_openid = models.CharField(max_length=50, blank=True, verbose_name='申请者微信open_id')
    status = models.IntegerField(choices=LEAVE_MESSAGE_STATUS, verbose_name='状态')
    next_dealer = models.ForeignKey(WXUser, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='下个审核人')
    deal_end_time = models.DateTimeField(null=True, verbose_name='审批结束时间')
    refuse_reason = models.TextField(blank=True, verbose_name='拒绝原因')
    attach_photo = models.TextField(blank=True, verbose_name='上传附件图片')  # 为字典形式的字符串

    def __unicode__(self):
        return '%s,%s,%s' % (self.leave_user_name, self.group, self.leave_start_time)









