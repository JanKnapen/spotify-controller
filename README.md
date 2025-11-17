# Spotify Controller

A Docker-based application that provides OAuth authentication with Spotify API and internal API endpoints for playlist management accessible by VMs.

## Architecture

- **Port 80**: Public endpoint for Spotify OAuth authentication
- **Port 8001** (configurable): Internal API for VM access to manage playlists
- **Django**: Backend API server
- **Nginx**: Reverse proxy handling routing between public OAuth and internal API

## Prerequisites

- Docker and Docker Compose installed
- Spotify Developer Account
- Spotify App credentials (Client ID and Client Secret)

## Setup

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your **Client ID** and **Client Secret**
4. Add `http://localhost/callback` to the Redirect URIs in your app settings

### 2. Configure Environment Variables

Edit the `.env` file and add your Spotify credentials:

```env
SPOTIFY_CLIENT_ID=your_actual_client_id
SPOTIFY_CLIENT_SECRET=your_actual_client_secret
SPOTIFY_REDIRECT_URI=http://localhost/callback

DJANGO_SECRET_KEY=your_secure_random_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

INTERNAL_API_PORT=8001
```

### 3. Start the Application

```bash
docker-compose up -d
```

This will:
- Build the Django application
- Start Nginx reverse proxy
- Expose port 80 for OAuth and port 8001 for internal API

### 4. Check Service Status

```bash
docker-compose ps
docker-compose logs -f
```

## Usage

### Authentication Flow

#### 1. Initiate OAuth Login

Visit in your browser:
```
http://localhost/login
```

This redirects you to Spotify's authorization page.

#### 2. Authorize the Application

Grant permissions to the application (playlist-modify-public and playlist-modify-private).

#### 3. Handle Callback

After authorization, Spotify redirects to:
```
http://localhost/callback
```

The application exchanges the authorization code for an access token and stores it in the session.

#### 4. Check Authentication Status

```bash
curl http://localhost/status
```

Response:
```json
{
  "authenticated": true,
  "user": {
    "id": "user_id",
    "display_name": "User Name",
    "email": "user@example.com"
  }
}
```

### Internal API Endpoints (Port 8001)

These endpoints are accessible from internal VMs on port 8001.

#### Add Song to Playlist

**Endpoint:** `POST http://localhost:8001/api/playlist/add`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
  "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Song added to playlist successfully",
  "snapshot_id": "AAAABWylwl...",
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
  "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8001/api/playlist/add \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
    "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
  }'
```

#### Remove Song from Playlist

**Endpoint:** `POST http://localhost:8001/api/playlist/remove`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
  "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Song removed from playlist successfully",
  "snapshot_id": "AAAABWylwl...",
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
  "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8001/api/playlist/remove \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
    "song_id": "3n3Ppam7vgaVa1iaRUc9Lp"
  }'
```

## Finding Spotify IDs

### Playlist ID
1. Open Spotify
2. Right-click on a playlist
3. Select "Share" → "Copy link to playlist"
4. The URL looks like: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
5. The playlist ID is: `37i9dQZF1DXcBWIGoYBM5M`

### Track/Song ID
1. Right-click on a song
2. Select "Share" → "Copy link to song"
3. The URL looks like: `https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp`
4. The track ID is: `3n3Ppam7vgaVa1iaRUc9Lp`

## Security Notes

- **OAuth on Port 80**: Only OAuth endpoints are exposed on port 80
- **Internal API on Port 8001**: Playlist management endpoints are only on the internal port
- The reverse proxy (Nginx) enforces this separation:
  - Port 80 blocks `/api/*` paths
  - Port 8001 blocks `/auth/*` paths
- Access tokens are stored in Django sessions (database-backed)
- Tokens expire after 1 hour (configurable in `settings.py`)

## Network Configuration for VMs

To allow other VMs to access the internal API:

1. Find your host machine's IP address:
   ```bash
   ip addr show
   ```

2. From other VMs, access the API at:
   ```
   http://<host-ip>:8001/api/playlist/add
   http://<host-ip>:8001/api/playlist/remove
   ```

3. Ensure firewall allows connections on port 8001:
   ```bash
   sudo ufw allow 8001/tcp
   ```

## Troubleshooting

### Check Container Logs

```bash
docker-compose logs django
docker-compose logs nginx
```

### Restart Services

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
docker-compose down
docker-compose up -d --build
```

### Token Expired

If you get authentication errors, re-authenticate by visiting:
```
http://localhost/login
```

### Database Issues

Reset the database:
```bash
docker-compose down -v
docker-compose up -d
```

## Development

### Access Django Shell

```bash
docker-compose exec django python manage.py shell
```

### Run Django Management Commands

```bash
docker-compose exec django python manage.py <command>
```

### View Django Admin

1. Create a superuser:
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

2. Access admin at: `http://localhost/admin` (note: you'll need to update nginx config to proxy this)

## Project Structure

```
spotify-controller/
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment file
├── .gitignore
├── docker-compose.yml        # Docker services configuration
├── README.md
├── nginx/
│   ├── nginx.conf           # Main Nginx configuration
│   ├── public.conf          # Public OAuth endpoints (port 80)
│   └── internal.conf        # Internal API endpoints (port 8001)
└── django/
    ├── Dockerfile
    ├── requirements.txt
    ├── manage.py
    ├── spotify_controller/  # Django project
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    └── api/                 # Django app
        ├── __init__.py
        ├── apps.py
        ├── urls/
        │   ├── __init__.py
        │   ├── auth.py      # OAuth URL routes
        │   └── api.py       # Playlist API routes
        └── views/
            ├── __init__.py
            ├── auth.py      # OAuth views
            └── playlist.py  # Playlist management views
```

## API Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200/201`: Success
- `400`: Bad request (missing parameters, invalid JSON)
- `401`: Unauthorized (not authenticated or token expired)
- `403`: Forbidden (accessing restricted endpoint)
- `500`: Internal server error

## License

MIT
