# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-30 12:20
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminArea',
            fields=[
                ('path', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('pcode', models.IntegerField(primary_key=True, serialize=False)),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=4326)),
                ('envelope', django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326)),
                ('leafletextent', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlaceAlternate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=32751)),
            ],
        ),
        migrations.CreateModel(
            name='Road',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.MultiLineStringField(srid=32751)),
                ('osm_id', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=255, null=True)),
                ('highway', models.CharField(max_length=255, null=True)),
                ('route', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Town',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=32751)),
                ('name', models.TextField()),
                ('size', models.IntegerField(choices=[(1, 'Major town'), (2, 'Minor town'), (3, 'Hamlet')])),
            ],
        ),
        migrations.CreateModel(
            name='World',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iso3', models.CharField(max_length=3, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=4326)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Worldsimple',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iso3', models.CharField(max_length=3)),
                ('name', models.CharField(max_length=100)),
                ('geom', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('adminarea_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='geo.AdminArea')),
            ],
            options={
                'abstract': False,
            },
            bases=('geo.adminarea',),
        ),
        migrations.CreateModel(
            name='Subdistrict',
            fields=[
                ('adminarea_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='geo.AdminArea')),
            ],
            options={
                'abstract': False,
            },
            bases=('geo.adminarea',),
        ),
        migrations.CreateModel(
            name='Suco',
            fields=[
                ('adminarea_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='geo.AdminArea')),
            ],
            options={
                'abstract': False,
            },
            bases=('geo.adminarea',),
        ),
    ]