# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-12-21 10:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0004_auto_20151221_1003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wxuser',
            name='company_vacation_days',
            field=models.FloatField(default=0, verbose_name='\u5269\u4f59\u4f01\u4e1a\u5e74\u5047\u6570'),
        ),
        migrations.AlterField(
            model_name='wxuser',
            name='legal_vacation_days',
            field=models.FloatField(default=5, verbose_name='\u5269\u4f59\u6cd5\u5b9a\u5e74\u5047\u6570'),
        ),
    ]