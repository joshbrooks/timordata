#!/bin/bash
export SOURCEDIR=`pwd`
export PROJECTNAME=app
export APPNAME=belun
export PIDFILE=/tmp/master_timordata.pid
export SERVER=0.0.0.0
export HTTPSOCK=3031
export PROCESSES=5
export HARA=20
export REQUESTS=5000
export WSGIFILE=wsgi.py
export DJANGO_SETTINGS_MODULE=${APPNAME}.settings
export VIRTUALENV=/home/josh/.virtualenvs/timordata
# nohup \
uwsgi --ini uwsgi.template.ini 
