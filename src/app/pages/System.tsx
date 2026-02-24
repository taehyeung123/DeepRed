import { useState, useEffect, useCallback } from 'react';
import {
  Server, Database, Zap, CheckCircle, AlertCircle, Clock, Brain, Bell,
  MessageSquare, Search, RefreshCw, Loader2, Play, Wifi, Calendar, Wrench,
} from 'lucide-react';
import { motion } from 'motion/react';

import { API_BASE } from '../lib/api';

interface HealthData {
  status: string;
  employees: number;
  timestamp?: string;
}

interface SchedulerStatus {
  running: boolean;
  available: boolean;
  jobs: { id: string; name: string; description: string; trigger: string }[];
  history: { job: string; status: string; detail: string; executed_at: string }[];
}

interface TelegramStatus {
  available: boolean;
  bot_token_set: boolean;
  chat_id_set: boolean;
  polling_active: boolean;
  inbox_count: number;
}

interface ToolItem {
  name: string;
  description: string;
}

export function System() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [memoryStats, setMemoryStats] = useState<any>(null);
  const [dbStats, setDbStats] = useState<any>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [telegram, setTelegram] = useState<TelegramStatus | null>(null);
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [notifications, setNotifications] = useState<{ total: number; unread: number }>({ total: 0, unread: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [runningJob, setRunningJob] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [hRes, mRes, dRes, sRes, tRes, toolRes, nRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/health`).then(r => r.json()),
        fetch(`${API_BASE}/api/memory/stats`).then(r => r.json()),
        fetch(`${API_BASE}/api/db/stats`).then(r => r.json()),
        fetch(`${API_BASE}/api/scheduler/status`).then(r => r.json()),
        fetch(`${API_BASE}/api/telegram/status`).then(r => r.json()),
        fetch(`${API_BASE}/api/tools`).then(r => r.json()),
        fetch(`${API_BASE}/api/notifications`).then(r => r.json()),
      ]);

      if (hRes.status === 'fulfilled') setHealth(hRes.value);
      if (mRes.status === 'fulfilled') setMemoryStats(mRes.value);
      if (dRes.status === 'fulfilled') setDbStats(dRes.value);
      if (sRes.status === 'fulfilled') setScheduler(sRes.value);
      if (tRes.status === 'fulfilled') setTelegram(tRes.value);
      if (toolRes.status === 'fulfilled') setTools(toolRes.value.tools || []);
      if (nRes.status === 'fulfilled') setNotifications({
        total: nRes.value.notifications?.length || 0,
        unread: nRes.value.unread_count || 0,
      });
    } catch { /* silent */ }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAll();
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/memory/search?q=${encodeURIComponent(searchQuery)}&limit=5`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch { setSearchResults([]); }
  };

  const handleRunJob = async (jobId: string) => {
    setRunningJob(jobId);
    try {
      await fetch(`${API_BASE}/api/scheduler/run/${jobId}`, { method: 'POST' });
      setTimeout(fetchAll, 2000);
    } catch { /* silent */ }
    finally { setRunningJob(null); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--dr-accent)] mx-auto mb-3" />
          <p className="text-[13px] text-[var(--dr-text-muted)]">시스템 상태 로딩...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">시스템 관리</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">서버, 스케줄러, 텔레그램, 도구 실시간 상태</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-3 py-2 rounded-lg bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                   text-[12px] text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)] transition-all
                   flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          새로고침
        </button>
      </div>

      {/* Status Cards Row */}
      <div className="grid grid-cols-4 gap-4">
        <StatusCard
          icon={Server}
          title="API 서버"
          status={health ? 'connected' : 'disconnected'}
          details={health ? `직원 ${health.employees}명 · ok` : '연결 실패'}
          color="var(--dr-success)"
        />
        <StatusCard
          icon={Database}
          title="데이터베이스"
          status={dbStats?.connection !== false ? 'connected' : 'disconnected'}
          details={dbStats ? `${dbStats.total_documents || 0}건 문서 · ${dbStats.total_work_logs || 0}건 로그` : 'N/A'}
          color="var(--dr-info)"
        />
        <StatusCard
          icon={Wifi}
          title="텔레그램 봇"
          status={telegram?.available ? 'connected' : 'disconnected'}
          details={telegram ? `폴링 ${telegram.polling_active ? 'ON' : 'OFF'} · 수신 ${telegram.inbox_count}건` : 'N/A'}
          color="#a78bfa"
        />
        <StatusCard
          icon={Calendar}
          title="스케줄러"
          status={scheduler?.running ? 'connected' : 'disconnected'}
          details={scheduler ? `${scheduler.jobs.length}개 작업 · ${scheduler.running ? '실행 중' : '중지'}` : 'N/A'}
          color="var(--dr-warning)"
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column: Scheduler + Tools */}
        <div className="col-span-2 space-y-6">
          {/* Scheduler Jobs */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-lg bg-[var(--dr-warning)]/15 flex items-center justify-center">
                <Clock className="w-4.5 h-4.5 text-[var(--dr-warning)]" />
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">자동 스케줄러</h2>
                <p className="text-[11px] text-[var(--dr-text-muted)]">
                  {scheduler?.running ? '✅ 스케줄러 활성' : '⚠️ 스케줄러 비활성'}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {scheduler?.jobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]">
                  <div className="flex-1">
                    <p className="text-[13px] font-medium text-[var(--dr-text)]">{job.name}</p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">{job.description}</p>
                  </div>
                  <button
                    onClick={() => handleRunJob(job.id)}
                    disabled={runningJob === job.id}
                    className="px-3 py-1.5 rounded-md bg-[var(--dr-accent)]/10 text-[var(--dr-accent)] text-[11px]
                             hover:bg-[var(--dr-accent)]/20 transition-colors flex items-center gap-1
                             disabled:opacity-50"
                  >
                    {runningJob === job.id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                    즉시 실행
                  </button>
                </div>
              ))}
            </div>

            {/* Recent Job History */}
            {scheduler?.history && scheduler.history.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[var(--dr-glass-border)]">
                <p className="text-[12px] font-medium text-[var(--dr-text-muted)] mb-2">최근 실행 기록</p>
                <div className="space-y-1.5">
                  {scheduler.history.slice(0, 5).map((h, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-[11px]">
                      <span className={h.status === 'success' ? 'text-[var(--dr-success)]' : 'text-[var(--dr-error)]'}>
                        {h.status === 'success' ? '✅' : '❌'}
                      </span>
                      <span className="text-[var(--dr-text-secondary)]">{h.job}</span>
                      <span className="text-[var(--dr-text-muted)] flex-shrink-0">{h.detail?.slice(0, 40)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Available Tools */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-lg bg-[var(--dr-info)]/15 flex items-center justify-center">
                <Wrench className="w-4.5 h-4.5 text-[var(--dr-info)]" />
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">사용 가능한 도구</h2>
                <p className="text-[11px] text-[var(--dr-text-muted)]">{tools.length}개 도구</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {tools.map((tool) => (
                <div key={tool.name} className="p-3 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]">
                  <p className="text-[12px] font-medium text-[var(--dr-text)]">{tool.name}</p>
                  <p className="text-[10px] text-[var(--dr-text-muted)] mt-0.5">{tool.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Memory + Notifications */}
        <div className="space-y-6">
          {/* Memory Stats */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-[var(--dr-accent)]" />
              <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">메모리</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="총 메모리" value={memoryStats?.total_memories?.toString() || '0'} />
              <StatCard label="직원당" value={`${Object.keys(memoryStats?.by_employee || {}).length}명`} />
            </div>

            {/* Memory Search */}
            <div className="mt-4 pt-3 border-t border-[var(--dr-glass-border)]">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="메모리 검색..."
                  className="flex-1 px-3 py-2 rounded-md bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                           text-[11px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                           focus:outline-none focus:border-[var(--dr-accent)]"
                />
                <button onClick={handleSearch} className="px-2 py-2 rounded-md bg-[var(--dr-accent)]/10 text-[var(--dr-accent)]">
                  <Search className="w-3.5 h-3.5" />
                </button>
              </div>
              {searchResults.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  {searchResults.map((r: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-[var(--dr-bg-hover)] text-[10px] text-[var(--dr-text-secondary)]">
                      {r.content?.slice(0, 80) || r.text?.slice(0, 80) || JSON.stringify(r).slice(0, 80)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Notifications */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-[var(--dr-warning)]" />
                <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">알림</h2>
              </div>
              {notifications.unread > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--dr-accent)]/15 text-[var(--dr-accent)]">
                  {notifications.unread}건 미읽
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="전체 알림" value={notifications.total.toString()} />
              <StatCard label="미읽음" value={notifications.unread.toString()} />
            </div>
          </div>

          {/* Telegram Detail */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4 text-[#a78bfa]" />
              <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">텔레그램</h2>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[var(--dr-text-muted)]">봇 토큰</span>
                <span className={telegram?.bot_token_set ? 'text-[var(--dr-success)]' : 'text-[var(--dr-error)]'}>
                  {telegram?.bot_token_set ? '✅ 설정됨' : '❌ 미설정'}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[var(--dr-text-muted)]">Chat ID</span>
                <span className={telegram?.chat_id_set ? 'text-[var(--dr-success)]' : 'text-[var(--dr-error)]'}>
                  {telegram?.chat_id_set ? '✅ 설정됨' : '❌ 미설정'}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[var(--dr-text-muted)]">폴링 상태</span>
                <span className={telegram?.polling_active ? 'text-[var(--dr-success)]' : 'text-[var(--dr-warning)]'}>
                  {telegram?.polling_active ? '🟢 활성' : '🟡 비활성'}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[var(--dr-text-muted)]">수신 메시지</span>
                <span className="text-[var(--dr-text)]">{telegram?.inbox_count || 0}건</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({
  icon: Icon, title, status, details, color,
}: {
  icon: any; title: string; status: 'connected' | 'disconnected'; details: string; color: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-4.5 h-4.5" style={{ color }} />
        </div>
        <div className="flex-1">
          <p className="text-[13px] font-medium text-[var(--dr-text)]">{title}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-[var(--dr-success)]' : 'bg-[var(--dr-error)]'}`} />
        <span className="text-[11px] text-[var(--dr-text-secondary)]">{details}</span>
      </div>
    </motion.div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-[var(--dr-bg-hover)] text-center">
      <p className="text-[16px] font-semibold font-mono text-[var(--dr-text)]">{value}</p>
      <p className="text-[10px] text-[var(--dr-text-muted)] mt-0.5">{label}</p>
    </div>
  );
}
