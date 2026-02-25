/**
 * DeepRed — 홈 화면
 * 조직도 스타일 오피스 뷰: 각 직원이 데스크에 앉아 노트북 작업 중인 모습
 */
import { useState } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router';
import { employees as baseEmployees, DEPARTMENTS, DEPT_NAME_TO_ID, type Employee } from '../../data/employees';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';
import { useAvatarStore } from '../hooks/useAvatarStore';
import { Monitor, Wifi, WifiOff } from 'lucide-react';

// ─── 부서 컬러 맵 ─────────────────────────
const DEPT_COLORS: Record<string, string> = {
    control: '#DC143C', strategy: '#3b82f6', product: '#ec4899',
    growth: '#22c55e', security_qa: '#f59e0b', analytics: '#6366f1',
    customer: '#a855f7',
};

// ─── 랩톱 SVG 아이콘 ──────────────────────
function LaptopIcon({ color = '#64748b', size = 32 }: { color?: string; size?: number }) {
    return (
        <svg width={size} height={size * 0.7} viewBox="0 0 48 34" fill="none">
            {/* 스크린 */}
            <rect x="6" y="2" width="36" height="22" rx="2" fill={`${color}18`} stroke={`${color}50`} strokeWidth="1.5" />
            {/* 스크린 빛 */}
            <rect x="9" y="5" width="30" height="16" rx="1" fill={`${color}10`} />
            {/* 코드 라인들 */}
            <rect x="12" y="8" width="14" height="1.5" rx="0.75" fill={`${color}35`} />
            <rect x="12" y="12" width="20" height="1.5" rx="0.75" fill={`${color}25`} />
            <rect x="12" y="16" width="10" height="1.5" rx="0.75" fill={`${color}30`} />
            {/* 베이스 */}
            <path d="M2 26 L6 24 L42 24 L46 26 L2 26 Z" fill={`${color}20`} stroke={`${color}35`} strokeWidth="1" />
            {/* 터치패드 */}
            <rect x="20" y="27" width="8" height="4" rx="1" fill={`${color}12`} stroke={`${color}25`} strokeWidth="0.5" />
        </svg>
    );
}

// ─── 데스크 컴포넌트 ──────────────────────
function DeskUnit({
    employee,
    color,
    delay = 0,
    onClick,
}: {
    employee: Employee;
    color: string;
    delay?: number;
    onClick: () => void;
}) {
    const [hovered, setHovered] = useState(false);
    const isOnline = employee.status === 'working' || employee.status === 'meeting';

    return (
        <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.4, ease: 'easeOut' }}
            onClick={onClick}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            className="relative flex flex-col items-center group cursor-pointer"
            style={{ outline: 'none', border: 'none', background: 'none' }}
        >
            {/* 데스크 카드 */}
            <motion.div
                className="relative rounded-2xl p-4 pb-3 flex flex-col items-center gap-1"
                style={{
                    background: hovered ? `${color}12` : `${color}06`,
                    border: `1px solid ${hovered ? `${color}40` : `${color}15`}`,
                    minWidth: 120,
                    transition: 'all 0.25s ease',
                    boxShadow: hovered ? `0 4px 20px ${color}15` : 'none',
                }}
                whileHover={{ y: -3 }}
            >
                {/* 상태 dot */}
                <div
                    className="absolute top-2 right-2 rounded-full"
                    style={{
                        width: 7, height: 7,
                        background: isOnline ? 'var(--dr-success)' : 'var(--dr-text-muted)',
                        boxShadow: isOnline ? '0 0 6px var(--dr-success)' : 'none',
                    }}
                />

                {/* 아바타 */}
                <div className="relative">
                    <AvatarRenderer config={employee.avatar} size="lg" bgColor={`${color}15`} />
                </div>

                {/* 노트북 — 아바타 아래 */}
                <div className="mt-0.5">
                    <LaptopIcon color={color} size={40} />
                </div>

                {/* 이름 + 역할 */}
                <div className="text-center mt-1">
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--dr-text)' }}>
                        {employee.name}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--dr-text-muted)', marginTop: 1 }}>
                        {employee.role}
                    </div>
                </div>

                {/* 호버 시 현재 작업 표시 */}
                {hovered && (
                    <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-1 px-2 py-1 rounded-md text-center"
                        style={{
                            background: `${color}10`,
                            border: `1px solid ${color}20`,
                            maxWidth: 140,
                        }}
                    >
                        <span style={{ fontSize: 10, color: 'var(--dr-text-secondary)', lineHeight: 1.3, display: 'block' }}>
                            {employee.currentTask}
                        </span>
                    </motion.div>
                )}
            </motion.div>
        </motion.button>
    );
}

