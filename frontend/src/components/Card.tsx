import { ReactNode } from "react"; // Assuming we might need this later, but for now standard classNames

interface CardProps {
    children: ReactNode;
    className?: string;
    title?: string;
    action?: ReactNode;
    noPadding?: boolean;
}

export function Card({ children, className = "", title, action, noPadding = false }: CardProps) {
    return (
        <div className={`bg-card border border-card-border rounded-2xl overflow-hidden flex flex-col shadow-sm ${className}`}>
            {(title || action) && (
                <div className="px-5 py-4 flex justify-between items-center border-b border-white/5 bg-white/2">
                    {title && <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{title}</h2>}
                    {action && <div>{action}</div>}
                </div>
            )}
            <div className={`flex-1 min-h-0 overflow-auto ${noPadding ? "" : "p-5"}`}>
                {children}
            </div>
        </div>
    );
}
