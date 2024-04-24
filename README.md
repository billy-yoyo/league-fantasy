
# League Fantasy website

Requires the following python packages:

* django
* lxml
* django-apscheduler
* mwclient

## Setup

* run `python manage.py migrate --settings league_fantasy.settings.[env]`
* run `python manage.py createsuperuser --settings league_fantasy.settings.[env]` and enter whatever details you want for the adminuser
* start the server with `python manage.py runserver --settings league_fantasy.settings.[env]`
* create a season & tournament via the `/admin` console (login using your superuser)
* run `python manage.py updategames -settings league_fantasy.settings.[env]` to fetch the latest team, player and game data for your tournament

## Running in production

Put a secret file in `/etc/secret.txt` containing the server secret
Put a file in `/etc/bot.json` containing the bot username + password in JSON format with keys "username" and "password".

* run `python manage.py migrate --settings=league_fantasy.settings.prod`
* install gunicorn: `python -m pip install gunicorn`
* run `gunicorn league_fantasy.wsgi --env DJANGO_SETTINGS_MODULE=league_fantasy.settings.prod`
* in another shell, run `python manage.py runapscheduler --settings league_fantasy.settings.prod`

Alternatively - just run `start.sh`

## Flags

Flags were sourced from https://github.com/lipis/flag-icons and copied here under the MIT license
