#!/bin/bash

# Activate virtual environment and run Django development server
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000