// ─── 부서 오피스 섹션 ─────────────────────
function DepartmentOffice({
    deptId,
    deptName,
    deptEmoji,
    deptColor,
    employees,
    delay = 0,
    onEmployeeClick,
}: {
    deptId: string;
    deptName: string;
    deptEmoji: string;
    deptColor: string;
    employees: Employee[];
    delay?: number;
    onEmployeeClick: (empId: string) => void;
}) {
    const activeCount = employees.filter(e => e.status === 'working' || e.status === 'meeting').length;

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.5 }}
            className="glass-card overflow-hidden"
            style={{ borderColor: `${deptColor}20` }}
        >
            {/* 부서 헤더 */}
            <div
                className="flex items-center justify-between px-5 py-3"
                style={{
                    background: `linear-gradient(135deg, ${deptColor}12, transparent)`,
                    borderBottom: `1px solid ${deptColor}15`,
                }}
            >
                <div className="flex items-center gap-2.5">
                    <span style={{ fontSize: 20 }}>{deptEmoji}</span>
                    <div>
                        <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--dr-text)' }}>
                            {deptName}
                        </h3>
                        <p style={{ fontSize: 10, color: 'var(--dr-text-muted)' }}>
                            <span style={{ color: 'var(--dr-success)', fontWeight: 600 }}>{activeCount}</span>
                            /{employees.length}명 근무중
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1.5">
                    {activeCount > 0 ? (
                        <Wifi size={13} style={{ color: 'var(--dr-success)' }} />
                    ) : (
                        <WifiOff size={13} style={{ color: 'var(--dr-text-muted)' }} />
                    )}
                </div>
            </div>

            {/* 데스크 그리드 */}
            <div
                className="p-4"
                style={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(auto-fill, minmax(130px, 1fr))`,
                    gap: 12,
                    justifyItems: 'center',
                }}
            >
                {employees.map((emp, i) => (
                    <DeskUnit
                        key={emp.id}
                        employee={emp}
                        color={deptColor}
                        delay={delay + 0.05 * i}
                        onClick={() => onEmployeeClick(emp.id)}
                    />
                ))}
            </div>
        </motion.div>
    );
}

// ─── 메인 홈 컴포넌트 ─────────────────────
export function Home() {
    const employees = useEmployees();
    const { ceoAvatar, ceoName } = useAvatarStore();
    const navigate = useNavigate();

    // CEO + COO(수진)
    const coo = employees.find(e => e.id === 'sujin');

    // 부서별 그룹 (컨트롤 타워 제외 - COO는 상단에 별도 표시)
    const deptEntries = Object.entries(DEPARTMENTS).filter(([id]) => id !== 'control');

    const handleEmployeeClick = (empId: string) => {
        navigate(`/messenger?employee=${empId}`);
    };

    return (
        <div className="space-y-6 pb-8">
            {/* 헤더 */}
            <div>
                <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">
                    🏢 DeepRed 오피스
                </h1>
                <p className="text-[13px] text-[var(--dr-text-secondary)]">
                    AI 팀이 일하고 있는 가상 오피스입니다
                </p>
            </div>

            {/* CEO + COO 오피스 */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="glass-card overflow-hidden"
                style={{
                    borderColor: 'rgba(220,20,60,0.25)',
                    boxShadow: '0 0 40px rgba(220,20,60,0.06)',
                }}
            >
                {/* C-Level 헤더 */}
                <div
                    className="px-5 py-3"
                    style={{
                        background: 'linear-gradient(135deg, rgba(220,20,60,0.08), transparent)',
                        borderBottom: '1px solid rgba(220,20,60,0.12)',
                    }}
                >
                    <div className="flex items-center gap-2.5">
                        <span style={{ fontSize: 20 }}>👑</span>
                        <div>
                            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--dr-text)' }}>
                                경영진 오피스
                            </h3>
                            <p style={{ fontSize: 10, color: 'var(--dr-text-muted)' }}>
                                CEO & COO
                            </p>
                        </div>
                    </div>
                </div>

                {/* CEO + COO 데스크 */}
                <div className="p-6 flex items-start justify-center gap-12 flex-wrap">
                    {/* CEO 데스크 */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.15 }}
                        className="flex flex-col items-center"
                    >
                        <div
                            className="rounded-2xl p-5 pb-3 flex flex-col items-center gap-1.5"
                            style={{
                                background: 'rgba(220,20,60,0.05)',
                                border: '1.5px solid rgba(220,20,60,0.2)',
                                minWidth: 140,
                                boxShadow: '0 4px 24px rgba(220,20,60,0.08)',
                            }}
                        >
                            <div className="absolute -top-2 -right-2" style={{ position: 'relative' }}>
                                <span style={{ fontSize: 22, position: 'absolute', top: -10, right: -8 }}>👑</span>
                            </div>
                            <AvatarRenderer config={ceoAvatar} size="xl" bgColor="rgba(220,20,60,0.1)" />
                            <LaptopIcon color="#DC143C" size={48} />
                            <div className="text-center mt-1">
                                <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--dr-text)' }}>
                                    {ceoName}
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--dr-accent)', fontWeight: 600 }}>
                                    CEO · 최고경영자
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* COO 데스크 */}
                    {coo && (
                        <motion.button
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.25 }}
                            className="flex flex-col items-center cursor-pointer"
                            style={{ outline: 'none', border: 'none', background: 'none' }}
                            onClick={() => handleEmployeeClick(coo.id)}
                        >
                            <div
                                className="rounded-2xl p-5 pb-3 flex flex-col items-center gap-1.5 hover:border-[rgba(220,20,60,0.35)] transition-all"
                                style={{
                                    background: 'rgba(220,20,60,0.04)',
                                    border: '1.5px solid rgba(220,20,60,0.15)',
                                    minWidth: 140,
                                }}
                            >
                                <div className="relative">
                                    <div
                                        className="absolute top-0 right-0 rounded-full"
                                        style={{
                                            width: 8, height: 8,
                                            background: coo.status === 'working' ? 'var(--dr-success)' : 'var(--dr-text-muted)',
                                            boxShadow: coo.status === 'working' ? '0 0 6px var(--dr-success)' : 'none',
                                            transform: 'translate(2px, -2px)',
                                        }}
                                    />
                                    <AvatarRenderer config={coo.avatar} size="xl" bgColor="rgba(220,20,60,0.08)" />
                                </div>
                                <LaptopIcon color="#DC143C" size={48} />
                                <div className="text-center mt-1">
                                    <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--dr-text)' }}>
                                        {coo.name}
                                    </div>
                                    <div style={{ fontSize: 11, color: 'var(--dr-accent)', fontWeight: 600 }}>
                                        COO · 총괄이사
                                    </div>
                                </div>
                            </div>
                        </motion.button>
                    )}
                </div>
            </motion.div>

            {/* 부서별 오피스 */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                {deptEntries.map(([deptId, dept], i) => {
                    const deptEmployees = employees.filter(
                        e => DEPT_NAME_TO_ID[e.department] === deptId
                    );
                    if (deptEmployees.length === 0) return null;

                    return (
                        <DepartmentOffice
                            key={deptId}
                            deptId={deptId}
                            deptName={dept.name}
                            deptEmoji={dept.emoji}
                            deptColor={dept.color}
                            employees={deptEmployees}
                            delay={0.1 + i * 0.08}
                            onEmployeeClick={handleEmployeeClick}
                        />
                    );
                })}
            </div>
        </div>
    );
}
