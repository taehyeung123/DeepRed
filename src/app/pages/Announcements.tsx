import { useState, useEffect, useCallback } from 'react';
import { Plus, Pin, Heart, MessageCircle, Megaphone, Trophy, RefreshCw, FileText, Loader2, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

import { API_BASE } from '../lib/api';

interface Announcement {
  id: string;
  type: 'notice' | 'mvp' | 'update';
  title: string;
  content: string;
  authorName: string;
  timestamp: string;
  likes: number;
  comments: number;
  pinned?: boolean;
}

const typeConfig = {
  notice: { icon: Megaphone, label: '공지', color: 'var(--dr-accent)' },
  mvp: { icon: Trophy, label: 'MVP', color: '#fbbf24' },
  update: { icon: RefreshCw, label: '업데이트', color: 'var(--dr-info)' },
};

export function Announcements() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState<'notice' | 'mvp' | 'update'>('notice');
  const [newPinned, setNewPinned] = useState(false);

  const fetchAnnouncements = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/announcements?limit=30`);
      const data = await res.json();
      setAnnouncements(data.announcements || []);
    } catch (err) {
      console.error('Failed to load announcements:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAnnouncements(); }, [fetchAnnouncements]);

  const handleSubmit = async () => {
    if (!newTitle.trim() || !newContent.trim() || submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/announcements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTitle.trim(),
          content: newContent.trim(),
          type: newType,
          pinned: newPinned,
          author_name: 'CEO',
        }),
      });
      if (res.ok) {
        setNewTitle('');
        setNewContent('');
        setNewType('notice');
        setNewPinned(false);
        setShowForm(false);
        await fetchAnnouncements();
      }
    } catch (err) {
      console.error('Failed to create announcement:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const pinnedAnnouncements = announcements.filter((a) => a.pinned);
  const regularAnnouncements = announcements.filter((a) => !a.pinned);

  const handleLike = async (id: string) => {
    // Optimistic update
    setAnnouncements(prev => prev.map(a => a.id === id ? { ...a, likes: a.likes + 1 } : a));
    try {
      await fetch(`${API_BASE}/api/announcements/${id}/like`, { method: 'POST' });
    } catch {
      // Revert on failure
      setAnnouncements(prev => prev.map(a => a.id === id ? { ...a, likes: a.likes - 1 } : a));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">공지사항</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">사내 공지 및 소식</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white text-[13px] font-medium hover:shadow-[var(--shadow-glow-accent)] transition-all duration-300 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          새 공지 작성
        </button>
      </div>

      {/* Create form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="glass-card p-5 space-y-4 overflow-hidden"
          >
            <h3 className="text-[14px] font-semibold text-[var(--dr-text)]">새 공지 작성</h3>

            {/* Type selector */}
            <div className="flex gap-2">
              {(['notice', 'mvp', 'update'] as const).map(t => {
                const cfg = typeConfig[t];
                return (
                  <button
                    key={t}
                    onClick={() => setNewType(t)}
                    className={`px-3 py-1.5 rounded-lg text-[12px] transition-all ${newType === t
                      ? 'font-semibold ring-2'
                      : 'opacity-50 hover:opacity-80'
                      }`}
                    style={{
                      backgroundColor: `${cfg.color}20`,
                      color: cfg.color,
                      ...(newType === t ? { ringColor: cfg.color } : {}),
                    }}
                  >
                    {cfg.label}
                  </button>
                );
              })}
            </div>

            <input
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              placeholder="공지 제목"
              className="w-full h-10 px-4 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                rounded-lg text-[14px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30"
            />

            <textarea
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
              placeholder="공지 내용을 입력하세요..."
              rows={4}
              className="w-full px-4 py-3 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                rounded-lg text-[13px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30 resize-none"
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-[12px] text-[var(--dr-text-secondary)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={newPinned}
                  onChange={e => setNewPinned(e.target.checked)}
                  className="rounded"
                />
                <Pin className="w-3.5 h-3.5" />
                고정 공지
              </label>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowForm(false)}
                  className="px-3 py-1.5 rounded-lg text-[12px] text-[var(--dr-text-muted)]
                    hover:bg-[var(--dr-bg-hover)] transition"
                >
                  취소
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!newTitle.trim() || !newContent.trim() || submitting}
                  className="px-4 py-1.5 rounded-lg text-[12px] text-white font-medium
                    bg-[var(--dr-accent)] hover:opacity-90 transition disabled:opacity-40
                    flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  등록
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <div className="glass-card p-16 text-center">
          <Loader2 className="w-8 h-8 text-[var(--dr-accent)] mx-auto mb-3 animate-spin" />
          <p className="text-[13px] text-[var(--dr-text-muted)]">공지사항 불러오는 중...</p>
        </div>
      ) : announcements.length === 0 ? (
        /* Empty state */
        <div className="glass-card p-16 text-center">
          <FileText className="w-14 h-14 text-[var(--dr-text-muted)] mx-auto mb-4 opacity-20" />
          <p className="text-[15px] font-medium text-[var(--dr-text-secondary)] mb-2">
            아직 공지사항이 없습니다
          </p>
          <p className="text-[12px] text-[var(--dr-text-muted)]">
            위의 "새 공지 작성" 버튼으로 첫 공지를 등록하세요.
          </p>
        </div>
      ) : (
        <>
          {/* Pinned Announcements */}
          {pinnedAnnouncements.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Pin className="w-4 h-4 text-[var(--dr-accent)]" />
                <h2 className="text-[13px] font-semibold text-[var(--dr-text)] uppercase tracking-wide">
                  고정 공지
                </h2>
              </div>
              {pinnedAnnouncements.map((announcement, idx) => (
                <AnnouncementCard key={announcement.id} announcement={announcement} index={idx} onLike={handleLike} />
              ))}
            </div>
          )}

          {/* Regular Announcements */}
          <div className="space-y-3">
            {regularAnnouncements.map((announcement, idx) => (
              <AnnouncementCard key={announcement.id} announcement={announcement} index={idx} onLike={handleLike} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function AnnouncementCard({
  announcement,
  index,
  onLike,
}: {
  announcement: Announcement;
  index: number;
  onLike?: (id: string) => void;
}) {
  const config = typeConfig[announcement.type] || typeConfig.notice;
  const Icon = config.icon;

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      const diff = Date.now() - d.getTime();
      const mins = Math.floor(diff / 60000);
      if (mins < 1) return '방금 전';
      if (mins < 60) return `${mins}분 전`;
      const hours = Math.floor(mins / 60);
      if (hours < 24) return `${hours}시간 전`;
      return `${Math.floor(hours / 24)}일 전`;
    } catch {
      return ts;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="glass-card p-5 hover:border-[var(--dr-glass-border)]/60 transition-all"
    >
      <div className="flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: `${config.color}20` }}
        >
          <Icon className="w-6 h-6" style={{ color: config.color }} />
        </div>

        <div className="flex-1">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-bold px-2 py-1 rounded-full"
                style={{ backgroundColor: `${config.color}20`, color: config.color }}
              >
                {config.label}
              </span>
              {announcement.pinned && (
                <Pin className="w-3.5 h-3.5 text-[var(--dr-accent)] fill-[var(--dr-accent)]" />
              )}
            </div>
          </div>

          <h3 className="text-[15px] font-semibold text-[var(--dr-text)] mb-2">
            {announcement.title}
          </h3>

          <p className="text-[13px] text-[var(--dr-text-secondary)] leading-relaxed mb-4 whitespace-pre-wrap">
            {announcement.content}
          </p>

          <div className="flex items-center justify-between pt-3 border-t border-[var(--dr-glass-border)]">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full bg-[var(--dr-accent)]/15 flex items-center justify-center text-[10px]">
                👤
              </div>
              <div>
                <p className="text-[12px] font-medium text-[var(--dr-text)]">
                  {announcement.authorName}
                </p>
                <p className="text-[10px] text-[var(--dr-text-muted)]">
                  {formatTime(announcement.timestamp)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={() => onLike?.(announcement.id)}
                className="flex items-center gap-1.5 text-[var(--dr-text-muted)] hover:text-[var(--dr-accent)] transition-colors"
              >
                <Heart className="w-4 h-4" />
                <span className="text-[12px]">{announcement.likes}</span>
              </button>
              <button className="flex items-center gap-1.5 text-[var(--dr-text-muted)] hover:text-[var(--dr-info)] transition-colors">
                <MessageCircle className="w-4 h-4" />
                <span className="text-[12px]">{announcement.comments}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
