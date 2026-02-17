import { PlexSession, PlexItem } from "@/hooks/useDashboardData";

interface PlexShelfProps {
    title: string;
    items: (PlexSession | PlexItem)[];
    type: 'session' | 'movie' | 'show';
    variant?: 'hero' | 'grid' | 'compact';
}

export function PlexShelf({ title, items, type, variant = 'grid' }: PlexShelfProps) {
    if (!items || items.length === 0) return null;

    // Hero Variant (Active Sessions)
    if (variant === 'hero') {
        return (
            <div className="relative w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-hidden group mb-4">
                {items.map((item: any, i) => (
                    <div key={i} className="absolute inset-0">
                        {/* Background Image with Gradient Overlay */}
                        <div
                            className="absolute inset-0 bg-cover bg-center transition-transform duration-1000 group-hover:scale-105"
                            style={{ backgroundImage: `url(${item.thumb})` }}
                        >
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/60 to-transparent" />
                        </div>

                        {/* Content */}
                        <div className="absolute bottom-0 left-0 p-6 w-full">
                            <div className="flex items-center gap-4 mb-2">
                                {item.user_thumb && (
                                    <img src={item.user_thumb} alt={item.user} className="w-8 h-8 rounded-full border border-white/20" />
                                )}
                                <span className="text-blue-400 font-bold tracking-wide uppercase text-xs">Now Playing &bull; {item.user}</span>
                            </div>
                            <h3 className="text-2xl md:text-3xl font-bold text-white mb-1 drop-shadow-md">{item.title}</h3>
                            <p className="text-slate-300 text-sm md:text-base line-clamp-1">{item.year || item.type}</p>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    // Standard Grid Variant (Recently Added)
    return (
        <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">{title}</h3>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
                {items.slice(0, 10).map((item: any, i) => (
                    <div key={i} className="group relative aspect-[2/3] bg-slate-800 rounded-lg overflow-hidden shadow-sm hover:shadow-md hover:ring-2 ring-blue-500/50 transition-all">
                        <div
                            className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                            style={{ backgroundImage: `url(${item.thumb})` }}
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="absolute bottom-0 left-0 p-2 w-full opacity-0 group-hover:opacity-100 transition-opacity">
                            <p className="text-xs font-bold text-white truncate">{item.title}</p>
                            {item.episode && <p className="text-[10px] text-slate-300 truncate">{item.episode}</p>}
                            {item.year && <p className="text-[10px] text-slate-300">{item.year}</p>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
