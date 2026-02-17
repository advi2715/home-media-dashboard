# Home Media Dashboard

A lightweight dashboard for monitoring your home media stack (Plex, Qbittorrent, Sonarr, Radarr, Overseerr).

## Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/advi2715/home-media-dashboard/main/install.sh | bash
```

### Manual Install

1. Download the latest release from [Releases](https://github.com/advi2715/home-media-dashboard/releases)
2. Extract and run:
   ```bash
   tar xzf media-dashboard-*.tar.gz
   cd media-dashboard-*/
   bash install.sh
   ```

### Upgrading from .deb or Arch Package

If you previously installed via `.deb` or Arch package, the installer will detect and offer to remove the old package automatically. Your configuration is preserved.

### Uninstalling

```bash
curl -fsSL https://raw.githubusercontent.com/advi2715/home-media-dashboard/main/install.sh | bash -s -- --uninstall
```

Or if you have the script locally:
```bash
bash install.sh --uninstall
```

## Configuration

The service loads configuration from `~/.config/media-dashboard/env`.

The installer creates a config template automatically. Edit it with your details:

```bash
nano ~/.config/media-dashboard/env
```

```bash
# Server Configuration
PORT=7152

# Plex
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_plex_token_here

# Qbittorrent
QBITTORRENT_URL=http://localhost:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Sonarr
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_sonarr_api_key

# Radarr
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_radarr_api_key

# Overseerr
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=your_overseerr_api_key
```

## How to Obtain API Keys

### Plex Token (`PLEX_TOKEN`)
1.  Sign in to Plex.tv in your browser.
2.  Click on any media item (movie or episode).
3.  Click the three dots **(...)** menu > **Get Info**.
4.  Click **View XML**.
5.  A new tab will open with XML data. Look at the URL bar.
6.  The token is the string after `X-Plex-Token=`.
    - Example: `...&X-Plex-Token=abc123xyz...` -> Application Token is `abc123xyz`.

### Sonarr / Radarr / Overseerr API Key
1.  Open the application in your browser.
2.  Go to **Settings** > **General**.
3.  Scroll down to the **Security** (or API) section.
4.  Copy the **API Key**.

### Qbittorrent Credentials
-   **Username**: Default is `admin`.
-   **Password**: Default is `adminadmin`.
-   **Note**: If you have "Bypass authentication for clients on localhost" checked in Qbittorrent settings, you may still need to provide credentials in the `.env` file, or ensure the dashboard is running on the same machine.

## Starting the Service

Enable and start the user service:

```bash
systemctl --user enable --now media-dashboard
```

Check the status:

```bash
systemctl --user status media-dashboard
```

View logs:
```bash
journalctl --user -u media-dashboard -f
```

## Access

Open your browser and navigate to:
[http://localhost:7152](http://localhost:7152)

## Troubleshooting

-   **Service fails to start:** Check logs (`journalctl --user -u media-dashboard`)
-   **"URL not configured":** Ensure `~/.config/media-dashboard/env` exists and is populated correctly
-   **After update:** Restart the service (`systemctl --user restart media-dashboard`)
