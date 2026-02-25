/**
 * DeepRed v4.0 — 조직도 & 직원 프로필
 * 탭1: 조직도 트리뷰 (CEO → COO(수진) → 부서장 → 직원)
 * 탭2: 직원 카드 그리드 + 상세 프로필 모달
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { employees as baseEmployees, departments, DEPT_NAME_TO_ID, type Employee } from '../../data/employees';
import {
  Users, Network, X, MessageCircle, Award,
  Briefcase, Clock, ChevronDown, Star, Activity,
  TrendingUp, Target, Send
} from 'lucide-react';
import { AvatarRenderer } from './avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';
import { useNavigate } from 'react-router';

// ─── 부서 컬러 맵 ─────────────────────────
const DEPT_COLORS: Record<string, string> = {
  control: '#DC143C', strategy: '#3b82f6', product: '#ec4899',
  growth: '#22c55e', security_qa: '#f59e0b', analytics: '#6366f1',
  customer: '#a855f7',
};


// ─── 직원 상세 프로필 모달 ─────────────────
function EmployeeProfileModal({ employee, onClose, onDM }: { employee: Employee; onClose: () => void; onDM?: (id: string) => void }) {
  const deptId = DEPT_NAME_TO_ID[employee.department] || '';
  const color = DEPT_COLORS[deptId] || employee.departmentColor || '#6b7280';
  const dept = departments.find(d => d.id === deptId);

  const currentWork = {
    task: `${employee.currentProject || '일반'} 프로젝트 — ${employee.skills[0]} 진행중`,
    startedAt: '오전 9:23',
    progress: employee.progress || Math.floor(Math.random() * 40 + 50),
  };

  const recentDeliverables = [
    { title: employee.recentDeliverables?.[0] || `${employee.skills[0]} 리포트`, type: '보고서', date: '오늘', emoji: '📝' },
    { title: employee.recentDeliverables?.[1] || `${employee.skills[1]} 분석 결과`, type: '분석', date: '어제', emoji: '📊' },
    { title: employee.recentDeliverables?.[2] || `${employee.currentProject} 업데이트`, type: '기획', date: '2일 전', emoji: '📋' },
  ];

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)', zIndex: 200,
        }}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        className="glass-card-strong"
        style={{
          position: 'fixed', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 560, maxHeight: '85vh', overflow: 'auto',
          zIndex: 201, padding: 0,
        }}
      >
        {/* 헤더 */}
        <div style={{
          background: `linear-gradient(135deg, ${color}20, transparent)`,
          padding: '24px 24px 20px', borderBottom: '1px solid var(--dr-border)',
        }}>
          <button
            onClick={onClose}
            className="dr-btn-icon"
            style={{ position: 'absolute', top: 12, right: 12 }}
          >
            <X size={18} />
          </button>
          <div className="flex items-center gap-4">
            <AvatarRenderer config={employee.avatar} size="xl" bgColor={`${color}20`} />
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--dr-text)' }}>
                {employee.name}
              </h2>
              <p style={{ fontSize: 13, color: 'var(--dr-text-secondary)', marginTop: 2 }}>
                {employee.role} · {dept?.name}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className="dr-status-dot dr-status-online" style={{ width: 7, height: 7 }} />
                <span style={{ fontSize: 12, color: 'var(--dr-success)' }}>근무중</span>
                <button
                  onClick={() => onDM?.(employee.id)}
                  className="flex items-center gap-1 ml-3 px-3 py-1 rounded-lg text-white text-[11px] font-medium transition-colors hover:opacity-90"
                  style={{ background: 'var(--dr-accent)' }}
                >
                  <Send size={11} /> DM 보내기
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 성격 */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--dr-border)' }}>
          <p style={{
            fontSize: 13, color: 'var(--dr-text-secondary)',
            lineHeight: 1.6, fontStyle: 'italic',
          }}>
            "{employee.personality}"
          </p>
        </div>

        {/* 현재 작업 */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--dr-border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Target size={14} style={{ color }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--dr-text)', letterSpacing: 0.5 }}>
              현재 작업
            </span>
          </div>
          <div className="glass-card" style={{ padding: '12px 16px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--dr-text)' }}>
              {currentWork.task}
            </div>
            <div className="flex items-center gap-3 mt-2">
              <Clock size={11} style={{ color: 'var(--dr-text-dim)' }} />
              <span style={{ fontSize: 11, color: 'var(--dr-text-muted)' }}>
                {currentWork.startedAt} 시작
              </span>
              <div style={{
                flex: 1, height: 4, borderRadius: 2,
                background: 'var(--dr-bg-hover)',
              }}>
                <div style={{
                  width: `${currentWork.progress}%`, height: '100%',
                  borderRadius: 2, background: color,
                  transition: 'width 1s ease',
                }} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 600, color }}>{currentWork.progress}%</span>
            </div>
          </div>
        </div>

        {/* 성과 지표 */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--dr-border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={14} style={{ color }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--dr-text)', letterSpacing: 0.5 }}>
              성과 지표
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
            {[
              { label: '기여도', value: employee.contribution, icon: '⭐' },
              { label: '정확도', value: `${employee.accuracy}%`, icon: '🎯' },
              { label: '오늘 태스크', value: employee.todayTasks, icon: '📋' },
            ].map(s => (
              <div key={s.label} className="glass-card" style={{ padding: '10px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 18 }}>{s.icon}</div>
                <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--dr-text)', marginTop: 4 }}>
                  {s.value}
                </div>
                <div style={{ fontSize: 10, color: 'var(--dr-text-dim)' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 최근 결과물 */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--dr-border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Briefcase size={14} style={{ color }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--dr-text)', letterSpacing: 0.5 }}>
              최근 결과물
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {recentDeliverables.map((d, i) => (
              <div key={i} className="glass-card flex items-center gap-3" style={{ padding: '10px 14px' }}>
                <span style={{ fontSize: 16 }}>{d.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--dr-text)' }}>{d.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--dr-text-muted)' }}>{d.type} · {d.date}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 스킬 태그 */}
        <div style={{ padding: '16px 24px' }}>
          <div className="flex items-center gap-2 mb-3">
            <Star size={14} style={{ color }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--dr-text)', letterSpacing: 0.5 }}>
              스킬
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {employee.skills.map(skill => (
              <span
                key={skill}
                className="dr-badge"
                style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      </motion.div>
    </>
  );
}

// ─── 직원 카드 ───────────────────────────
function EmployeeCard({ employee, onClick }: { employee: Employee; onClick: () => void }) {
  const deptId = DEPT_NAME_TO_ID[employee.department] || '';
  const color = DEPT_COLORS[deptId] || employee.departmentColor || '#6b7280';

  return (
    <motion.button
      onClick={onClick}
      className="glass-card text-left w-full"
      style={{ padding: '16px', cursor: 'pointer' }}
      whileHover={{ y: -2, borderColor: `${color}40` }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <AvatarRenderer config={employee.avatar} size="lg" bgColor={`${color}15`} />
          <span
            className={`dr-status-dot ${employee.status === 'working' ? 'dr-status-online' : employee.status === 'reporting' ? 'dr-status-busy' : 'dr-status-offline'}`}
            style={{ position: 'absolute', bottom: 0, right: 0, width: 10, height: 10, border: '2px solid var(--dr-bg-card)' }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--dr-text)' }}>{employee.name}</div>
          <div style={{ fontSize: 12, color: 'var(--dr-text-muted)' }}>{employee.role}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color }}>⭐ {employee.contribution}</div>
          <div style={{ fontSize: 10, color: 'var(--dr-text-dim)' }}>기여도</div>
        </div>
      </div>

      {/* 스킬 태그 (2개만) */}
      <div className="flex gap-1.5 mt-3">
        {employee.skills.slice(0, 2).map(s => (
          <span key={s} className="dr-badge" style={{ background: `${color}10`, color, fontSize: 10, padding: '2px 8px' }}>
            {s}
          </span>
        ))}
      </div>
    </motion.button>
  );
}

// ─── 조직도 트리 (CEO → COO 수진 → 부서장) ─────────
function OrgTree() {
  const employees = useEmployees();
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set(departments.map(d => d.id)));

  const toggleDept = (id: string) => {
    setExpandedDepts(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // COO실 제외 부서 (COO 수진은 상위에 표시)
  const deptWithoutControl = departments.filter(d => d.id !== 'control');

  return (
    <div style={{ padding: '32px 24px', overflowX: 'auto' }}>
      {/* CEO 카드 */}
      <div className="flex flex-col items-center mb-2">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card"
          style={{
            padding: '18px 32px', textAlign: 'center',
            borderColor: 'rgba(220,20,60,0.3)',
            boxShadow: '0 0 30px rgba(220,20,60,0.1)',
          }}
        >
          <div style={{ fontSize: 28 }}>👑</div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--dr-text)', marginTop: 4 }}>CEO</div>
          <div style={{ fontSize: 12, color: 'var(--dr-accent)' }}>최고경영자</div>
        </motion.div>

        {/* 수직선 CEO → COO */}
        <div style={{ width: 2, height: 28, background: 'var(--dr-border-light)' }} />

        {/* COO 수진 카드 */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card"
          style={{
            padding: '14px 28px', textAlign: 'center',
            borderColor: 'rgba(220,20,60,0.2)',
            background: 'linear-gradient(135deg, rgba(220,20,60,0.06), transparent)',
          }}
        >
          <div className="flex items-center gap-3 justify-center">
            <div
              className="dr-avatar dr-avatar-md"
              style={{ background: 'rgba(220,20,60,0.15)', borderColor: 'rgba(220,20,60,0.3)' }}
            >
              🎯
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--dr-text)' }}>수진</div>
              <div style={{ fontSize: 12, color: 'var(--dr-accent)' }}>COO · 총괄이사</div>
            </div>
          </div>
          <div style={{ fontSize: 11, color: 'var(--dr-text-muted)', marginTop: 6 }}>
            전 부서 통합 관리 및 전략 수립
          </div>
        </motion.div>

        {/* 수직선 COO → 부서 */}
        <div style={{ width: 2, height: 20, background: 'var(--dr-border-light)' }} />

        {/* 수평선 */}
        <div style={{
          width: Math.min(deptWithoutControl.length * 200, 900),
          height: 2,
          background: 'var(--dr-border-light)',
        }} />
      </div>

      {/* 부서 그리드 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 12,
        marginTop: 4,
      }}>
        {deptWithoutControl.map((dept, i) => {
          const deptEmployees = employees.filter(e => DEPT_NAME_TO_ID[e.department] === dept.id);
          const color = DEPT_COLORS[dept.id] || '#6b7280';
          const isExpanded = expandedDepts.has(dept.id);
          const activeCount = deptEmployees.filter(e => e.status === 'working').length;

          return (
            <motion.div
              key={dept.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.04 }}
              layout
            >
              <button
                onClick={() => toggleDept(dept.id)}
                className="glass-card w-full text-left"
                style={{
                  padding: '14px 16px', cursor: 'pointer',
                  borderColor: isExpanded ? `${color}30` : undefined,
                  background: isExpanded ? `${color}05` : undefined,
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: 18 }}>{dept.icon}</span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--dr-text)' }}>{dept.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--dr-text-muted)' }}>
                        <span style={{ color: 'var(--dr-success)' }}>{activeCount}</span>/{deptEmployees.length}명
                      </div>
                    </div>
                  </div>
                  <motion.div animate={{ rotate: isExpanded ? 180 : 0 }}>
                    <ChevronDown size={14} style={{ color: 'var(--dr-text-dim)' }} />
                  </motion.div>
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{ overflow: 'hidden' }}
                  >
                    {deptEmployees.map(emp => (
                      <div
                        key={emp.id}
                        className="flex items-center gap-3"
                        style={{
                          padding: '8px 16px', marginTop: 2,
                          borderLeft: `2px solid ${color}30`,
                          marginLeft: 20,
                        }}
                      >
                        <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${color}15`} />
                        <div className="flex-1">
                          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--dr-text)' }}>{emp.name}</span>
                          <span style={{ fontSize: 11, color: 'var(--dr-text-muted)', marginLeft: 6 }}>{emp.role}</span>
                        </div>
                        <span
                          className={`dr-status-dot ${emp.status === 'working' ? 'dr-status-online' : emp.status === 'reporting' ? 'dr-status-busy' : 'dr-status-offline'}`}
                          style={{ width: 6, height: 6 }}
                        />
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ─── 메인 컴포넌트 ────────────────────────
export function OrganizationChart() {
  const [tab, setTab] = useState<'tree' | 'profiles'>('tree');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [deptFilter, setDeptFilter] = useState<string>('all');
  const employees = useEmployees();
  const navigate = useNavigate();

  const handleDM = (empId: string) => {
    navigate(`/messenger?employee=${empId}`);
  };

  const filtered = deptFilter === 'all'
    ? employees
    : employees.filter(e => DEPT_NAME_TO_ID[e.department] === deptFilter);

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--dr-bg)' }}>
      {/* 탭 바 */}
      <div
        className="flex items-center gap-1 px-4 flex-shrink-0"
        style={{
          height: 48, borderBottom: '1px solid var(--dr-border)',
          background: 'var(--dr-bg-elevated)',
        }}
      >
        {[
          { id: 'tree' as const, label: '조직도', Icon: Network },
          { id: 'profiles' as const, label: '직원 프로필', Icon: Users },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex items-center gap-2 px-4 py-2 rounded-md transition-all"
            style={{
              fontSize: 13, fontWeight: tab === t.id ? 600 : 400,
              color: tab === t.id ? 'var(--dr-text)' : 'var(--dr-text-muted)',
              background: tab === t.id ? 'var(--dr-accent-soft)' : 'transparent',
              border: 'none', cursor: 'pointer',
            }}
          >
            <t.Icon size={14} />
            {t.label}
          </button>
        ))}

        {/* 부서 필터 (프로필 탭에서만) */}
        {tab === 'profiles' && (
          <select
            value={deptFilter}
            onChange={e => setDeptFilter(e.target.value)}
            className="dr-input ml-auto"
            style={{ width: 160, padding: '6px 10px', fontSize: 12 }}
          >
            <option value="all">전체 부서</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.icon} {d.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-auto">
        {tab === 'tree' ? (
          <OrgTree />
        ) : (
          <div style={{ padding: 24, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
            {filtered.map((emp, i) => (
              <motion.div
                key={emp.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
              >
                <EmployeeCard employee={emp} onClick={() => setSelectedEmployee(emp)} />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* 프로필 모달 */}
      <AnimatePresence>
        {selectedEmployee && (
          <EmployeeProfileModal
            employee={selectedEmployee}
            onClose={() => setSelectedEmployee(null)}
            onDM={handleDM}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
