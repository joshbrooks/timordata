# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-08 14:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nhdb', '0006_timetamp_new_models'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='activity',
            new_name='oldactivity',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='beneficiary',
            new_name='oldbeneficiary',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='sector',
            new_name='oldsector',
        ),
    ]