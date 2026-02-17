import { QBitTorrent } from "@/hooks/useDashboardData";

interface CompactDownloadListProps {
    downloads: QBitTorrent[];
    emptyMessage?: string;
}

export function CompactDownloadList({ downloads, emptyMessage = "No active downloads" }: CompactDownloadListProps) {
    if (!downloads || downloads.length === 0) {
        return <div className="text-slate-500 text-sm italic py-2 text-center">{emptyMessage}</div>;
    }

    return (
        <div className="space-y-1">
            {downloads.map((dl, i) => (
                <div key={i} className="group relative bg-slate-800/30 hover:bg-slate-700/40 rounded-lg p-2 transition-colors">
                    {/* Progress Bar Background */}
                    <div
                        className="absolute bottom-0 left-0 h-0.5 bg-blue-500/50 transition-all duration-500"
                        style={{ width: dl.progress }}
                    />

                    <div className="flex justify-between items-center text-sm relative z-10">
                        <div className="flex-1 min-w-0 pr-3">
                            <div className="font-medium text-slate-200 truncate" title={dl.name}>
                                {dl.name}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
                                    {dl.state}
                                </span>
                            </div>
                        </div>

                        <div className="text-right whitespace-nowrap">
                            <div className="font-mono text-blue-400 text-xs font-bold">
                                {dl.dlspeed > 0 ? (dl.dlspeed / 1024 / 1024).toFixed(1) + ' MB/s' : ''}
                            </div>
                            <div className="text-[10px] text-slate-500 mt-0.5">{dl.progress}</div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
