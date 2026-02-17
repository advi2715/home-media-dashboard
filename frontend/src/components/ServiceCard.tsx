import { LucideIcon } from 'lucide-react';
import Link from 'next/link';

interface ServiceCardProps {
    title: string;
    url: string;
    status?: 'online' | 'offline' | 'warning' | 'error';
    children: React.ReactNode;
    className?: string; // Allow custom classes like 'col-span-3'
}

export function ServiceCard({ title, url, status = 'online', children, className = '' }: ServiceCardProps) {
    const statusColors = {
        online: 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]',
        offline: 'bg-slate-500',
        warning: 'bg-amber-500',
        error: 'bg-red-500',
    };

    return (
        <div className={`bg-slate-800/70 border border-white/10 backdrop-blur-md rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-200 flex flex-col ${className}`}>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-slate-50">
                    <Link href={url} target="_blank" className="hover:text-blue-400 transition-colors">
                        {title}
                    </Link>
                </h2>
                <span className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
            </div>
            <div className="flex-grow">
                {children}
            </div>
        </div>
    );
}
