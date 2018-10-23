# QStack
Django based web app. with functionality similar to StackOverflow

Used python version: 3.5
     django version: 2.0.2

Preparation:
'''
python3 manage.py migrate
python3 manage.py createsuperuser
'''
It's also can be useful to upload data from test database in test_content folder:
'''
python3 manage.py loaddata test_content/test_data.json
'''

Example of running the application:
'''
python3 manage.py runserver 0.0.0.0:8000
'''
Running of functional tests:
'''
python3 manage.py test tests
'''
  
