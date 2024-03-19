from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout

def newroom(request):
    return redirect('/myapp')
