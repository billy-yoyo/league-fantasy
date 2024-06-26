from ._base import *
import json

with open("/etc/secret.txt") as f:
  SECRET_KEY = f.read().strip()

ALLOWED_HOSTS = [
  ".euphoriadraft.co.uk"
]

STATIC_ROOT = "/var/www/league_fantasy/static"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'gunicorn': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/opt/djangoprojects/reports/bin/gunicorn.errors',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        }
    },
    'loggers': {
        'gunicorn.errors': {
            'level': 'DEBUG',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
    }
}

with open("/etc/bot.json") as f:
  bot = json.load(f)

BOT_USERNAME = bot["username"]
BOT_PASSWORD = bot["password"]

