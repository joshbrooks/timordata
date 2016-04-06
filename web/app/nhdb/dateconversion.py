import psycopg2
import datetime
import os
import unicodedata
import datetime


conn = psycopg2.connect("dbname=import user=belun")
cur = conn.cursor()

cur.execute('select verified from tblpeople')
for date, in cur.fetchall():
    if date:

        try:
            if '-' in date:
                y,m,d = date.split(' ')[0].split('-')
            elif '/' in date:
                y,m,d = date.split(' ')[0].split('/')
            else:
                print 'no convert for %s'%date
                continue
        except ValueError:
            print 'invalid convert for %s'%date
            continue
        
        y, m, d = int(y), int(m), int(d)
        
        # Swap y, d if y > 1900
        
        if d > 1900:
            y,d = d,y
        if m > 12:
            m,d = d,m
        
        #print y,m,d

        dt = datetime.datetime(y,m,d).date()

        print date,
        print dt.isoformat()

