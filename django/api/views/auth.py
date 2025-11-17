"""
Spotify OAuth authentication views.
"""
import base64
import secrets
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlencode
from api import token_manager


def spotify_login(request):
    """
    Initiates the Spotify OAuth flow by redirecting to Spotify's authorization page.
    """
    # Clear any existing session data to start fresh
    request.session.flush()
    
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(16)
    request.session['oauth_state'] = state
    
    # Scopes needed for playlist modification
    scope = 'playlist-modify-public playlist-modify-private'
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'scope': scope,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'state': state,
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    return HttpResponseRedirect(auth_url)


@csrf_exempt
def spotify_callback(request):
    """
    Handles the callback from Spotify OAuth and exchanges the code for an access token.
    """
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        return JsonResponse({
            'success': False,
            'error': error
        }, status=400)
    
    # Verify state to prevent CSRF
    stored_state = request.session.get('oauth_state')
    if not state or state != stored_state:
        return JsonResponse({
            'success': False,
            'error': 'State mismatch - possible CSRF attack'
        }, status=400)
    
    # Exchange code for access token
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Prepare credentials
    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials_b64}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Store tokens in session (for browser)
        request.session['access_token'] = token_data.get('access_token')
        request.session['refresh_token'] = token_data.get('refresh_token')
        request.session['token_type'] = token_data.get('token_type')
        request.session['expires_in'] = token_data.get('expires_in')
        
        # ALSO store tokens globally for API access from VMs
        token_manager.save_tokens(
            access_token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_type=token_data.get('token_type'),
            expires_in=token_data.get('expires_in')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully authenticated with Spotify',
            'expires_in': token_data.get('expires_in')
        })
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def auth_status(request):
    """
    Check if the user is authenticated with Spotify.
    """
    access_token = request.session.get('access_token')
    
    if not access_token:
        return JsonResponse({
            'authenticated': False,
            'message': 'No access token found. Please authenticate first.'
        })
    
    # Optionally verify token with Spotify
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return JsonResponse({
                'authenticated': True,
                'user': {
                    'id': user_data.get('id'),
                    'display_name': user_data.get('display_name'),
                    'email': user_data.get('email')
                }
            })
        else:
            return JsonResponse({
                'authenticated': False,
                'message': 'Token is invalid or expired'
            })
            
    except requests.exceptions.RequestException:
        return JsonResponse({
            'authenticated': False,
            'message': 'Failed to verify token'
        }, status=500)
