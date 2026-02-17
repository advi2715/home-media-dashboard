import { ArrowDown, ArrowUp } from 'lucide-react';

interface TransferStatsProps {
    dlSpeed: number;
    upSpeed: number;
    dlSession: number;
    upSession: number;
}

function formatBytes(bytes: number, decimals = 2) {
    if (!+bytes) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function TransferStats({ dlSpeed, upSpeed, dlSession, upSession }: TransferStatsProps) {
    return (
        <div className="grid grid-cols-2 gap-3 mb-6 bg-slate-700/30 p-4 rounded-xl border border-white/5">
            <div className="flex flex-col">
                <span className="text-xs uppercase text-slate-400 tracking-wider mb-1">Down Speed</span>
                <div className="flex items-center text-blue-400 font-mono font-bold text-lg">
                    <ArrowDown size={16} className="mr-1" />
                    {formatBytes(dlSpeed)}/s
                </div>
            </div>

            <div className="flex flex-col">
                <span className="text-xs uppercase text-slate-400 tracking-wider mb-1">Up Speed</span>
                <div className="flex items-center text-purple-400 font-mono font-bold text-lg">
                    <ArrowUp size={16} className="mr-1" />
                    {formatBytes(upSpeed)}/s
                </div>
            </div>

            <div className="flex flex-col">
                <span className="text-xs uppercase text-slate-400 tracking-wider mb-1">Session DL</span>
                <div className="text-slate-200 font-mono text-sm">
                    {formatBytes(dlSession)}
                </div>
            </div>

            <div className="flex flex-col">
                <span className="text-xs uppercase text-slate-400 tracking-wider mb-1">Session UL</span>
                <div className="text-slate-200 font-mono text-sm">
                    {formatBytes(upSession)}
                </div>
            </div>
        </div>
    );
}
