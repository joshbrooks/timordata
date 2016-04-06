SECRET_KEY = '4gpe9e)-#$_nlhc@d+72d9dt&0fc5fdhgf7z1fgo9go_09$nxk'
DEBUG = True # SECURITY WARNING: don't run with debug turned on in production!
CRISPY_FAIL_SILENTLY = False # in production make this True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'django',
        'NAME': 'timordata.info',
        'PASSWORD': 'L1terary20@',
        'HOST': 'db'
    }
}
