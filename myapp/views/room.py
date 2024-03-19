from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse

def newroom(request):
    return redirect('home')

def joinroom(request, room_id=None):
    uri = request.path
    # Vous pouvez également utiliser request.build_absolute_uri() si vous avez besoin de l'URI complet incluant le nom d'hôte

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>URI de la requête</title>
    </head>
    <body>
        <h1>URI de la requête : {uri}</h1>
    </body>
    </html>
    """
    
    return HttpResponse(html_content)
