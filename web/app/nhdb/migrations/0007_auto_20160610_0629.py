# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-10 06:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nhdb', '0006_auto_20160610_0605'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationPlaceDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suco', models.CharField(blank=True, max_length=256, null=True)),
                ('subdistrict', models.CharField(blank=True, max_length=256, null=True)),
                ('district', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='organizationplace',
            name='suco',
        ),
        migrations.AddField(
            model_name='organizationplacedescription',
            name='organizationplace',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nhdb.OrganizationPlace'),
        ),
    ]
