# myapp/views/error.py

from django.shortcuts import render

def error(request, error=''):
    render(request, 'myapp/error.html', {'error': error})