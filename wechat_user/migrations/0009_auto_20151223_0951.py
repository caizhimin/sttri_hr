# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-12-23 09:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0008_auto_20151222_1615'),
    ]

    operations = [
        migrations.RenameField(
            model_name='leave',
            old_name='leave_user_name',
            new_name='applicant_name',
        ),
        migrations.AddField(
            model_name='leave',
            name='applicant_openid',
            field=models.CharField(blank=True, max_length=50, verbose_name='\u7533\u8bf7\u8005\u5fae\u4fe1open_id'),
        ),
        migrations.AlterField(
            model_name='wxuser',
            name='wx_openid',
            field=models.CharField(blank=True, max_length=50, verbose_name='\u7528\u6237\u5fae\u4fe1openid'),
        ),
    ]
