
# League Fantasy website

Requires the following python packages:

* django
* requests
* beautifulsoup4
* django-apscheduler

## Setup

* run `python manage.py migrate --settings settings.dev`

## Running in production

Put a secret file in `/etc/secret.txt` containing the server secret

* run `python manage.py migrate --settings=settings.dev`
* install gunicorn: `python -m pip install gunicorn`
* run `gunicorn league_fantasy.wsgi --env DJANGO_SETTINGS_MODULE=settings.prod`
* in another shell, run `python manage.py runapscheduler --settings settings.prod`


