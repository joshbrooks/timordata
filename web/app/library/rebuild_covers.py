#!/usr/bin/python
# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile
import subprocess
import sys
import logging
import os
import re

logging.basicConfig(level=logging.WARN)

os.environ['DJANGO_SETTINGS_MODULE'] = 'belun.settings'
sys.path.append(os.path.join(os.path.abspath('.'), '../'))
import django
django.setup()
from library.models import *
from django.core.files import File
import os
from library.sources.import_csv import versions_thumbnail

versions_thumbnail()
