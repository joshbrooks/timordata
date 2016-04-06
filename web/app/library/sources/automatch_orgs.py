import logging
import sys

__author__ = 'josh'

# Generate a CSV file to automatically match organization names from the input CSV's


logging.basicConfig(level=logging.INFO)
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'belun.settings'
sys.path.append(os.path.join(os.path.abspath('.'), '../'))
import django

django.setup()

from geo.models import World, AdminArea
from library.models import *
from nhdb.models import Organization, PropertyTag, OrganizationClass
import unicodecsv as csv
from django.core.files import File
# Create your tests here.
from fuzzywuzzy import fuzz

import fuzzywuzzy
from unidecode import unidecode
data_dir = '/home/josh/Desktop/DATA_CENTRE/'

input_organisation_names = []
for root,d,f in os.walk(data_dir):
    for filename in f:
        if filename.endswith('.csv'):
            print root
            print filename
            source_file = os.path.join(root,filename)

            reader = csv.DictReader(open(source_file, 'r'))
            for r in reader:

                print r

                if not r.get('org'):
                    continue
                for n in [n.strip() for n in r.get('org').split(',')]:
                    print n
                    if n not in input_organisation_names:
                        input_organisation_names.append(n)
organisations = Organization.objects.values_list('name','pk').all()

organisation_names = [o[0] for o in organisations]

matches = {}

f = open('automatch_orgs.csv', 'w')
w = csv.DictWriter(f, ['name', 'tokensort', 'ts_ratio', 'partial','partial_ratio', 'simple', 'simple_ratio'])

for i in input_organisation_names:

    write = {'name': i}

    ts_ratio, ts_organisation_name = 0, None
    for j in organisation_names:
        _ratio = fuzz.token_set_ratio(i,j)
        if _ratio > ts_ratio and _ratio > 70:
            write['tokensort'], write['ts_ratio'] = _ratio, j

    partial_ratio, part_organisation_name = 0, None
    for j in organisation_names:
        _ratio = fuzz.partial_ratio(i,j)
        if _ratio > partial_ratio and _ratio > 70:
            write['partial'], write['partial_ratio'] = _ratio, j

    simple_ratio, simple_organisation_name = 0, None
    for j in organisation_names:
        _ratio = fuzz.ratio(i,j)
        if _ratio > simple_ratio and _ratio > 70:
            write['simple'], write['simple_ratio'] = _ratio, j

    print write
    w.writerow(write)
