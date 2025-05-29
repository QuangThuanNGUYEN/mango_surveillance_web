# 🥭 Django Mango Surveillance System - Setup Guide

## **Project Overview**
A comprehensive Django-based agricultural surveillance system for mango growers featuring intelligent surveillance calculations, advanced analytics, and user data isolation.

pip install requirements.txt

Create a user with username 'grower' first to populate data

# Reset database if needed
rm db.sqlite3
python manage.py migrate
python manage.py shell < populate_data.py

