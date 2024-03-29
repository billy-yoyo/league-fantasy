
# League Fantasy website

Requires the following python packages:

* django
* requests
* beautifulsoup4
* lxml
* django-apscheduler
* mwclient

## Setup

* run `python manage.py migrate --settings settings.dev`

## Running in production

Put a secret file in `/etc/secret.txt` containing the server secret
Put a file in `/etc/bot.txt` containing the bot username + password in JSON format with keys "username" and "password".

* run `python manage.py migrate --settings=settings.dev`
* install gunicorn: `python -m pip install gunicorn`
* run `gunicorn league_fantasy.wsgi --env DJANGO_SETTINGS_MODULE=settings.prod`
* in another shell, run `python manage.py runapscheduler --settings settings.prod`


