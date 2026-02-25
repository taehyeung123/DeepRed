import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';
import { Loader2, RefreshCw, ChevronDown, Users, Zap, CheckCircle, BarChart3, TrendingUp } from 'lucide-react';
import { API_BASE } from '../lib/api';

interface AttendanceEntry {
  employee_id: string;
  name: string;
  role: string;
  department: string;
  department_key: string;
  status: 'working' | 'reporting' | 'meeting' | 'offline';
  login_time: string;
  today_tasks: number;
  contribution: number;
}

interface DayHistory {
  date: string;
  weekday: string;
  is_today: boolean;
  summary: {
    total_contribution: number;
    total_tasks: number;
    active_employees: number;
    total_employees: number;
  };
  employees: {
    employee_id: string;
    name: string;
    department_key: string;
    contribution: number;
    tasks: number;
    status: string;
  }[];
}

export function Attendance() {
  const employees = useEmployees();
  const [activeTab, setActiveTab] = useState<'current' | 'calendar'>('current');
  const [attendance, setAttendance] = useState<AttendanceEntry[]>([]);
  const [activityHistory, setActivityHistory] = useState<DayHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [serverOnline, setServerOnline] = useState(false);
  const [expandedDay, setExpandedDay] = useState<string | null>(null);

  const statusLabels: Record<string, string> = {
    working: '근무중',
    reporting: '보고중',
    meeting: '회의중',
    offline: '부재',
  };

  const statusColors: Record<string, string> = {
    working: 'var(--dr-success)',
    reporting: 'var(--dr-warning)',
    meeting: 'var(--dr-info)',
    offline: 'var(--dr-text-muted)',
  };

  const DEPT_COLORS: Record<string, string> = {
    control: '#DC143C', planning: '#f97316', security: '#64748b',
    design: '#f59e0b', content: '#8b5cf6', marketing: '#22c55e',
    business: '#0ea5e9', automation: '#06b6d4', data: '#6366f1',
    research: '#ec4899', customer: '#14b8a6',
  };

  const WEEKDAY_KOREAN: Record<string, string> = {
    Mon: '월', Tue: '화', Wed: '수', Thu: '목',
    Fri: '금', Sat: '토', Sun: '일',
  };

  const fetchAttendance = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/attendance`);
      const data = await res.json();
      setAttendance(data.attendance || []);
      setServerOnline(true);

      // Also fetch activity history for calendar tab
      fetch(`${API_BASE}/api/stats/activity-history?days=7`)
        .then(r => r.json())
        .then(hist => setActivityHistory(hist))
        .catch(() => { });
    } catch {
      setServerOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAttendance(); }, [fetchAttendance]);

  const getEmployeeForAttendance = (entry: AttendanceEntry) => {
    return employees.find(e => e.id === entry.employee_id);
  };

  const getEmployeeById = (id: string) => {
    return employees.find(e => e.id === id);
  };

  const getActivityLevel = (contribution: number): 'high' | 'medium' | 'low' | 'none' => {
    if (contribution >= 50) return 'high';
    if (contribution >= 20) return 'medium';
    if (contribution > 0) return 'low';
    return 'none';
  };

  const activityLevelColors = {
    high: 'var(--dr-success)',
    medium: 'var(--dr-info)',
    low: 'var(--dr-warning)',
    none: 'var(--dr-text-muted)',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">출근부</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">AI 직원 출근 및 업무 현황</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAttendance}
            className="p-2 rounded-lg hover:bg-[var(--dr-bg-hover)] transition text-[var(--dr-text-muted)]"
            title="새로고침"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <div className="flex gap-2 p-1 bg-[var(--dr-bg-card)] rounded-lg border border-[var(--dr-glass-border)]">
            <button
              onClick={() => setActiveTab('current')}
              className={`px-4 py-2 rounded-md text-[13px] font-medium transition-all ${activeTab === 'current'
                ? 'bg-[var(--dr-accent)] text-white'
                : 'text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)]'
                }`}
            >
              실시간 현황
            </button>
            <button
              onClick={() => setActiveTab('calendar')}
              className={`px-4 py-2 rounded-md text-[13px] font-medium transition-all ${activeTab === 'calendar'
                ? 'bg-[var(--dr-accent)] text-white'
                : 'text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)]'
                }`}
            >
              주간 캘린더
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-card p-16 text-center">
          <Loader2 className="w-8 h-8 text-[var(--dr-accent)] mx-auto mb-3 animate-spin" />
          <p className="text-[13px] text-[var(--dr-text-muted)]">출근 현황 불러오는 중...</p>
        </div>
      ) : activeTab === 'current' ? (
        <div className="glass-card overflow-hidden">
          {!serverOnline && (
            <div className="px-4 py-2 bg-[var(--dr-warning)]/10 text-[var(--dr-warning)] text-[11px] text-center font-medium">
              ⚠️ 서버 연결 실패 — 캐시 데이터 표시 중
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--dr-glass-border)] bg-[var(--dr-bg-elevated)]">
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">직원</th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">부서</th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">상태</th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">출근 시간</th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">오늘 태스크</th>
                  <th className="text-right p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">기여도</th>
                </tr>
              </thead>
              <tbody>
                {attendance.map((entry, idx) => {
                  const emp = getEmployeeForAttendance(entry);
                  const deptColor = DEPT_COLORS[entry.department_key] || '#888';
                  return (
                    <motion.tr
                      key={entry.employee_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      className="border-b border-[var(--dr-glass-border)] hover:bg-[var(--dr-bg-hover)] transition-colors"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          {emp ? (
                            <AvatarRenderer config={emp.avatar} size="md" bgColor={`${deptColor}20`} />
                          ) : (
                            <div className="w-12 h-12 rounded-full bg-[var(--dr-bg-card)]" />
                          )}
                          <div>
                            <p className="text-[13px] font-medium text-[var(--dr-text)]">{entry.name}</p>
                            <p className="text-[11px] text-[var(--dr-text-muted)]">{entry.role}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium"
                          style={{ backgroundColor: `${deptColor}15`, color: deptColor }}
                        >
                          {entry.department}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-2 h-2 rounded-full status-dot-pulse"
                            style={{ backgroundColor: statusColors[entry.status] || statusColors.offline }}
                          />
                          <span className="text-[12px] font-medium" style={{ color: statusColors[entry.status] || statusColors.offline }}>
                            {statusLabels[entry.status] || entry.status}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-[12px] font-mono text-[var(--dr-text-secondary)]">{entry.login_time}</span>
                      </td>
                      <td className="p-4">
                        <span className="text-[12px] font-mono text-[var(--dr-text)]">{entry.today_tasks}건</span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="text-[13px] font-mono font-semibold" style={{ color: deptColor }}>{entry.contribution}pt</span>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* ─── 주간 캘린더 탭 ─────────────────── */
        <div className="space-y-4">
          {/* Department summary chart */}
          {(() => {
            const deptMap = new Map<string, { name: string; contribution: number; tasks: number; count: number }>();
            activityHistory.forEach(day => day.employees.forEach(e => {
              const prev = deptMap.get(e.department_key) || { name: e.department_key, contribution: 0, tasks: 0, count: 0 };
              deptMap.set(e.department_key, { name: prev.name, contribution: prev.contribution + e.contribution, tasks: prev.tasks + e.tasks, count: prev.count + 1 });
            }));
            const depts = [...deptMap.entries()].sort((a, b) => b[1].contribution - a[1].contribution);
            const maxContrib = Math.max(...depts.map(d => d[1].contribution), 1);
            const totalContrib = activityHistory.reduce((s, d) => s + d.summary.total_contribution, 0);
            const totalTasks = activityHistory.reduce((s, d) => s + d.summary.total_tasks, 0);
            const avgActive = Math.round(activityHistory.reduce((s, d) => s + d.summary.active_employees, 0) / Math.max(activityHistory.length, 1));

            return (
              <>
                {/* Stats summary cards */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="glass-card p-4 text-center">
                    <TrendingUp className="w-5 h-5 mx-auto mb-1 text-[var(--dr-accent)]" />
                    <p className="text-[20px] font-bold text-[var(--dr-text)]">{totalContrib}<span className="text-[12px] font-normal text-[var(--dr-text-muted)]">pt</span></p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">주간 총 기여도</p>
                  </div>
                  <div className="glass-card p-4 text-center">
                    <CheckCircle className="w-5 h-5 mx-auto mb-1 text-[var(--dr-success)]" />
                    <p className="text-[20px] font-bold text-[var(--dr-text)]">{totalTasks}<span className="text-[12px] font-normal text-[var(--dr-text-muted)]">건</span></p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">주간 총 태스크</p>
                  </div>
                  <div className="glass-card p-4 text-center">
                    <Users className="w-5 h-5 mx-auto mb-1 text-[var(--dr-info)]" />
                    <p className="text-[20px] font-bold text-[var(--dr-text)]">{avgActive}<span className="text-[12px] font-normal text-[var(--dr-text-muted)]">명</span></p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">평균 참여 인원</p>
                  </div>
                </div>

                {/* Dept bar chart */}
                {depts.length > 0 && (
                  <div className="glass-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <BarChart3 className="w-4 h-4 text-[var(--dr-accent)]" />
                      <h3 className="text-[14px] font-semibold text-[var(--dr-text)]">부서별 주간 기여도</h3>
                    </div>
                    <div className="space-y-2.5">
                      {depts.map(([key, dept]) => {
                        const color = DEPT_COLORS[key] || '#888';
                        const pct = Math.round((dept.contribution / maxContrib) * 100);
                        return (
                          <div key={key} className="flex items-center gap-3">
                            <span className="text-[11px] w-16 text-right text-[var(--dr-text-muted)] truncate">{key}</span>
                            <div className="flex-1 h-4 bg-[var(--dr-bg-hover)] rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${pct}%` }}
                                transition={{ duration: 0.8 }}
                                className="h-full rounded-full"
                                style={{ backgroundColor: color }}
                              />
                            </div>
                            <span className="text-[11px] font-mono w-12 text-right" style={{ color }}>{dept.contribution}pt</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
          <div className="grid grid-cols-3 md:grid-cols-7 gap-3">
            {activityHistory.map((day, idx) => {
              const isExpanded = expandedDay === day.date;
              const avgContrib = day.summary.total_contribution / Math.max(day.summary.total_employees, 1);
              const level = getActivityLevel(avgContrib);
              const activeRatio = day.summary.active_employees / Math.max(day.summary.total_employees, 1);

              return (
                <motion.div
                  key={day.date}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => setExpandedDay(isExpanded ? null : day.date)}
                  className={`glass-card p-4 cursor-pointer transition-all hover:scale-[1.02] ${day.is_today ? 'border-2 border-[var(--dr-accent)] shadow-lg' : ''
                    } ${isExpanded ? 'ring-2 ring-[var(--dr-accent)]/50' : ''}`}
                >
                  <div className="text-center mb-3">
                    <p className="text-[11px] text-[var(--dr-text-muted)]">
                      {WEEKDAY_KOREAN[day.weekday] || day.weekday}
                    </p>
                    <p className={`text-[18px] font-bold ${day.is_today ? 'text-[var(--dr-accent)]' : 'text-[var(--dr-text)]'}`}>
                      {new Date(day.date).getDate()}
                    </p>
                  </div>

                  <div className="w-full h-2 rounded-full bg-[var(--dr-bg-hover)] overflow-hidden mb-3">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.round(activeRatio * 100)}%` }}
                      transition={{ duration: 0.8, delay: idx * 0.05 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: activityLevelColors[level] }}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3 text-[var(--dr-text-muted)]" />
                        <span className="text-[10px] text-[var(--dr-text-muted)]">참여</span>
                      </div>
                      <span className="text-[10px] font-mono font-medium text-[var(--dr-text)]">
                        {day.summary.active_employees}/{day.summary.total_employees}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Zap className="w-3 h-3 text-[var(--dr-text-muted)]" />
                        <span className="text-[10px] text-[var(--dr-text-muted)]">기여</span>
                      </div>
                      <span className="text-[10px] font-mono font-medium text-[var(--dr-text)]">
                        {day.summary.total_contribution}pt
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-[var(--dr-text-muted)]" />
                        <span className="text-[10px] text-[var(--dr-text-muted)]">태스크</span>
                      </div>
                      <span className="text-[10px] font-mono font-medium text-[var(--dr-text)]">
                        {day.summary.total_tasks}건
                      </span>
                    </div>
                  </div>

                  {day.is_today && (
                    <div className="mt-2 text-center">
                      <span className="text-[9px] px-2 py-0.5 rounded-full bg-[var(--dr-accent)] text-white font-semibold">TODAY</span>
                    </div>
                  )}

                  <div className="mt-2 flex justify-center">
                    <ChevronDown className={`w-3 h-3 text-[var(--dr-text-muted)] transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Expanded day detail */}
          <AnimatePresence>
            {expandedDay && (() => {
              const day = activityHistory.find(d => d.date === expandedDay);
              if (!day) return null;
              const sortedEmployees = [...day.employees].sort((a, b) => b.contribution - a.contribution);

              return (
                <motion.div
                  key={expandedDay}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass-card overflow-hidden"
                >
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-[14px] font-semibold text-[var(--dr-text)]">
                        {new Date(day.date).toLocaleDateString('ko-KR', {
                          month: 'long', day: 'numeric', weekday: 'long',
                        })} 활동 상세
                      </h3>
                      <div className="flex items-center gap-3 text-[11px] text-[var(--dr-text-muted)]">
                        <span>참여 {day.summary.active_employees}/{day.summary.total_employees}</span>
                        <span>총 기여 {day.summary.total_contribution}pt</span>
                        <span>태스크 {day.summary.total_tasks}건</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {sortedEmployees.map((empActivity) => {
                        const emp = getEmployeeById(empActivity.employee_id);
                        const deptColor = DEPT_COLORS[empActivity.department_key] || '#888';
                        const maxContribution = Math.max(...sortedEmployees.map(e => e.contribution), 1);
                        const barWidth = (empActivity.contribution / maxContribution) * 100;

                        return (
                          <motion.div
                            key={empActivity.employee_id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-center gap-3 p-2 rounded-lg hover:bg-[var(--dr-bg-hover)] transition-colors"
                          >
                            {emp ? (
                              <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${deptColor}20`} />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-[var(--dr-bg-card)]" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-[11px] font-medium text-[var(--dr-text)] truncate">{empActivity.name}</span>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-[var(--dr-text-muted)]">{empActivity.tasks}건</span>
                                  <span className="text-[10px] font-mono font-semibold" style={{ color: deptColor }}>
                                    {empActivity.contribution}pt
                                  </span>
                                </div>
                              </div>
                              <div className="w-full h-1.5 bg-[var(--dr-bg-hover)] rounded-full overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${barWidth}%` }}
                                  transition={{ duration: 0.6 }}
                                  className="h-full rounded-full"
                                  style={{ backgroundColor: empActivity.contribution > 0 ? deptColor : 'transparent' }}
                                />
                              </div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              );
            })()}
          </AnimatePresence>

          {/* Legend */}
          <div className="flex items-center gap-6 justify-center py-2">
            {Object.entries({ '높은 활동': 'high', '보통 활동': 'medium', '낮은 활동': 'low', '부재': 'none' }).map(([label, level]) => (
              <div key={level} className="flex items-center gap-2">
                <div className="w-4 h-1.5 rounded-full" style={{ backgroundColor: activityLevelColors[level as keyof typeof activityLevelColors] }} />
                <span className="text-[11px] text-[var(--dr-text-muted)]">{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
