import useSWR from 'swr';

export interface PlexSession {
    user: string;
    user_thumb: string;
    title: string;
    thumb: string;
    year?: string;
    type?: string;
}

export interface PlexItem {
    title: string;
    year?: string;
    episode?: string;
    thumb: string;
}

export interface PlexData {
    error?: string;
    active_sessions: PlexSession[];
    movies: PlexItem[];
    shows: PlexItem[];
}

export interface QBitTorrent {
    name: string;
    state: string;
    progress: string;
    dlspeed: number;
}

export interface QBitData {
    error?: string;
    active_downloads: QBitTorrent[];
    recent: QBitTorrent[];
    transfer_info?: {
        dl_info_speed: number;
        up_info_speed: number;
        dl_info_data: number;
        up_info_data: number;
    };
    error_count: number;
    errored_torrents: any[];
}

export interface ArrItem {
    title: string;
    status: string;
}

export interface ArrData {
    error?: string;
    activity: ArrItem[];
    errors: any[];
    warnings: any[];
}

export interface OverseerrRequest {
    title: string;
    user: string;
    date: string;
    image: string;
}

export interface OverseerrData {
    error?: string;
    count: number;
    requests: OverseerrRequest[];
}

export interface DashboardData {
    plex: PlexData;
    qbittorrent: QBitData;
    sonarr: ArrData;
    radarr: ArrData;
    overseerr: OverseerrData;
    urls: {
        plex: string;
        qbittorrent: string;
        sonarr: string;
        radarr: string;
        overseerr: string;
    };
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function useDashboardData() {
    const { data, error, isLoading } = useSWR<DashboardData>('/api/data', fetcher, {
        refreshInterval: 2000,
    });

    return {
        data,
        isLoading,
        isError: error,
    };
}
