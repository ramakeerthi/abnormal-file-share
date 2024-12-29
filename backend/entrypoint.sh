#!/bin/bash

# Apply database migrations
python manage.py migrate

# Start the server
exec python manage.py runserver_plus --cert-file /app/certificates/localhost.crt --key-file /app/certificates/localhost.key 0.0.0.0:8000 