import { Link, useLocation } from 'react-router';
import {
  MessageSquare,
  LayoutDashboard,
  Users,
  CheckSquare,
  FolderOpen,
  Video,
  Megaphone,
  Settings,
  ChevronLeft,
  ChevronRight,
  Hash,
  Circle,
  CalendarDays,
} from 'lucide-react';
import { motion } from 'motion/react';
import { AvatarRenderer } from './avatar/AvatarRenderer';
import { useAvatarStore } from '../hooks/useAvatarStore';
import { useEmployees } from '../hooks/useEmployees';

interface SidebarProps {
  expanded: boolean;
  onToggle: () => void;
}

const menuSections = [
  {
    title: '메인',
    items: [
      { path: '/', label: '대시보드', icon: LayoutDashboard },
      { path: '/messenger', label: '메신저', icon: MessageSquare },
    ],
  },
  {
    title: '업무',
    items: [
      { path: '/tasks', label: '태스크', icon: CheckSquare },
      { path: '/deliverables', label: '결과물', icon: FolderOpen },
      { path: '/meetings', label: '회의실', icon: Video },
    ],
  },
  {
    title: '관리',
    items: [
      { path: '/organization', label: '조직도', icon: Users },
      { path: '/attendance', label: '출근부', icon: CalendarDays },
      { path: '/announcements', label: '공지사항', icon: Megaphone },
      { path: '/system', label: '시스템', icon: Settings },
    ],
  },
];

export function Sidebar({ expanded, onToggle }: SidebarProps) {
  const location = useLocation();
  const { ceoAvatar, ceoName } = useAvatarStore();
  const employees = useEmployees();
  const dmEmployees = employees; // 전체 16명 표시

  return (
    <motion.div
      initial={false}
      animate={{ width: expanded ? 240 : 72 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="relative flex-shrink-0 h-full bg-[var(--dr-bg-elevated)] border-r border-[var(--dr-glass-border)]"
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-[var(--dr-glass-border)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] flex items-center justify-center shadow-[var(--shadow-glow-accent)]">
              <span className="text-white font-bold text-lg">D</span>
            </div>
            {expanded && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                <h1 className="text-[var(--dr-text)] text-[15px] font-semibold">DeepRed</h1>
                <p className="text-[var(--dr-text-dim)] text-[10px]">AI 팀 워크스페이스</p>
              </motion.div>
            )}
          </div>
        </div>

        {/* Menu */}
        <div className="flex-1 overflow-y-auto py-4">
          {menuSections.map((section, idx) => (
            <div key={idx} className="mb-4">
              {expanded && (
                <div className="px-4 mb-2">
                  <span className="text-[var(--dr-text-muted)] text-[10px] uppercase tracking-wider font-medium">
                    {section.title}
                  </span>
                </div>
              )}
              <nav className="space-y-0.5 px-2">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;

                  return (
                    <Link key={item.path} to={item.path}>
                      <div
                        className={`
                          relative flex items-center gap-3 px-3 py-2.5 rounded-lg
                          transition-all duration-200
                          ${isActive
                            ? 'bg-[var(--dr-accent-soft)] text-[var(--dr-text)]'
                            : 'text-[var(--dr-text-secondary)] hover:bg-[var(--dr-bg-hover)] hover:text-[var(--dr-text)]'
                          }
                        `}
                      >
                        {isActive && (
                          <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[var(--dr-accent)] rounded-r-full" />
                        )}
                        <Icon className="w-5 h-5 flex-shrink-0" />
                        {expanded && (
                          <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-[13px] font-medium"
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}

          {/* DM Section */}
          {expanded && (
            <div className="mt-2 mb-4">
              <div className="px-4 mb-2">
                <span className="text-[var(--dr-text-muted)] text-[10px] uppercase tracking-wider font-medium">
                  다이렉트 메시지
                </span>
              </div>
              <nav className="space-y-0.5 px-2 max-h-[320px] overflow-y-auto scrollbar-thin">
                {dmEmployees.map((emp) => (
                  <Link key={emp.id} to={`/messenger?employee=${emp.id}`}>
                    <div className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--dr-text-secondary)] hover:bg-[var(--dr-bg-hover)] hover:text-[var(--dr-text)] transition-all duration-200">
                      <div className="relative">
                        <AvatarRenderer config={emp.avatar} size="xs" bgColor={emp.departmentColor + '33'} />
                        <Circle
                          className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 fill-[var(--dr-success)] text-[var(--dr-bg-elevated)]"
                        />
                      </div>
                      <span className="text-[12px] font-medium truncate">{emp.name}</span>
                      <span className="text-[10px] text-[var(--dr-text-dim)] ml-auto">{emp.role.split(' ')[0]}</span>
                    </div>
                  </Link>
                ))}
              </nav>
            </div>
          )}
        </div>

        {/* User Profile + Toggle */}
        <div className="p-3 border-t border-[var(--dr-glass-border)]">
          {expanded && (
            <Link to="/profile">
              <div className="flex items-center gap-3 px-2 py-2 mb-2 rounded-lg hover:bg-[var(--dr-bg-hover)] transition-all cursor-pointer">
                <AvatarRenderer config={ceoAvatar} size="sm" bgColor="#2a1525" />
                <div className="flex-1 min-w-0">
                  <p className="text-[var(--dr-text)] text-[12px] font-medium truncate">{ceoName}</p>
                  <p className="text-[var(--dr-text-dim)] text-[10px]">CEO · 프로필 설정</p>
                </div>
              </div>
            </Link>
          )}
          <button
            onClick={onToggle}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                     bg-[var(--dr-bg-card)] hover:bg-[var(--dr-bg-hover)]
                     text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)]
                     transition-all duration-200"
          >
            {expanded ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            {expanded && <span className="text-[12px]">접기</span>}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
