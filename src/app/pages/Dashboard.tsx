import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, TrendingDown, Target, CheckCircle, Percent, Users, Brain, AlertTriangle, Lightbulb, Flame, Loader2, RefreshCw, FolderKanban } from 'lucide-react';
import { employees as baseEmployees } from '../../data/employees';
import { motion } from 'motion/react';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';

import { API_BASE } from '../lib/api';

interface BriefingData {
  greeting: string;
  summary: string;
  highlights: { project: string; status: string; metric: string }[];
  issues: { level: string; message: string }[];
  recommendation: string;
  mvp: { name: string; reason: string };
}

interface ActivityItem {
  id: string;
  employee_id?: string;
  employee_name: string;
  action: string;
  type: string;
  icon: string;
  department: string;
  timestamp: string;
}

export function Dashboard() {
  const employees = useEmployees();
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [briefingLoading, setBriefingLoading] = useState(false);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [serverOnline, setServerOnline] = useState(false);

  // ─── 실시간 KPI (from /api/stats/*) ───
  const [liveKPI, setLiveKPI] = useState<any>(null);
  const [liveDepts, setLiveDepts] = useState<any[]>([]);
  const [livePerformers, setLivePerformers] = useState<any[]>([]);
  const [liveProjects, setLiveProjects] = useState<any[]>([]);

  // fallback to static data if API hasn't loaded yet
  const totalContribution = liveKPI?.total_contribution ?? employees.reduce((sum, emp) => sum + emp.contribution, 0);
  const totalTasks = liveKPI?.total_tasks ?? employees.reduce((sum, emp) => sum + emp.todayTasks, 0);
  const avgAccuracy = liveKPI?.accuracy ?? Math.round(employees.reduce((sum, emp) => sum + emp.accuracy, 0) / employees.length);
  const activeEmployees = liveKPI?.active_employees ?? employees.filter(e => e.status === 'working' || e.status === 'meeting').length;
  const totalEmployees = liveKPI?.total_employees ?? 16;
  const trends = liveKPI?.trends ?? { contribution: '+0%', tasks: '+0%', accuracy: '+0%', active: `${activeEmployees}/${totalEmployees}` };

  const topPerformers = livePerformers.length > 0 ? livePerformers : [...employees].sort((a, b) => b.contribution - a.contribution).slice(0, 5);
  const departmentStats = liveDepts.length > 0 ? liveDepts : [];

  // Department color map for activity feed
  const DEPT_COLORS: Record<string, string> = {
    control: '#DC143C', tech: '#3b82f6', design: '#f59e0b',
    marketing: '#22c55e', data: '#6366f1', support: '#a855f7',
    automation: '#06b6d4',
  };

  // Check server & load activity log
  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(res => res.json())
      .then(() => {
        setServerOnline(true);
        // Load activity log
        fetch(`${API_BASE}/api/activity-log?limit=10`)
          .then(r => r.json())
          .then(data => setActivities(data.logs || []))
          .catch(() => { })
          .finally(() => setActivitiesLoading(false));

        // Load live stats
        Promise.allSettled([
          fetch(`${API_BASE}/api/stats/kpi`).then(r => r.json()),
          fetch(`${API_BASE}/api/stats/departments`).then(r => r.json()),
          fetch(`${API_BASE}/api/stats/top-performers?limit=5`).then(r => r.json()),
          fetch(`${API_BASE}/api/stats/projects`).then(r => r.json()),
        ]).then(([kpi, depts, perf, proj]) => {
          if (kpi.status === 'fulfilled') setLiveKPI(kpi.value);
          if (depts.status === 'fulfilled') setLiveDepts(depts.value);
          if (perf.status === 'fulfilled') setLivePerformers(perf.value);
          if (proj.status === 'fulfilled') setLiveProjects(proj.value);
        });
      })
      .catch(() => {
        setServerOnline(false);
        setActivitiesLoading(false);
      });
  }, []);

  // Request new briefing from AI
  const requestBriefing = useCallback(async () => {
    if (briefingLoading) return;
    setBriefingLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/briefing`, { method: 'POST' });
      const data = await res.json();
      setBriefing(data);
    } catch (err) {
      console.error('Briefing error:', err);
    } finally {
      setBriefingLoading(false);
    }
  }, [briefingLoading]);

  // Format relative time
  const getRelativeTime = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '방금 전';
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    return `${Math.floor(hours / 24)}일 전`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">CEO 대시보드</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">전사 KPI와 AI 인사이트</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${serverOnline ? 'bg-[var(--dr-success)]' : 'bg-[var(--dr-error)]'}`} />
          <span className="text-[11px] text-[var(--dr-text-muted)]">
            서버 {serverOnline ? '연결됨' : '오프라인'}
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard icon={Target} label="전체 기여도" value={totalContribution.toLocaleString()} unit="pt" trend={trends.contribution} trendUp={true} color="var(--dr-accent)" />
        <KPICard icon={CheckCircle} label="완료 태스크" value={totalTasks.toString()} unit="건" trend={trends.tasks} trendUp={true} color="var(--dr-success)" />
        <KPICard icon={Percent} label="평균 정확도" value={avgAccuracy.toString()} unit="%" trend={trends.accuracy} trendUp={true} color="var(--dr-info)" />
        <KPICard icon={Users} label="활동 직원" value={activeEmployees.toString()} unit={`/${totalEmployees}`} trend="stable" trendUp={true} color="var(--dr-warning)" />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* AI Briefing */}
        <div className="col-span-2 space-y-6">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">AI 데일리 브리핑</h2>
                  <p className="text-[11px] text-[var(--dr-text-muted)]">
                    {briefing ? '수진(COO) 생성' : '브리핑을 요청하세요'}
                  </p>
                </div>
              </div>
              <button
                onClick={requestBriefing}
                disabled={briefingLoading || !serverOnline}
                className="px-4 py-2 rounded-lg bg-[var(--dr-accent)] text-white text-[12px] font-medium
                         hover:bg-[#b91c3c] transition-colors flex items-center gap-2
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {briefingLoading ? (
                  <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 생성 중...</>
                ) : (
                  <><RefreshCw className="w-3.5 h-3.5" /> 새 브리핑 요청</>
                )}
              </button>
            </div>

            {briefing ? (
              <div className="space-y-5">
                {/* Greeting */}
                <div className="p-3 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]">
                  <p className="text-[13px] text-[var(--dr-text)]">{briefing.greeting}</p>
                  <p className="text-[12px] text-[var(--dr-text-secondary)] mt-1">{briefing.summary}</p>
                </div>

                {/* Highlights */}
                {briefing.highlights?.length > 0 && (
                  <BriefingSection
                    icon={Flame}
                    title="프로젝트 현황"
                    color="var(--dr-accent)"
                    items={briefing.highlights.map(h => `${h.project}: ${h.status} (${h.metric})`)}
                  />
                )}

                {/* Issues */}
                {briefing.issues?.length > 0 && (
                  <BriefingSection
                    icon={AlertTriangle}
                    title="이슈 & 리스크"
                    color="var(--dr-warning)"
                    items={briefing.issues.map(i => `${i.level === 'warning' ? '⚠️' : i.level === 'critical' ? '🔴' : 'ℹ️'} ${i.message}`)}
                  />
                )}

                {/* Recommendation */}
                {briefing.recommendation && (
                  <BriefingSection
                    icon={Lightbulb}
                    title="추천 액션"
                    color="var(--dr-success)"
                    items={[briefing.recommendation]}
                  />
                )}

                {/* MVP */}
                {briefing.mvp && (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-[#f59e0b]/10 to-transparent border border-[#f59e0b]/20">
                    <span className="text-[20px]">🏆</span>
                    <div>
                      <p className="text-[12px] font-semibold text-[#f59e0b]">이번 주 MVP: {briefing.mvp.name}</p>
                      <p className="text-[11px] text-[var(--dr-text-secondary)]">{briefing.mvp.reason}</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Brain className="w-12 h-12 text-[var(--dr-text-muted)] mb-3 opacity-30" />
                <p className="text-[13px] text-[var(--dr-text-muted)]">
                  {serverOnline
                    ? '"새 브리핑 요청" 버튼을 클릭하면 수진(COO)이 AI 브리핑을 생성합니다'
                    : '서버 연결 후 브리핑을 요청할 수 있습니다'}
                </p>
              </div>
            )}
          </div>

          {/* Department Productivity */}
          <div className="glass-card p-6">
            <h2 className="text-[15px] font-semibold text-[var(--dr-text)] mb-4">
              부서별 생산성
            </h2>
            <div className="space-y-3">
              {departmentStats.map((dept) => (
                <div key={dept.name}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[14px]">{dept.emoji}</span>
                      <span className="text-[12px] text-[var(--dr-text)]">{dept.name}</span>
                    </div>
                    <span className="text-[12px] font-mono font-medium" style={{ color: dept.color }}>
                      {dept.productivity}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[var(--dr-bg-hover)] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${dept.productivity}%` }}
                      transition={{ duration: 1, delay: 0.1, ease: 'easeOut' }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: dept.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Project Progress */}
          {liveProjects.length > 0 && (
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-[var(--dr-info)]/10 flex items-center justify-center">
                  <FolderKanban className="w-4 h-4 text-[var(--dr-info)]" />
                </div>
                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">
                  프로젝트 현황
                </h2>
              </div>
              <div className="space-y-4">
                {liveProjects.map((proj: any) => (
                  <div key={proj.name} className="glass-card p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[18px]">{proj.icon}</span>
                        <div>
                          <p className="text-[13px] font-semibold text-[var(--dr-text)]">{proj.name}</p>
                          <p className="text-[10px] text-[var(--dr-text-muted)]">{proj.description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-[var(--dr-success)]/10 text-[var(--dr-success)] font-medium">
                          {proj.status}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-3">
                      <div className="flex-1 h-2 bg-[var(--dr-bg-hover)] rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${proj.progress}%` }}
                          transition={{ duration: 1.2, ease: 'easeOut' }}
                          className="h-full rounded-full bg-gradient-to-r from-[var(--dr-accent)] to-[var(--dr-info)]"
                        />
                      </div>
                      <span className="text-[12px] font-mono font-bold text-[var(--dr-accent)]">{proj.progress}%</span>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-[10px] text-[var(--dr-text-muted)]">
                        배정 인원: {proj.assigned_count}명
                      </span>
                      <span className="text-[10px] text-[var(--dr-text-muted)]">
                        완료 태스크: {proj.total_tasks}건 · 기여도: {proj.total_contribution}pt
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Real-time Activities */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">
                실시간 활동 피드
              </h2>
              {activities.length > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--dr-accent)]/10 text-[var(--dr-accent)]">
                  LIVE
                </span>
              )}
            </div>
            {activitiesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-[var(--dr-text-muted)]" />
              </div>
            ) : activities.length > 0 ? (
              <div className="space-y-3">
                {activities.slice(0, 8).map((activity, idx) => {
                  const color = DEPT_COLORS[activity.department] || '#6b7280';
                  return (
                    <motion.div
                      key={activity.id || idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.08 }}
                      className="flex gap-3"
                    >
                      <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-[14px]"
                        style={{ backgroundColor: `${color}20` }}>
                        {activity.icon || '📌'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] text-[var(--dr-text)]">
                          <span className="font-medium">{activity.employee_name}</span>{' '}
                          {activity.action}
                        </p>
                        <span className="text-[10px] text-[var(--dr-text-muted)]">
                          {getRelativeTime(activity.timestamp)}
                        </span>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <p className="text-[12px] text-[var(--dr-text-muted)] text-center py-6">
                {serverOnline ? '아직 기록된 활동이 없습니다' : '서버 오프라인'}
              </p>
            )}
          </div>

          {/* Top Performers */}
          <div className="glass-card p-5">
            <h2 className="text-[14px] font-semibold text-[var(--dr-text)] mb-4">
              탑 퍼포머
            </h2>
            <div className="space-y-3">
              {topPerformers.map((perf: any, idx: number) => {
                // live API returns {id, name, role, contribution, ...}
                const emp = employees.find(e => e.id === (perf.id || perf.employee_id));
                return (
                  <div key={perf.id || idx} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] flex items-center justify-center text-white text-[11px] font-bold">
                      {idx + 1}
                    </div>
                    {emp ? (
                      <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${emp.departmentColor}20`} />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-[var(--dr-bg-hover)]" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-[var(--dr-text)]">{perf.name}</p>
                      <p className="text-[10px] text-[var(--dr-text-muted)]">{perf.role}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[11px] font-mono font-medium" style={{ color: emp?.departmentColor || 'var(--dr-accent)' }}>
                        {perf.contribution}pt
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({
  icon: Icon, label, value, unit, trend, trendUp, color,
}: {
  icon: any; label: string; value: string; unit: string; trend: string; trendUp: boolean; color: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {trend !== 'stable' && (
          <div className={`flex items-center gap-1 ${trendUp ? 'text-[var(--dr-success)]' : 'text-[var(--dr-error)]'}`}>
            {trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            <span className="text-[11px] font-medium">{trend}</span>
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-[24px] font-semibold font-mono" style={{ color }}>{value}</span>
        <span className="text-[12px] text-[var(--dr-text-muted)]">{unit}</span>
      </div>
      <p className="text-[11px] text-[var(--dr-text-muted)] mt-1">{label}</p>
    </motion.div>
  );
}

function BriefingSection({
  icon: Icon, title, color, items,
}: {
  icon: any; title: string; color: string; items: string[];
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4" style={{ color }} />
        <h3 className="text-[13px] font-semibold" style={{ color }}>{title}</h3>
      </div>
      <ul className="space-y-2 ml-6">
        {items.map((item, idx) => (
          <li key={idx} className="text-[12px] text-[var(--dr-text-secondary)] flex gap-2">
            <span className="text-[var(--dr-text-muted)]">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
