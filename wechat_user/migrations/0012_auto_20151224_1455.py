# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-12-24 14:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0011_auto_20151223_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leave',
            name='status',
            field=models.IntegerField(choices=[('0', '\u53d6\u6d88'), ('1', '\u5ba1\u6838\u4e2d'), ('2', '\u672a\u901a\u8fc7'), ('3', '\u901a\u8fc7'), ('4', '\u5df2\u5b8c\u6210')], verbose_name='\u72b6\u6001'),
        ),
    ]
