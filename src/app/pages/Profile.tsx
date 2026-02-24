import { useState } from 'react'
import { User, Users, Pencil, X, Check } from 'lucide-react'
import { AvatarCustomizer } from '../components/avatar/AvatarCustomizer'
import { AvatarRenderer } from '../components/avatar/AvatarRenderer'
import { useAvatarStore } from '../hooks/useAvatarStore'
import { employees } from '../../data/employees'
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

    const editingEmp = editingEmployee ? employees.find(e => e.id === editingEmployee) : null

    return (
        <div className="space-y-6">
            <h1 className="text-[20px] font-semibold text-[var(--dr-text)]">프로필 설정</h1>

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
