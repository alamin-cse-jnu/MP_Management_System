#!/bin/sh

python manage.py loaddata fixtures/initial/menu_data.json
python manage.py loaddata fixtures/initial/parliament_menu.json
python manage.py loaddata fixtures/initial/parliament_data.json
python manage.py loaddata fixtures/initial/mp_menu.json
python manage.py loaddata fixtures/initial/ministry_menu.json
python manage.py loaddata fixtures/initial/committee_menu.json
python manage.py loaddata fixtures/initial/institution_menu.json
python manage.py loaddata fixtures/initial/travel_menu.json
python manage.py loaddata fixtures/initial/reports_menu.json
python manage.py loaddata fixtures/initial/audit_menu.json