# Home Media Dashboard

A lightweight dashboard for monitoring your home media stack (Plex, Qbittorrent, Sonarr, Radarr).

## Installation

### Arch Linux
1.  Download the universal package (`any`):
    ```bash
    wget https://github.com/asdghsas35/home-media-dashboard/releases/download/v1.1.6/media-dashboard-1.1.6-1-any.pkg.tar.zst
    ```
2.  Install the package using `pacman`:
    ```bash
    sudo pacman -U media-dashboard-1.1.6-1-any.pkg.tar.zst
    ```

### Debian / Ubuntu (including Raspberry Pi)
1.  Download the universal package (`all`):
    ```bash
    wget https://github.com/asdghsas35/home-media-dashboard/releases/download/v1.1.6/media-dashboard_1.1.6_all.deb
    ```
2.  Install the package using `apt` (this automatically handles dependencies):
    ```bash
    sudo apt install ./media-dashboard_1.1.6_all.deb
    ```
    *Note: If you already ran `dpkg -i` and got errors, run `sudo apt-get install -f` to fix missing dependencies.*

## Configuration

The service runs as a user service and loads configuration from `~/.config/media-dashboard/env`.

1.  Create the configuration directory:
    ```bash
    mkdir -p ~/.config/media-dashboard
    ```

2.  Create the environment file:
    ```bash
    nano ~/.config/media-dashboard/env
    ```

3.  Paste the following configuration and update with your details:

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
    ```

## Starting the Service

Enable and start the user service:

```bash
systemctl --user enable --now media-dashboard
```

Check the status:

```bash
systemctl --user status media-dashboard
```

Run the logs:
```bash
journalctl --user -u media-dashboard -f
```

## Access

Open your browser and navigate to:
[http://localhost:7152](http://localhost:7152)

## Troubleshooting

-   **Service fails to start:** Check logs (`journalctl --user -u media-dashboard`).
-   **"Qbittorrent URL not configured":** Ensure `~/.config/media-dashboard/env` exists and is populated correctly.
-   **Memory Issues:** This version includes a fix for high-volume Qbittorrent error fetching. If you experience crashes, please report with logs.
