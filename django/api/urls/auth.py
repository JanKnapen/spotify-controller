"""
URL configuration for authentication endpoints.
"""
from django.urls import path
from api.views import auth

urlpatterns = [
    path('login', auth.spotify_login, name='spotify_login'),
    path('callback', auth.spotify_callback, name='spotify_callback'),
    path('status', auth.auth_status, name='auth_status'),
]
