"""
Django settings for hxw_blog project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import json
import sys
import tempfile
import pymysql

from logging.handlers import TimedRotatingFileHandler

pymysql.install_as_MySQLdb()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_ROOT = os.path.dirname(REPO_ROOT)

sys.path.append(os.path.join(PROJECT_ROOT, 'djangoapps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(jewtgm=p#i!meyny@p)$+!_utfidoae(=h!%e0+3u#!8149u^'

with open(os.path.join(ENV_ROOT, 'hxw_blog.env.json')) as env_file:
    ENV_TOKENS = json.load(env_file)

with open(os.path.join(ENV_ROOT, 'hxw_blog.auth.json')) as auth_file:
    AUTH_TOKENS = json.load(auth_file)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV_TOKENS['DEBUG']

SITE_NAME = ENV_TOKENS['SITE_NAME']
HOST = ENV_TOKENS['HOST']
HTTPS = ENV_TOKENS['HTTPS']

ALLOWED_HOSTS = [
    '*'
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'utils',
    'error_handler',
    'ueditor',
    'account',
    'index',
    'article',
    'site_info',
    'restful_api'
]

MIDDLEWARE = [
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'hxw_blog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.csrf',
                'django.contrib.messages.context_processors.messages',
                'utils.context_processors.site_info'
            ],
        },
    },
]

WSGI_APPLICATION = 'hxw_blog.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = AUTH_TOKENS['DATABASES']

SESSION_COOKIE_DOMAIN = ENV_TOKENS['SESSION_COOKIE_DOMAIN']
SESSION_SAVE_EVERY_REQUEST = True

######################### MARKETING SITE ###############################
LOGGED_IN_COOKIE_NAME = ENV_TOKENS['LOGGED_IN_COOKIE_NAME']
USER_INFO_COOKIE_NAME = ENV_TOKENS['USER_INFO_COOKIE_NAME']
USER_INFO_COOKIE_VERSION = 1

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = ENV_TOKENS['LANGUAGE_CODE']

TIME_ZONE = ENV_TOKENS['TIME_ZONE']

USE_I18N = True

USE_L10N = True

USE_TZ = True

APPEND_SLASH = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'static')
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(REPO_ROOT, 'staticfiles')

MEDIA_ROOT = os.path.join(ENV_ROOT, 'media')
MEDIA_URL = '/media/'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/account/login'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'formatters': {
        'standard': {
            'format': '%(levelname)s %(asctime)s %(pathname)s %(filename)s %(module)s %(funcName)s %(lineno)d: %(message)s'
        },
        # INFO 2016-09-03 16:25:20,067 /home/ubuntu/mysite/views.py views.py views get 29: some info...
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'standard'
        },
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(ENV_ROOT, 'log/hxw_blog/django.log'),
            'formatter': 'standard',
            'when': 'D',
            'interval': 1,
            'encoding': 'utf-8',
            'backupCount': 60
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True  # 是否继承父类的log信息
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = ENV_TOKENS['EMAIL_HOST']
EMAIL_PORT = ENV_TOKENS['EMAIL_PORT']
EMAIL_HOST_USER = ENV_TOKENS['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = AUTH_TOKENS['EMAIL_HOST_PASSWORD']
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
MAIL_USE_TLS = ENV_TOKENS['MAIL_USE_TLS']
EMAIL_USE_SSL = ENV_TOKENS['EMAIL_USE_SSL']
EMAIL_SUBJECT_PREFIX = ENV_TOKENS['EMAIL_SUBJECT_PREFIX']
DEFAULT_FROM_EMAIL_DISPLAY = '{prefix} <{from_address}>'.format(prefix=EMAIL_SUBJECT_PREFIX,
                                                                from_address=DEFAULT_FROM_EMAIL)

# Pagination settings
DEFAULT_PAGE_SIZE = ENV_TOKENS['DEFAULT_PAGE_SIZE']

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# CACHE_MIDDLEWARE_SECONDS = 60 * 5
# CACHE_MIDDLEWARE_KEY_PREFIX = ""

# Django rest framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'utils.paginators.StandardResultsSetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler'
}

################################## Social login ################################
WEIBO_APP_KEY = AUTH_TOKENS['WEIBO_APP_KEY']
WEIBO_APP_SECRET = AUTH_TOKENS['WEIBO_APP_SECRET']
WEIBO_LOGIN_REDIRECT_URI = ENV_TOKENS['WEIBO_LOGIN_REDIRECT_URI']

QQ_APP_KEY = AUTH_TOKENS['QQ_APP_KEY']
QQ_APP_SECRET = AUTH_TOKENS['QQ_APP_SECRET']
QQ_LOGIN_REDIRECT_URI = ENV_TOKENS['QQ_LOGIN_REDIRECT_URI']

WECHAT_APP_KEY = AUTH_TOKENS['WECHAT_APP_KEY']
WECHAT_APP_SECRET = AUTH_TOKENS['WECHAT_APP_SECRET']
WECHAT_LOGIN_REDIRECT_URI = ENV_TOKENS['WECHAT_LOGIN_REDIRECT_URI']

# alipay
ALIPAY_LOGIN_REDIRECT_URI = ENV_TOKENS['ALIPAY_LOGIN_REDIRECT_URI']
ALIPAY_URL = AUTH_TOKENS['ALIPAY']['ALIPAY_URL']
ALIPAY_APPID = AUTH_TOKENS['ALIPAY']['APPID']
ALIPAY_FORMAT = AUTH_TOKENS['ALIPAY']['FORMAT']
ALIPAY_CHARSET = AUTH_TOKENS['ALIPAY']['CHARSET']
ALIPAY_SIGN_TYPE = AUTH_TOKENS['ALIPAY']['SIGN_TYPE']
ALIPAY_VERSION = AUTH_TOKENS['ALIPAY']['VERSION']
