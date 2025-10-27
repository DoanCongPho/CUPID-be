step:
     - install poetry
     - run: poetry env activate
     - run: poetry install
     - run: python manage.py runserver  (to start the project)