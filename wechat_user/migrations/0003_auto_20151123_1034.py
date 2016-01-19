# -*- coding: utf-8 -*-
# Generated by Django 1.9c1 on 2015-11-23 10:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_user', '0002_auto_20151119_1627'),
    ]

    operations = [
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(choices=[('1', '\u8bf7\u5047'), ('2', '\u5916\u51fa')], max_length=2, verbose_name='\u8bf7\u5047/\u5916\u51fa')),
                ('type', models.CharField(max_length=2, verbose_name='\u5177\u4f53\u7c7b\u522b')),
                ('leave_start_datetime', models.DateTimeField(verbose_name='\u5f00\u59cb\u65f6\u95f4')),
                ('leave_end_datetime', models.DateTimeField(verbose_name='\u7ed3\u675f\u65f6\u95f4')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u7533\u8bf7\u65f6\u95f4')),
                ('leave_days', models.FloatField(verbose_name='\u5929\u6570')),
                ('leave_reason', models.TextField(verbose_name='\u539f\u56e0')),
                ('remark', models.TextField(blank=True, verbose_name='\u5907\u6ce8')),
                ('leave_user_name', models.CharField(max_length=20, verbose_name='\u7533\u8bf7\u4eba\u59d3\u540d')),
                ('status', models.CharField(choices=[('0', '\u53d6\u6d88'), ('1', '\u5ba1\u6838\u4e2d'), ('2', '\u672a\u901a\u8fc7'), ('3', '\u901a\u8fc7'), ('4', '\u5df2\u5b8c\u6210')], max_length=10, verbose_name='\u72b6\u6001')),
                ('deal_end_time', models.DateField(verbose_name='\u5ba1\u6279\u7ed3\u675f\u65f6\u95f4')),
            ],
        ),
        migrations.RemoveField(
            model_name='wxuser',
            name='leader',
        ),
        migrations.AddField(
            model_name='wxuser',
            name='dept_leader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leader', to='wechat_user.WXUser', verbose_name='\u90e8\u95e8\u9886\u5bfc'),
        ),
        migrations.AddField(
            model_name='wxuser',
            name='direct_director',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='director', to='wechat_user.WXUser', verbose_name='\u76f4\u63a5\u4e3b\u7ba1'),
        ),
        migrations.AddField(
            model_name='leave',
            name='next_dealer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wechat_user.WXUser', verbose_name='\u4e0b\u4e2a\u5ba1\u6838\u4eba'),
        ),
    ]