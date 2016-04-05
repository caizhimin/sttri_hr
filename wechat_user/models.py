# coding: utf8
from __future__ import unicode_literals
from datetime import datetime, timedelta
from django.db import models
from django.utils.html import format_html


# Create your models here.

SEX_LIST = (
    (0, '男'),
    (1, '女'),
)
LEAVE_GROUP_LIST = (
    (1, u'请假'),
    (2, u'外出')
)

LEAVE_TYPE_LIST = (
    (0, u'法定年假'),
    (8, u'企业年假'),
    (1, u'事假'),
    (2, u'病假'),
    (3, u'产假'),
    (4, u'会议'),
    (5, u'培训'),
    (6, u'出差'),
    (7, u'其他'),
)

LEAVE_MESSAGE_STATUS = (
    (0, u'已取消'),
    (1, u'审核中'),  # 可取消, 不可销假
    (2, u'未通过', ),
    (3, u'已通过'),  # 生效时间前可取消， 可销假
    (4, u'已完成'),
)

IS_LEADER_STATUS = ((0, '否'), (1, '是'))
IS_TIMEKEEPER_STATUS = IS_LEADER_STATUS


class WXUser(models.Model):
    department = models.CharField(max_length=30, verbose_name='部门')
    work_num = models.CharField(max_length=30, verbose_name='工号')
    name = models.CharField(max_length=20, verbose_name='姓名')
    cell_phone = models.CharField(max_length=20, verbose_name='手机')
    email = models.CharField(max_length=100, verbose_name='邮箱')
    wx_openid = models.CharField(max_length=50, blank=True, verbose_name='微信openid')
    wx_nickname = models.CharField(max_length=100, blank=True, verbose_name='微信昵称')
    sex = models.IntegerField(choices=SEX_LIST, blank=True, verbose_name='性别')
    direct_director = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='直接主管',
                                        related_name='director')
    dept_leader = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='部门领导',
                                    related_name='leader')
    working_years = models.IntegerField(verbose_name='工作年限')
    company_working_years = models.IntegerField(verbose_name='企业工作年限')
    legal_vacation_days = models.FloatField(default=5, verbose_name='剩余法定年假数')
    company_vacation_days = models.FloatField(default=0, verbose_name='剩余企业年假数')
    is_leader = models.IntegerField(choices=IS_LEADER_STATUS, verbose_name='是否为管理序列')
    is_timekeeper = models.IntegerField(choices=IS_TIMEKEEPER_STATUS, default=0, verbose_name='是否为部门考勤员')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = '员工信息'
        verbose_name = '员工信息'


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
    all_dealers = models.CharField(max_length=10, blank=True, default='', verbose_name='审批过的人')
    deal_end_time = models.DateTimeField(null=True, verbose_name='审批结束时间')
    refuse_reason = models.TextField(blank=True, verbose_name='拒绝原因')
    attach_photo = models.TextField(blank=True, verbose_name='上传附件图片')  # 为字典形式的字符串

    def __unicode__(self):
        return '%s' % self.applicant_name

    def show_attach_photo_for_admin(self):
        if self.attach_photo:
            attach_photo = eval(self.attach_photo)
            return format_html('<img src="%s" width="300px" style="margin-right:30px" /><img src="%s" width="300px"/>' %
                               (attach_photo['sick_level_img'], attach_photo['sick_history_img']))
        else:
            return '无'

    @property
    def gt_start_time_lt_end_time(self):
        """
        开始和结束时间之前,可以提前返回
        :return:
        """
        if self.leave_end_datetime > datetime.now() > self.leave_start_datetime:
            return True
        return False

    @property
    def lt_start_time(self):
        """
        开始时间之前,可以取消
        :return:
        """
        if datetime.now() < self.leave_start_datetime:
            return True
        return False

    show_attach_photo_for_admin.short_description = '附件图片'

    class Meta:
        verbose_name_plural = '请假/外出信息'









