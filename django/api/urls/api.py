"""
URL configuration for API endpoints.
"""
from django.urls import path
from api.views import playlist

urlpatterns = [
    path('playlist/add', playlist.add_song_to_playlist, name='add_song'),
    path('playlist/remove', playlist.remove_song_from_playlist, name='remove_song'),
]
