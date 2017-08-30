from .settings_secret import SECRET_KEY, DEBUG, CRISPY_FAIL_SILENTLY, DATABASES, ALLOWED_HOSTS
import os

from django.utils.translation import gettext_noop
import json
import django.conf.locale
from django.conf import global_settings

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# Add Tetun as a selectable language along with ID, EN and PT language codes
EXTRA_LANG_INFO = {
    'tet': {
        'bidi': False,
        'code': 'tet',
        'name': 'Tetun',
        'name_local': 'Tetun',
    },
}

global_settings.LANGUAGES += ('tet', gettext_noop('Tetun'))
# global_settings.LANGUAGES += ('ind', gettext_noop('Indonesian')),

LANGUAGES = (
    ('tet', gettext_noop('Tetun')),
    ('en', gettext_noop('English')),
    ('pt', gettext_noop('Portugese')),
    ('id', gettext_noop('Indonesian')),
)

LANGUAGES_FIX_ID = (
    ('tet', gettext_noop('Tetun')),
    ('en', gettext_noop('English')),
    ('pt', gettext_noop('Portugese')),
    ('ind', gettext_noop('Indonesian')),
)

LANG_INFO = dict(list(django.conf.locale.LANG_INFO.items()) + list(EXTRA_LANG_INFO.items()))
django.conf.locale.LANG_INFO = LANG_INFO

LOCALE_PATHS = (
    os.path.join(os.path.dirname(__file__), '..', 'locale'),
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            'memcached:11211',
        ]
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates/", ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = (
    'grappelli',
    'modeltranslation',  # Keep this above admin!!
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.sites',
    'django.contrib.flatpages',
    # 'debug_toolbar',

    # Contributed apps
    'rest_framework',
    'django_tables2',
    'crispy_forms',
    'django_extensions',

    'rest_framework_swagger',

    # My own applications
    'donormapping',
    'library',
    'nhdb',
    'geo',
    'suggest',

)

SITE_ID = 1  # For flatpages

CRISPY_TEMPLATE_PACK = 'bootstrap3'

MIDDLEWARE_CLASSES = (
    'belun.stats_middleware.StatsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',

    # Caching
    # 'django.middleware.cache.UpdateCacheMiddleware',
    # 'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
)

CACHE_MIDDLEWARE_ALIAS = 'default'
# CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = 'timordata.info'

ROOT_URLCONF = 'belun.urls'

WSGI_APPLICATION = 'belun.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = ['/var/www/html/static/']
MEDIA_ROOT = '/var/www/html/media/'
MEDIA_URL = '/media/'

MODELTRANSLATION_FALLBACK_LANGUAGES = ('en', 'tet', 'pt', 'id')
MODELTRANSLATION_TRANSLATION_REGISTRY = 'translation'

GRAPPELLI_AUTOCOMPLETE_SEARCH_FIELDS = {
    "geo": {
        "world": ("iso3__icontains", "name__icontains",),
        "adminarea": ("name__icontains",),
    },
    "nhdb": {
        "organization": ("id__iexact", "name__icontains",),
        "project": ("id__iexact", "name__icontains",),
        "publication": ("id__iexact", "name__icontains",),
        "propertytag": ("name__icontains",),
    },
    "donormapping": {
        'fundingoffer': ('name__icontains',)
    },
    "library": {
        "tag": ('name__icontains',),

    }
}

INTERNAL_IPS = ['127.0.0.1', '172.18.0.1']

GRAPPELLI_ADMIN_TITLE = "Timor-Leste Data Center"

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEN = 'pillow'

CKEDITOR_CONFIGS = {
    'custom': {
        'extraPlugins': ['divarea'],
        'toolbar': [
            {'name': 'document', 'items': ['Source', '-', 'NewPage', 'Preview', '-', 'Templates']},
            # Defines toolbar group with name (used to create voice label) and items in 3 subgroups.
            ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'],
            # Defines toolbar group without name.
            '/',  # Line break - next group will be placed in new line.
            {'name': 'basicstyles', 'items': ['Bold', 'Italic']}
        ]
    },
    'awesome_ckeditor': {
        'toolbar': [["Format", "Bold", "Italic", "Underline", "Strike", "SpellChecker"],
                    ['NumberedList', 'BulletedList', "Indent", "Outdent", 'JustifyLeft', 'JustifyCenter',
                     'JustifyRight', 'JustifyBlock'],
                    ["Image", "Table", "Link", "Unlink", "Anchor", "SectionLink", "Subscript", "Superscript"],
                    ['Undo', 'Redo'], ["Source"],
                    ["Maximize"]],
    },
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': 300,
    },
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGE_SIZE': 100,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination'

}
LOGIN_REDIRECT_URL = '/'
DATETIME_FORMAT = 'Y-m-d H:i:sO'
DATE_FORMAT = 'Y-m-d'
SELECT2_BOOTSTRAP = True
AUTO_RENDER_SELECT2_STATICS = False

STATIC_URL = '/static/'
STATICFILES_DIRS = ['/home/josh/Desktop/timordata_media/static']
MEDIA_ROOT = '/home/josh/Desktop/timordata_media/media'
MEDIA_URL = '/media/'
# STATIC_ROOT = '/home/josh/Desktop/timordata_media/collect/'
