"""
URL configuration for spotify_controller project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('api.urls.auth')),
    path('api/', include('api.urls.api')),
]
