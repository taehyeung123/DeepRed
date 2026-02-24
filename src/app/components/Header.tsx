import { useState, useEffect, useRef } from 'react';
import { Search, Bell, Activity, X, Check, CheckCheck, User, FileText, Megaphone } from 'lucide-react';
import { employees } from '../../data/employees';
import { API_BASE } from '../lib/api';
import { useNavigate } from 'react-router';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  employee_id?: string;
  employee_name?: string;
  read: boolean;
  timestamp: string;
}

interface SearchResult {
  type: string;
  id: string;
  title: string;
  subtitle: string;
  icon: string;
}

export function Header() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [serverOnline, setServerOnline] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const navigate = useNavigate();

  const activeCount = employees.filter(
    (emp) => emp.status === 'working' || emp.status === 'meeting'
  ).length;

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Poll notifications every 10s
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/notifications?limit=20`);
        const data = await res.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
        setServerOnline(true);
      } catch {
        setServerOnline(false);
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, []);

  // Close panel on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setShowPanel(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearch(false);
      }
    };
    if (showPanel || showSearch) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showPanel, showSearch]);

  // Debounced search
  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (!val.trim()) {
      setSearchResults([]);
      setShowSearch(false);
      return;
    }
    searchTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(val)}&limit=8`);
        const data = await res.json();
        setSearchResults(data.results || []);
        setShowSearch(true);
      } catch {
        setSearchResults([]);
      }
    }, 300);
  };

  const handleResultClick = (r: SearchResult) => {
    setShowSearch(false);
    setSearchQuery('');
    if (r.type === 'employee') navigate(`/messenger?employee=${r.id}`);
    else if (r.type === 'announcement') navigate('/announcements');
    else if (r.type === 'document') navigate('/deliverables');
  };

  const RESULT_ICONS: Record<string, typeof User> = { employee: User, announcement: Megaphone, document: FileText };

  const markRead = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/notifications/${id}/read`, { method: 'POST' });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch { /* silent */ }
  };

  const markAllRead = async () => {
    try {
      await fetch(`${API_BASE}/api/notifications/read-all`, { method: 'POST' });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch { /* silent */ }
  };

  const formatTime = (date: Date) =>
    date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const formatDate = (date: Date) =>
    date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });

  const getRelativeTime = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '방금';
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    return `${Math.floor(hours / 24)}일 전`;
  };

  return (
    <header className="h-16 border-b border-[var(--dr-glass-border)] bg-[var(--dr-bg-elevated)] flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="relative" ref={searchRef}>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--dr-text-muted)]" />
          <input
            type="text"
            placeholder="직원, 문서, 공지사항 검색..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowSearch(true)}
            className="w-72 h-9 pl-10 pr-4 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                     rounded-lg text-[13px] text-[var(--dr-text)]
                     placeholder:text-[var(--dr-text-muted)]
                     focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30 focus:border-[var(--dr-accent)]
                     transition-all"
          />
          {showSearch && searchResults.length > 0 && (
            <div className="absolute left-0 top-11 w-80 max-h-80 overflow-y-auto glass-card border border-[var(--dr-glass-border)] rounded-xl shadow-2xl z-50">
              {searchResults.map((r, idx) => {
                const RIcon = RESULT_ICONS[r.type] || FileText;
                return (
                  <button
                    key={`${r.type}-${r.id}-${idx}`}
                    onClick={() => handleResultClick(r)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[var(--dr-bg-hover)] transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded-lg bg-[var(--dr-accent)]/10 flex items-center justify-center flex-shrink-0">
                      <RIcon className="w-4 h-4 text-[var(--dr-accent)]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-[var(--dr-text)] truncate">{r.title}</p>
                      <p className="text-[10px] text-[var(--dr-text-muted)] truncate">{r.subtitle}</p>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--dr-bg-hover)] text-[var(--dr-text-muted)]">
                      {r.type === 'employee' ? '직원' : r.type === 'announcement' ? '공지' : '문서'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Server Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]">
          <Activity className={`w-4 h-4 ${serverOnline ? 'text-[var(--dr-success)]' : 'text-[var(--dr-error)]'}`} />
          <span className="text-[12px] text-[var(--dr-text-secondary)]">
            {serverOnline ? `${activeCount}/16 근무중` : '오프라인'}
          </span>
        </div>

        {/* Notifications */}
        <div className="relative" ref={panelRef}>
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="relative p-2 rounded-lg hover:bg-[var(--dr-bg-hover)] transition-colors"
          >
            <Bell className="w-5 h-5 text-[var(--dr-text-secondary)]" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center
                             bg-[var(--dr-accent)] text-white text-[10px] font-bold rounded-full">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Panel */}
          {showPanel && (
            <div className="absolute right-0 top-12 w-80 max-h-96 overflow-y-auto glass-card border border-[var(--dr-glass-border)] rounded-xl shadow-2xl z-50">
              <div className="flex items-center justify-between p-3 border-b border-[var(--dr-glass-border)]">
                <span className="text-[13px] font-semibold text-[var(--dr-text)]">알림</span>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[10px] text-[var(--dr-accent)] hover:underline flex items-center gap-1"
                    >
                      <CheckCheck className="w-3 h-3" /> 전체 읽음
                    </button>
                  )}
                  <button onClick={() => setShowPanel(false)} className="text-[var(--dr-text-muted)] hover:text-[var(--dr-text)]">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {notifications.length === 0 ? (
                <div className="p-6 text-center">
                  <Bell className="w-8 h-8 text-[var(--dr-text-muted)] mx-auto mb-2 opacity-30" />
                  <p className="text-[12px] text-[var(--dr-text-muted)]">알림이 없습니다</p>
                </div>
              ) : (
                <div className="divide-y divide-[var(--dr-glass-border)]">
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 hover:bg-[var(--dr-bg-hover)] transition-colors cursor-pointer ${!n.read ? 'bg-[var(--dr-accent)]/5' : ''
                        }`}
                      onClick={() => !n.read && markRead(n.id)}
                    >
                      <div className="flex items-start gap-2">
                        {!n.read && <div className="w-2 h-2 rounded-full bg-[var(--dr-accent)] mt-1.5 flex-shrink-0" />}
                        <div className="flex-1 min-w-0">
                          <p className="text-[12px] font-medium text-[var(--dr-text)]">{n.title}</p>
                          <p className="text-[11px] text-[var(--dr-text-secondary)] mt-0.5 line-clamp-2">{n.message}</p>
                          <span className="text-[10px] text-[var(--dr-text-muted)] mt-1 block">
                            {n.employee_name && `${n.employee_name} · `}{getRelativeTime(n.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Time */}
        <div className="flex flex-col items-end">
          <div className="text-[13px] text-[var(--dr-text)] font-mono">{formatTime(currentTime)}</div>
          <div className="text-[10px] text-[var(--dr-text-muted)]">{formatDate(currentTime)}</div>
        </div>
      </div>
    </header>
  );
}
