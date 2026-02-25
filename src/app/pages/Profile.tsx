import { useState, useEffect } from 'react'
import { User, Users, Pencil, X, Check, Building2, Settings, BarChart3, MessageSquare, Calendar, Star } from 'lucide-react'
import { AvatarCustomizer } from '../components/avatar/AvatarCustomizer'
import { AvatarRenderer } from '../components/avatar/AvatarRenderer'
import { useAvatarStore } from '../hooks/useAvatarStore'
import { employees } from '../../data/employees'
import { API_BASE } from '../lib/api'
import type { AvatarConfig } from '../../data/avatarParts'

export function Profile() {
    const {
        ceoAvatar, ceoName, setCeoAvatar, setCeoName,
        setEmployeeAvatar, getEmployeeAvatar,
    } = useAvatarStore()

    const [editingCeoName, setEditingCeoName] = useState(false)
    const [nameInput, setNameInput] = useState(ceoName)
    const [editingEmployee, setEditingEmployee] = useState<string | null>(null)
    const [tempAvatar, setTempAvatar] = useState<AvatarConfig | null>(null)

    // Company info
    const [companyName, setCompanyName] = useState(() => localStorage.getItem('dr-company-name') || 'DeepRed Inc.')
    const [companySlogan, setCompanySlogan] = useState(() => localStorage.getItem('dr-company-slogan') || 'AI 직원과 함께하는 차세대 경영')
    const [editingCompany, setEditingCompany] = useState(false)
    const [tempCompanyName, setTempCompanyName] = useState(companyName)
    const [tempCompanySlogan, setTempCompanySlogan] = useState(companySlogan)

    // Stats
    const [stats, setStats] = useState({ totalChats: 0, totalMeetings: 0, topEmployee: '' })

    // Settings
    const [notifications, setNotifications] = useState(() => localStorage.getItem('dr-notifications') !== 'false')

    useEffect(() => {
        // Fetch stats from API
        Promise.all([
            fetch(`${API_BASE}/api/stats/summary`).then(r => r.json()).catch(() => null),
        ]).then(([summary]) => {
            if (summary) {
                setStats({
                    totalChats: summary.total_chats || summary.total_conversations || 0,
                    totalMeetings: summary.total_meetings || 0,
                    topEmployee: summary.most_active_employee || summary.top_contributor || '—',
                })
            }
        })
    }, [])

    const handleSaveName = () => {
        if (nameInput.trim()) {
            setCeoName(nameInput.trim())
        }
        setEditingCeoName(false)
    }

    const handleStartEditEmployee = (empId: string) => {
        setEditingEmployee(empId)
        setTempAvatar(getEmployeeAvatar(empId))
    }

    const handleSaveEmployee = () => {
        if (editingEmployee && tempAvatar) {
            setEmployeeAvatar(editingEmployee, tempAvatar)
        }
        setEditingEmployee(null)
        setTempAvatar(null)
    }

    const handleCancelEmployee = () => {
        setEditingEmployee(null)
        setTempAvatar(null)
    }

    const handleSaveCompany = () => {
        localStorage.setItem('dr-company-name', tempCompanyName)
        localStorage.setItem('dr-company-slogan', tempCompanySlogan)
        setCompanyName(tempCompanyName)
        setCompanySlogan(tempCompanySlogan)
        setEditingCompany(false)
    }

    const toggleNotifications = () => {
        const next = !notifications
        setNotifications(next)
        localStorage.setItem('dr-notifications', String(next))
    }

    const editingEmp = editingEmployee ? employees.find(e => e.id === editingEmployee) : null

    return (
        <div className="space-y-6">
            <h1 className="text-[20px] font-semibold text-[var(--dr-text)]">프로필 설정</h1>

            {/* ─── CEO Stats ─── */}
            <div className="grid grid-cols-3 gap-3">
                <div className="glass-card p-4 text-center">
                    <MessageSquare className="w-5 h-5 mx-auto mb-1 text-[var(--dr-accent)]" />
                    <p className="text-[20px] font-bold text-[var(--dr-text)]">{stats.totalChats}</p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">총 대화</p>
                </div>
                <div className="glass-card p-4 text-center">
                    <Calendar className="w-5 h-5 mx-auto mb-1 text-[var(--dr-info)]" />
                    <p className="text-[20px] font-bold text-[var(--dr-text)]">{stats.totalMeetings}</p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">총 회의</p>
                </div>
                <div className="glass-card p-4 text-center">
                    <Star className="w-5 h-5 mx-auto mb-1 text-[var(--dr-warning)]" />
                    <p className="text-[14px] font-bold text-[var(--dr-text)] truncate">{stats.topEmployee || '—'}</p>
                    <p className="text-[11px] text-[var(--dr-text-muted)]">최다 대화 직원</p>
                </div>
            </div>

            {/* ─── CEO Profile ─── */}
            <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-5">
                    <User className="w-5 h-5 text-[var(--dr-accent)]" />
                    <h2 className="text-[16px] font-semibold text-[var(--dr-text)]">CEO 프로필</h2>
                    <div className="ml-auto flex items-center gap-2">
                        {editingCeoName ? (
                            <div className="flex items-center gap-1.5">
                                <input
                                    value={nameInput}
                                    onChange={e => setNameInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSaveName()}
                                    className="w-28 h-8 px-3 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                             rounded-lg text-[13px] text-[var(--dr-text)]
                             focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30"
                                    autoFocus
                                />
                                <button onClick={handleSaveName}
                                    className="p-1.5 rounded-md bg-[var(--dr-accent)] text-white hover:opacity-90 transition">
                                    <Check className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => { setNameInput(ceoName); setEditingCeoName(true) }}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                           text-[var(--dr-text)] hover:bg-[var(--dr-bg-hover)] transition text-[14px] font-medium"
                            >
                                {ceoName}
                                <Pencil className="w-3.5 h-3.5 text-[var(--dr-text-muted)]" />
                            </button>
                        )}
                    </div>
                </div>

                {/* CEO Avatar Customizer — full width */}
                <AvatarCustomizer value={ceoAvatar} onChange={setCeoAvatar} />
            </div>

            {/* ─── Company Info ─── */}
            <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-4">
                    <Building2 className="w-5 h-5 text-[var(--dr-accent)]" />
                    <h2 className="text-[16px] font-semibold text-[var(--dr-text)]">회사 정보</h2>
                    {!editingCompany && (
                        <button
                            onClick={() => { setTempCompanyName(companyName); setTempCompanySlogan(companySlogan); setEditingCompany(true) }}
                            className="ml-auto p-1.5 rounded-md hover:bg-[var(--dr-bg-hover)] transition text-[var(--dr-text-muted)]"
                        >
                            <Pencil className="w-3.5 h-3.5" />
                        </button>
                    )}
                </div>
                {editingCompany ? (
                    <div className="space-y-3">
                        <div>
                            <label className="text-[11px] text-[var(--dr-text-muted)] mb-1 block">회사명</label>
                            <input
                                value={tempCompanyName}
                                onChange={e => setTempCompanyName(e.target.value)}
                                className="w-full h-9 px-3 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                                         rounded-lg text-[13px] text-[var(--dr-text)]
                                         focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30"
                            />
                        </div>
                        <div>
                            <label className="text-[11px] text-[var(--dr-text-muted)] mb-1 block">슬로건</label>
                            <input
                                value={tempCompanySlogan}
                                onChange={e => setTempCompanySlogan(e.target.value)}
                                className="w-full h-9 px-3 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                                         rounded-lg text-[13px] text-[var(--dr-text)]
                                         focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30"
                            />
                        </div>
                        <div className="flex gap-2 justify-end">
                            <button onClick={() => setEditingCompany(false)}
                                className="px-3 py-1.5 rounded-lg text-[12px] text-[var(--dr-text-muted)] hover:bg-[var(--dr-bg-hover)] transition">
                                취소
                            </button>
                            <button onClick={handleSaveCompany}
                                className="px-4 py-1.5 rounded-lg text-[12px] text-white font-medium bg-[var(--dr-accent)] hover:opacity-90 transition">
                                저장
                            </button>
                        </div>
                    </div>
                ) : (
                    <div>
                        <p className="text-[15px] font-semibold text-[var(--dr-text)]">{companyName}</p>
                        <p className="text-[12px] text-[var(--dr-text-muted)] mt-1">{companySlogan}</p>
                    </div>
                )}
            </div>

            {/* ─── Settings ─── */}
            <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-4">
                    <Settings className="w-5 h-5 text-[var(--dr-accent)]" />
                    <h2 className="text-[16px] font-semibold text-[var(--dr-text)]">환경 설정</h2>
                </div>
                <div className="space-y-3">
                    <div className="flex items-center justify-between py-2">
                        <div>
                            <p className="text-[13px] text-[var(--dr-text)]">알림</p>
                            <p className="text-[11px] text-[var(--dr-text-muted)]">브리핑/회의 알림 수신</p>
                        </div>
                        <button
                            onClick={toggleNotifications}
                            className={`w-10 h-5 rounded-full transition-colors relative ${notifications ? 'bg-[var(--dr-accent)]' : 'bg-[var(--dr-bg-hover)]'}`}
                        >
                            <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${notifications ? 'left-5' : 'left-0.5'}`} />
                        </button>
                    </div>
                    <div className="border-t border-[var(--dr-glass-border)]" />
                    <div className="flex items-center justify-between py-2">
                        <div>
                            <p className="text-[13px] text-[var(--dr-text)]">언어</p>
                            <p className="text-[11px] text-[var(--dr-text-muted)]">인터페이스 언어</p>
                        </div>
                        <span className="text-[12px] px-3 py-1 rounded-lg bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)] text-[var(--dr-text-secondary)]">
                            한국어
                        </span>
                    </div>
                </div>
            </div>

            {/* ─── Employee Avatars ─── */}
            <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-4">
                    <Users className="w-5 h-5 text-[var(--dr-accent)]" />
                    <h2 className="text-[16px] font-semibold text-[var(--dr-text)]">AI 팀원 아바타</h2>
                    <span className="text-[12px] text-[var(--dr-text-muted)]">클릭해서 편집</span>
                </div>

                {/* Employee editing panel */}
                {editingEmp && tempAvatar && (
                    <div className="mb-6 p-5 rounded-xl bg-[var(--dr-bg-elevated)] border border-[var(--dr-glass-border)]">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-[14px] font-semibold text-[var(--dr-text)]">
                                {editingEmp.name} 아바타 편집
                            </h3>
                            <div className="flex gap-2">
                                <button onClick={handleCancelEmployee}
                                    className="px-3 py-1.5 rounded-lg text-[12px] text-[var(--dr-text-muted)]
                           hover:bg-[var(--dr-bg-hover)] transition">
                                    취소
                                </button>
                                <button onClick={handleSaveEmployee}
                                    className="px-4 py-1.5 rounded-lg text-[12px] text-white font-medium
                           bg-[var(--dr-accent)] hover:opacity-90 transition">
                                    저장
                                </button>
                            </div>
                        </div>
                        <AvatarCustomizer value={tempAvatar} onChange={setTempAvatar} compact />
                    </div>
                )}

                {/* Employee grid */}
                <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-3">
                    {employees.map(emp => {
                        const isEditing = editingEmployee === emp.id
                        return (
                            <button
                                key={emp.id}
                                onClick={() => handleStartEditEmployee(emp.id)}
                                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all
                  ${isEditing
                                        ? 'bg-[var(--dr-accent-soft)] ring-2 ring-[var(--dr-accent)]'
                                        : 'hover:bg-[var(--dr-bg-hover)]'
                                    }`}
                            >
                                <AvatarRenderer
                                    config={isEditing && tempAvatar ? tempAvatar : getEmployeeAvatar(emp.id)}
                                    size="md"
                                    bgColor={`${emp.departmentColor}20`}
                                />
                                <span className="text-[11px] font-medium text-[var(--dr-text)] truncate w-full text-center">
                                    {emp.name}
                                </span>
                                <span className="text-[9px] text-[var(--dr-text-dim)] truncate w-full text-center">
                                    {emp.department}
                                </span>
                            </button>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
