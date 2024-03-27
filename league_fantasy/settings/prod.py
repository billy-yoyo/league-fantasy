from ._base import *

with open("/etc/secret.txt") as f:
  SECRET_KEY = f.read().strip()

ALLOWED_HOSTS = [
  ".euphoriadraft.co.uk"
]

STATIC_ROOT = "/var/www/league_fantasy/static"
