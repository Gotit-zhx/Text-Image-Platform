"""
URL configuration for backend_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import include, path

def healthz(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('healthz', healthz),
    path('', lambda request: JsonResponse({
        'message': 'Backend is running',
        'apiBase': '/api',
        'bootstrap': '/api/community/bootstrap',
    })),
    # Vue owns /admin/* in the same-origin deployment.
    path('django-admin/' if settings.PRODUCTION else 'admin/', admin.site.urls),
    path('api/', include('community.urls')),
]

from community.media import media_file
urlpatterns += [path('media/<int:media_id>/<str:variant>', media_file)]
