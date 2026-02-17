'use client';

import { useState } from "react";
import { useSWRConfig } from "swr";
import { useDashboardData } from "@/hooks/useDashboardData";
import { Card } from "@/components/Card";
import { PlexShelf } from "@/components/PlexShelf";
import { CompactDownloadList } from "@/components/CompactDownloadList";
import { TorrentErrorModal } from "@/components/TorrentErrorModal";
import { AlertCircle, ArrowDown, ArrowUp, HardDrive } from "lucide-react";

export default function Dashboard() {
  const { data, isLoading, isError } = useDashboardData();
  const { mutate } = useSWRConfig();
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);

  const handleDeleteTorrent = async (hash: string, deleteFiles: boolean) => {
    try {
      const res = await fetch('/api/delete_torrent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hash, delete_files: deleteFiles }),
      });
      const result = await res.json();
      if (result.success) mutate('/api/data');
      else alert('Failed to delete: ' + (result.error || 'Unknown error'));
    } catch (e) {
      alert('Network error');
    }
  };

  if (isError) return <div className="min-h-screen flex items-center justify-center text-red-500">Failed to load data.</div>;
  if (isLoading || !data) return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading...</div>;

  // QBit Formatting
  const dlSpeed = data.qbittorrent.transfer_info?.dl_info_speed || 0;
  const upSpeed = data.qbittorrent.transfer_info?.up_info_speed || 0;
  const dlSession = data.qbittorrent.transfer_info?.dl_info_data || 0;
  const upSession = data.qbittorrent.transfer_info?.up_info_data || 0;
  const formatSpeed = (bytes: number) => bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB/s` : `${(bytes / 1024).toFixed(1)} KB/s`;
  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="bento-grid bg-slate-950 text-slate-200">

      {/* 1. Header / Status / Arrs (Left Column on Desktop) */}
      <div className="flex flex-col gap-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-baseline justify-between px-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">Media<span className="text-blue-500">Dash</span></h1>
          <span className="text-xs font-mono text-slate-500">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>

        {/* Overseerr Widget */}
        <Card className="shrink-0 bg-indigo-950/20 border-indigo-900/30" noPadding>
          <div className="p-4 flex items-center gap-4">
            <div className="text-3xl font-bold text-indigo-400">{data.overseerr.count || 0}</div>
            <div className="flex-1">
              <div className="text-xs font-bold uppercase tracking-wider text-indigo-300/70">Requests</div>
              <div className="text-xs text-indigo-200/50 truncate">
                {(data.overseerr.requests || []).slice(0, 1).map(r => r.title).join(', ') || 'No pending requests'}
              </div>
            </div>
          </div>
        </Card>

        {/* Sonarr (TV) */}
        <Card title="Sonarr" className="flex-1">
          <div className="space-y-2">
            {(data.sonarr.activity || []).length === 0 && <span className="text-slate-600 text-xs italic">Queue empty</span>}
            {(data.sonarr.activity || []).map((item, i) => (
              <div key={i} className="flex justify-between items-center text-xs bg-slate-900/50 p-2 rounded border border-white/5">
                <span className="truncate flex-1 pr-2">{item.title}</span>
                <span className="text-blue-400 font-mono">{item.status}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Radarr (Movies) */}
        <Card title="Radarr" className="flex-1">
          <div className="space-y-2">
            {(data.radarr.activity || []).length === 0 && <span className="text-slate-600 text-xs italic">Queue empty</span>}
            {(data.radarr.activity || []).map((item, i) => (
              <div key={i} className="flex justify-between items-center text-xs bg-slate-900/50 p-2 rounded border border-white/5">
                <span className="truncate flex-1 pr-2">{item.title}</span>
                <span className="text-amber-400 font-mono">{item.status}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 2. Plex (Center, Main Focus) */}
      <Card className="col-span-1 md:col-span-1 xl:row-span-2 overflow-hidden border-blue-900/20" noPadding>
        {/* Hero: Active Session or Latest Movie */}
        {(data.plex.active_sessions || []).length > 0 ? (
          <PlexShelf title="" items={data.plex.active_sessions} type="session" variant="hero" />
        ) : (
          <div className="p-6 bg-gradient-to-b from-blue-950/20 to-transparent">
            <h2 className="text-2xl font-bold text-white mb-1">Library</h2>
            <p className="text-sm text-slate-400">Nothing playing right now.</p>
          </div>
        )}

        <div className="p-5 space-y-6">
          <PlexShelf title="Recent Movies" items={data.plex.movies || []} type="movie" variant="grid" />
          <PlexShelf title="Recent TV" items={data.plex.shows || []} type="show" variant="grid" />
        </div>
      </Card>

      {/* 3. Downloads (Right Column) */}
      <Card className="flex flex-col border-emerald-900/20" noPadding>
        {/* Speed Header */}
        <div className="p-5 bg-slate-900/50 border-b border-white/5 grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs font-bold uppercase text-emerald-500/70 mb-1 flex items-center gap-1">
              <ArrowDown className="w-3 h-3" /> Down
            </div>
            <div className="text-2xl font-mono text-white">{formatSpeed(dlSpeed)}</div>
            <div className="text-xs text-slate-500 font-mono mt-1">Session: {formatBytes(dlSession)}</div>
          </div>
          <div>
            <div className="text-xs font-bold uppercase text-blue-500/70 mb-1 flex items-center gap-1">
              <ArrowUp className="w-3 h-3" /> Up
            </div>
            <div className="text-2xl font-mono text-white">{formatSpeed(upSpeed)}</div>
            <div className="text-xs text-slate-500 font-mono mt-1">Session: {formatBytes(upSession)}</div>
          </div>
        </div>

        <div className="p-5 flex-1 overflow-auto">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Active Downloads</h3>
            <button
              onClick={() => setIsErrorModalOpen(true)}
              className={`text-xs px-2 py-1 rounded font-bold transition-colors ${(data.qbittorrent.error_count || 0) > 0
                ? "bg-red-500/20 text-red-400 hover:bg-red-500/30 animate-pulse"
                : "bg-slate-800/50 text-slate-500 cursor-default"
                }`}
              disabled={(data.qbittorrent.error_count || 0) === 0}
            >
              {(data.qbittorrent.error_count || 0)} Errors
            </button>
          </div>

          <CompactDownloadList downloads={data.qbittorrent.active_downloads || []} />

          <div className="mt-8">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Recent Activity</h3>
            <CompactDownloadList downloads={(data.qbittorrent.recent || []).slice(0, 5)} emptyMessage="No recent activity" />
          </div>
        </div>
      </Card>

      <TorrentErrorModal
        isOpen={isErrorModalOpen}
        onClose={() => setIsErrorModalOpen(false)}
        errors={data.qbittorrent.errored_torrents || []}
        onDelete={handleDeleteTorrent}
      />
    </div>
  );
}
