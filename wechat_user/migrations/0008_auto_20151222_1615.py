# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-12-22 16:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0007_wxuser_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leave',
            name='group',
            field=models.IntegerField(choices=[('1', '\u8bf7\u5047'), ('2', '\u5916\u51fa')], verbose_name='\u8bf7\u5047/\u5916\u51fa'),
        ),
    ]
