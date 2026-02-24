import { useState, useEffect, useCallback } from 'react';
import { motion } from 'motion/react';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';
import { Loader2, RefreshCw } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '';

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

export function Attendance() {
  const employees = useEmployees();
  const [activeTab, setActiveTab] = useState<'current' | 'calendar'>('current');
  const [attendance, setAttendance] = useState<AttendanceEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [serverOnline, setServerOnline] = useState(false);

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

  const fetchAttendance = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/attendance`);
      const data = await res.json();
      setAttendance(data.attendance || []);
      setServerOnline(true);
    } catch {
      setServerOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAttendance(); }, [fetchAttendance]);

  const getDaysOfWeek = () => {
    const days = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() - today.getDay() + i);
      days.push(date);
    }
    return days;
  };

  const daysOfWeek = getDaysOfWeek();

  // Merge attendance data with employee avatar data
  const getEmployeeForAttendance = (entry: AttendanceEntry) => {
    return employees.find(e => e.id === entry.employee_id);
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
          {/* Refresh */}
          <button
            onClick={fetchAttendance}
            className="p-2 rounded-lg hover:bg-[var(--dr-bg-hover)] transition text-[var(--dr-text-muted)]"
            title="새로고침"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Tabs */}
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
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    직원
                  </th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    부서
                  </th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    상태
                  </th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    출근 시간
                  </th>
                  <th className="text-left p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    오늘 태스크
                  </th>
                  <th className="text-right p-4 text-[11px] font-semibold text-[var(--dr-text-muted)] uppercase tracking-wider">
                    기여도
                  </th>
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
                          style={{
                            backgroundColor: `${deptColor}15`,
                            color: deptColor,
                          }}
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
                          <span
                            className="text-[12px] font-medium"
                            style={{ color: statusColors[entry.status] || statusColors.offline }}
                          >
                            {statusLabels[entry.status] || entry.status}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-[12px] font-mono text-[var(--dr-text-secondary)]">
                          {entry.login_time}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="text-[12px] font-mono text-[var(--dr-text)]">
                          {entry.today_tasks}건
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <span
                          className="text-[13px] font-mono font-semibold"
                          style={{ color: deptColor }}
                        >
                          {entry.contribution}pt
                        </span>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="glass-card p-6">
          <div className="grid grid-cols-7 gap-4">
            {daysOfWeek.map((day, idx) => {
              const isToday = day.toDateString() === new Date().toDateString();

              return (
                <div
                  key={idx}
                  className={`glass-card p-4 ${isToday ? 'border-2 border-[var(--dr-accent)]' : ''}`}
                >
                  <div className="text-center mb-4">
                    <p className="text-[11px] text-[var(--dr-text-muted)] mb-1">
                      {day.toLocaleDateString('ko-KR', { weekday: 'short' })}
                    </p>
                    <p
                      className={`text-[16px] font-semibold ${isToday ? 'text-[var(--dr-accent)]' : 'text-[var(--dr-text)]'}`}
                    >
                      {day.getDate()}
                    </p>
                  </div>

                  {/* Activity indicators */}
                  <div className="space-y-1">
                    {attendance.slice(0, 5).map((entry) => (
                      <div
                        key={entry.employee_id}
                        className="h-1.5 rounded-full"
                        style={{
                          backgroundColor: `${DEPT_COLORS[entry.department_key] || '#888'}${isToday ? '40' : '20'}`,
                        }}
                      />
                    ))}
                  </div>

                  {isToday && (
                    <div className="mt-3 text-center">
                      <span className="text-[10px] text-[var(--dr-accent)] font-medium">
                        오늘
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-6 flex items-center gap-4 justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-1.5 rounded-full bg-[var(--dr-success)]" />
              <span className="text-[11px] text-[var(--dr-text-muted)]">높은 활동</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1.5 rounded-full bg-[var(--dr-info)]" />
              <span className="text-[11px] text-[var(--dr-text-muted)]">보통 활동</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1.5 rounded-full bg-[var(--dr-text-muted)]" />
              <span className="text-[11px] text-[var(--dr-text-muted)]">낮은 활동</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
