# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-12-23 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0009_auto_20151223_0951'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leave',
            name='type',
            field=models.IntegerField(verbose_name='\u5177\u4f53\u7c7b\u522b'),
        ),
    ]
