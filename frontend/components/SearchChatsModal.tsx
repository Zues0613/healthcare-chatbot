'use client';

import { useEffect, useState } from 'react';
import { X, Search as SearchIcon, Clock } from 'lucide-react';
import { apiClient, API_BASE } from '../utils/api';
import { getAuthUser } from '../utils/auth';

interface ChatSession {
  id: string;
  customerId: string;
  createdAt: string;
  updatedAt: string;
  language?: string;
  messageCount: number;
}

interface SearchChatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
}

export default function SearchChatsModal({ isOpen, onClose, onSelectSession }: SearchChatsModalProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const user = getAuthUser();

  useEffect(() => {
    if (isOpen && user) {
      fetchSessions();
    }
  }, [isOpen, user]);

  const fetchSessions = async () => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    try {
      // Get customer_id from current user info
      let customerId: string | null = null;
      
      try {
        // Get current user info to get customer_id
        const userInfoResponse = await apiClient.get(`${API_BASE}/auth/me`);
        customerId = userInfoResponse.data?.id;
      } catch (err: any) {
        console.error('Error getting user info:', err);
        // If /auth/me fails, we can't proceed
        setError('Unable to get user information. Please try again.');
        setSessions([]);
        return;
      }
      
      if (!customerId) {
        setError('Unable to get user information');
        setSessions([]);
        return;
      }
      
      // Fetch sessions for this customer
      const response = await apiClient.get(`${API_BASE}/customer/${customerId}/sessions?limit=100`);
      setSessions(response.data || []);
    } catch (err: any) {
      console.error('Error fetching sessions:', err);
      setError(err.response?.data?.detail || 'Failed to load chat history');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredSessions = sessions.filter((session) => {
    if (!searchTerm.trim()) return true;
    const search = searchTerm.toLowerCase();
    return (
      session.id.toLowerCase().includes(search) ||
      session.language?.toLowerCase().includes(search) ||
      new Date(session.createdAt).toLocaleString().toLowerCase().includes(search)
    );
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-900 shadow-[0_25px_70px_rgba(15,23,42,0.65)] backdrop-blur-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <h2 className="text-xl font-semibold text-white">Search chats</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="border-b border-white/10 px-6 py-4">
          <div className="relative">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by date, language, or session ID..."
              className="w-full rounded-lg border border-white/10 bg-slate-800/50 px-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-400 focus:border-emerald-400/50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              autoFocus
            />
          </div>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-sm text-slate-400">Loading chat history...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-sm text-red-400">{error}</div>
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <SearchIcon className="mb-4 h-12 w-12 text-slate-600" />
              <p className="text-sm text-slate-400">
                {searchTerm ? 'No chats found matching your search' : 'No chat history yet'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredSessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => {
                    onSelectSession(session.id);
                    onClose();
                  }}
                  className="w-full rounded-lg border border-white/10 bg-slate-800/30 px-4 py-3 text-left transition hover:border-emerald-400/30 hover:bg-slate-800/50"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="h-4 w-4 text-slate-400 flex-shrink-0" />
                        <span className="text-xs text-slate-400 truncate">
                          {formatDate(session.createdAt)}
                        </span>
                        {session.language && (
                          <span className="text-xs text-emerald-400/70">
                            • {session.language.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-200 truncate">
                        {session.messageCount} message{session.messageCount !== 1 ? 's' : ''}
                      </p>
                      <p className="text-xs text-slate-500 mt-1 truncate font-mono">
                        {session.id}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

