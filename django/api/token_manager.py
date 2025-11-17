"""
Global token manager for Spotify API access.
Stores tokens in a simple file that all requests can access.
"""
import json
import os
from pathlib import Path

TOKEN_FILE = Path('/app/tokens.json')


def save_tokens(access_token, refresh_token, token_type='Bearer', expires_in=3600):
    """Save tokens to file."""
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': token_type,
        'expires_in': expires_in
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)


def get_tokens():
    """Get tokens from file."""
    if not TOKEN_FILE.exists():
        return None
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def update_access_token(access_token, expires_in=3600):
    """Update just the access token (after refresh)."""
    tokens = get_tokens()
    if tokens:
        tokens['access_token'] = access_token
        tokens['expires_in'] = expires_in
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)


def get_access_token():
    """Get the current access token."""
    tokens = get_tokens()
    return tokens.get('access_token') if tokens else None


def get_refresh_token():
    """Get the current refresh token."""
    tokens = get_tokens()
    return tokens.get('refresh_token') if tokens else None
