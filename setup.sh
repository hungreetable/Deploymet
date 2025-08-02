#!/bin/bash

#install dependancies
pip install setuptools
pip install -r requirements.txt

# run django command
python manage.py makemigrations
python manage.py migrate
python manage.py runserver


