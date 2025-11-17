"""
Spotify playlist management views.
"""
import json
import base64
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api import token_manager


def refresh_access_token(request=None):
    """
    Helper function to refresh the access token using the refresh token.
    Now uses global token storage instead of session.
    """
    refresh_token = token_manager.get_refresh_token()
    
    if not refresh_token:
        return None
    
    token_url = 'https://accounts.spotify.com/api/token'
    
    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials_b64}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Update access token in global storage
        new_access_token = token_data.get('access_token')
        token_manager.update_access_token(
            access_token=new_access_token,
            expires_in=token_data.get('expires_in', 3600)
        )
        
        # If refresh token is rotated, update it too
        if token_data.get('refresh_token'):
            # Full token update with new refresh token
            token_manager.save_tokens(
                access_token=new_access_token,
                refresh_token=token_data.get('refresh_token'),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_in=token_data.get('expires_in', 3600)
            )
        
        return new_access_token
        
    except Exception:
        return None


def get_access_token(request=None):
    """
    Helper function to get access token from global storage.
    No longer dependent on session/request.
    """
    return token_manager.get_access_token()


@csrf_exempt
@require_http_methods(["POST"])
def add_song_to_playlist(request):
    """
    Add a song to a Spotify playlist.
    
    Expected JSON body:
    {
        "playlist_id": "spotify_playlist_id",
        "song_id": "spotify_track_id"
    }
    
    Note: song_id should be just the track ID, not the full URI.
    The endpoint will construct the proper Spotify URI.
    """
    access_token = get_access_token()
    
    if not access_token:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated. Please authenticate with Spotify first.'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        song_id = data.get('song_id')
        
        if not playlist_id or not song_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: playlist_id and song_id'
            }, status=400)
        
        # Construct Spotify track URI if not already in URI format
        if not song_id.startswith('spotify:track:'):
            track_uri = f'spotify:track:{song_id}'
        else:
            track_uri = song_id
        
        # Spotify API endpoint to add tracks
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'uris': [track_uri]
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            snapshot_id = response.json().get('snapshot_id')
            return JsonResponse({
                'success': True,
                'message': 'Song added to playlist successfully',
                'snapshot_id': snapshot_id,
                'playlist_id': playlist_id,
                'song_id': song_id
            })
        elif response.status_code == 401:
            # Try to refresh the token
            new_token = refresh_access_token()
            if new_token:
                # Retry with new token
                headers['Authorization'] = f'Bearer {new_token}'
                retry_response = requests.post(url, headers=headers, json=payload)
                
                if retry_response.status_code == 201:
                    snapshot_id = retry_response.json().get('snapshot_id')
                    return JsonResponse({
                        'success': True,
                        'message': 'Song added to playlist successfully (token refreshed)',
                        'snapshot_id': snapshot_id,
                        'playlist_id': playlist_id,
                        'song_id': song_id
                    })
            
            return JsonResponse({
                'success': False,
                'error': 'Access token expired and refresh failed. Please re-authenticate at /login'
            }, status=401)
        else:
            error_data = response.json()
            return JsonResponse({
                'success': False,
                'error': error_data.get('error', {}).get('message', 'Failed to add song to playlist'),
                'status_code': response.status_code
            }, status=response.status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Request to Spotify API failed: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def remove_song_from_playlist(request):
    """
    Remove a song from a Spotify playlist.
    
    Expected JSON body:
    {
        "playlist_id": "spotify_playlist_id",
        "song_id": "spotify_track_id"
    }
    
    Note: song_id should be just the track ID, not the full URI.
    The endpoint will construct the proper Spotify URI.
    """
    access_token = get_access_token()
    
    if not access_token:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated. Please authenticate with Spotify first.'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        song_id = data.get('song_id')
        
        if not playlist_id or not song_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: playlist_id and song_id'
            }, status=400)
        
        # Construct Spotify track URI if not already in URI format
        if not song_id.startswith('spotify:track:'):
            track_uri = f'spotify:track:{song_id}'
        else:
            track_uri = song_id
        
        # Spotify API endpoint to remove tracks
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'tracks': [
                {
                    'uri': track_uri
                }
            ]
        }
        
        response = requests.delete(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            snapshot_id = response.json().get('snapshot_id')
            return JsonResponse({
                'success': True,
                'message': 'Song removed from playlist successfully',
                'snapshot_id': snapshot_id,
                'playlist_id': playlist_id,
                'song_id': song_id
            })
        elif response.status_code == 401:
            # Try to refresh the token
            new_token = refresh_access_token()
            if new_token:
                # Retry with new token
                headers['Authorization'] = f'Bearer {new_token}'
                retry_response = requests.delete(url, headers=headers, json=payload)
                
                if retry_response.status_code == 200:
                    snapshot_id = retry_response.json().get('snapshot_id')
                    return JsonResponse({
                        'success': True,
                        'message': 'Song removed from playlist successfully (token refreshed)',
                        'snapshot_id': snapshot_id,
                        'playlist_id': playlist_id,
                        'song_id': song_id
                    })
            
            return JsonResponse({
                'success': False,
                'error': 'Access token expired and refresh failed. Please re-authenticate at /login'
            }, status=401)
        else:
            error_data = response.json()
            return JsonResponse({
                'success': False,
                'error': error_data.get('error', {}).get('message', 'Failed to remove song from playlist'),
                'status_code': response.status_code
            }, status=response.status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Request to Spotify API failed: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)
