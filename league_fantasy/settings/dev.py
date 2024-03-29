from ._base import *
import json

DEBUG = True
SECRET_KEY = 'django-insecure-wy-x^@wpwypzo7+lt!s+z$gcrddrs5mrb1)wihv0-vkb$u%)uo'

with open("bot.json") as f:
  bot = json.load(f)

BOT_USERNAME = bot["username"]
BOT_PASSWORD = bot["password"]
