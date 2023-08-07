import os
from decouple import config

class Config(object):
    SECRET_KEY = config('SECRET_KEY', 'SET-THIS-ENV-VAR-IN-PROD!-esdas#!3de*o0alas')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_KEY = config('STRIPE_WEBHOOK_KEY')

class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    
    DB_HOST=config('DB_HOST')
    DB_PORT=config('DB_PORT', default='5432')
    DB_NAME=config('DB_NAME', default='sfra')
    DB_USERNAME=config('DB_USERNAME', default='dev')
    DB_PASSWORD=config('DB_PASSWORD', default='')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    CACHE_TYPE = 'redis'
    CACHE_KEY_PREFIX = 'appname-'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    DB_HOST=config('DB_HOST')
    DB_PORT=config('DB_PORT', default='5432')
    DB_NAME=config('DB_NAME', default='sfra')
    DB_USERNAME=config('DB_USERNAME', default='dev')
    DB_PASSWORD=config('DB_PASSWORD', default='')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    CACHE_TYPE = 'simple'