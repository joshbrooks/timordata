FROM ubuntu:latest

MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"
ENV DEBIAN_FRONTEND=noninteractive

RUN route -n | awk '/^0.0.0.0/ {print $2}' > /tmp/host_ip.txt; nc -zv `cat /tmp/host_ip.txt` 3142 &> /dev/null && if [ $? -eq 0 ]; then echo "Acquire::http::Proxy \"http://$(cat /tmp/host_ip.txt):3142\";" > /etc/apt/apt.conf.d/30proxy; echo "Proxy detected on docker host - using for this build"; fi

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y \
		python \
		gcc \
		gettext \
		mysql-client libmysqlclient-dev \
		postgresql-client libpq-dev \
		sqlite3 \
		python-dev \
		python-pip \
                libgeos-c1 \
		imagemagick

# Requirements for Pillow
RUN apt-get install -y python-dev libjpeg8 zlib1g libtiff5 libfreetype6 liblcms2-2 libwebp5 libtk8.6
RUN apt-get install -y libjpeg8-dev zlib1g-dev libtiff5-dev libfreetype6-dev
RUN apt-get install -y libmagickwand-dev

RUN if [ -f "/etc/apt/apt.conf.d/30proxy" ]; then rm /etc/apt/apt.conf.d/30proxy; fi

# COPY ./get-pip.py /tmp
# RUN python /tmp/get-pip.py
RUN pip install -U pip
RUN pip install virtualenv
RUN useradd -U -ms /bin/bash django

RUN mkdir -p /home/django/.cache/pip
COPY ./pip /home/django/.cache/pip
RUN chown -R django:django /home/django/.cache
USER django
WORKDIR /home/django

RUN virtualenv /home/django/env
RUN mkdir -p /home/django/app/
COPY app/requirements.txt /home/django/

RUN mkdir -p /home/django/.cache
COPY pip /home/django/.cache

RUN . env/bin/activate && pip install -r /home/django/requirements.txt
RUN . env/bin/activate && pip install uwsgi
USER root
RUN rm -rf /home/django/.cache/pip
RUN mkdir -p /var/www/html/static/
RUN touch /var/www/html/static/test

USER django

EXPOSE 8000

# use Volume for the application
# CMD . env/bin/activate; python app/manage.py runserver 0.0.0.0:8000
# CMD . env/bin/activate; env/bin/uwsgi -H /home/django/env/ --ini app/uwsgi.ini

CMD ["env/bin/uwsgi", "--ini", "app/uwsgi.ini"]

