'use client';

import { useState } from 'react';
import { X, Trash2, AlertTriangle } from 'lucide-react';

interface ErrorItem {
    name: string;
    hash: string;
    state: string;
    message: string;
}

interface TorrentErrorModalProps {
    isOpen: boolean;
    onClose: () => void;
    errors: ErrorItem[];
    onDelete: (hash: string, deleteFiles: boolean) => Promise<void>;
}

export function TorrentErrorModal({ isOpen, onClose, errors, onDelete }: TorrentErrorModalProps) {
    const [confirmHash, setConfirmHash] = useState<string | null>(null);
    const [deleteFiles, setDeleteFiles] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    if (!isOpen) return null;

    const handleConfirmDelete = async () => {
        if (!confirmHash) return;
        setIsDeleting(true);
        await onDelete(confirmHash, deleteFiles);
        setIsDeleting(false);
        setConfirmHash(null);
        setDeleteFiles(false);
        // If no more errors, close modal? specific choice left to parent or user
    };

    const selectedError = errors.find((e) => e.hash === confirmHash);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg border border-slate-700 overflow-hidden">

                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-slate-700 bg-slate-800/50">
                    <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                        {confirmHash ? (
                            <>
                                <AlertTriangle className="text-red-400 w-5 h-5" />
                                Confirm Deletion
                            </>
                        ) : (
                            <>
                                <AlertTriangle className="text-yellow-400 w-5 h-5" />
                                Torrent Errors ({errors.length})
                            </>
                        )}
                    </h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-0 max-h-[60vh] overflow-y-auto">
                    {confirmHash && selectedError ? (
                        <div className="p-6 space-y-4">
                            <p className="text-slate-300">
                                Are you sure you want to delete <strong className="text-white">{selectedError.name}</strong>?
                            </p>

                            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-200 text-sm">
                                This action cannot be undone.
                            </div>

                            <label className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors">
                                <input
                                    type="checkbox"
                                    checked={deleteFiles}
                                    onChange={(e) => setDeleteFiles(e.target.checked)}
                                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-red-500 focus:ring-red-500 focus:ring-offset-slate-800"
                                />
                                <span className="text-slate-200 select-none">Also delete files on disk</span>
                            </label>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setConfirmHash(null)}
                                    className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors font-medium"
                                    disabled={isDeleting}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleConfirmDelete}
                                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors font-medium flex justify-center items-center gap-2"
                                    disabled={isDeleting}
                                >
                                    {isDeleting ? 'Deleting...' : 'Delete Forever'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-700/50">
                            {errors.length === 0 ? (
                                <div className="p-8 text-center text-slate-500">
                                    No errors found.
                                </div>
                            ) : (
                                errors.map((err) => (
                                    <div key={err.hash} className="p-4 hover:bg-slate-700/20 transition-colors group">
                                        <div className="flex justify-between items-start gap-3">
                                            <div className="min-w-0 flex-1">
                                                <div className="font-medium text-slate-200 truncate pr-2">{err.name}</div>
                                                <div className="text-xs text-red-400 mt-1">{err.message}</div>
                                                <div className="text-xs text-slate-500 mt-1 uppercase tracking-wider">{err.state}</div>
                                            </div>
                                            <button
                                                onClick={() => setConfirmHash(err.hash)}
                                                className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                                                title="Delete Torrent"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>

                {!confirmHash && (
                    <div className="p-4 bg-slate-800/50 border-t border-slate-700 text-right">
                        <button onClick={onClose} className="text-sm text-slate-400 hover:text-white px-3 py-1">
                            Close
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
