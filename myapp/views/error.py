# myapp/views/error.py

from django.shortcuts import render

def error(request, error=''):
    return render(request, 'myapp/error.html', {'error': error})