import { useState } from 'react'
import { Dice5, RotateCcw } from 'lucide-react'
import { AvatarRenderer } from './AvatarRenderer'
import type { AvatarConfig } from '../../../data/avatarParts'
import {
    AVATAR_PART_LABELS,
    OPTIONS_MAP,
    DEFAULT_AVATAR,
    generateRandomAvatar,
} from '../../../data/avatarParts'

interface AvatarCustomizerProps {
    value: AvatarConfig
    onChange: (config: AvatarConfig) => void
    compact?: boolean
}

type PartKey = keyof AvatarConfig

export function AvatarCustomizer({ value, onChange, compact = false }: AvatarCustomizerProps) {
    const [activeTab, setActiveTab] = useState<string>('top')

    const handlePartChange = (key: string, val: string) => {
        onChange({ ...value, [key]: val })
    }

    const handleRandom = () => onChange(generateRandomAvatar())
    const handleReset = () => onChange(DEFAULT_AVATAR)

    const currentOptions = OPTIONS_MAP[activeTab] || []
    const isColorPicker = ['hairColor', 'skinColor', 'clothesColor'].includes(activeTab)

    return (
        <div className={compact ? 'space-y-4' : 'space-y-5'}>
            {/* Top row: Avatar preview + actions */}
            <div className="flex items-center gap-4">
                <AvatarRenderer config={value} size={compact ? 'lg' : 'xl'} bgColor="#1c1c32" />

                <div className="flex flex-col gap-2">
                    <button
                        onClick={handleRandom}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg
                       bg-[var(--dr-bg-hover)] hover:bg-[var(--dr-accent-soft)]
                       text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)]
                       transition-all duration-200 text-[13px]"
                    >
                        <Dice5 className="w-4 h-4" />
                        🎲 랜덤 생성
                    </button>

                    <button
                        onClick={handleReset}
                        className="flex items-center gap-2 px-4 py-1.5 rounded-lg
                       text-[var(--dr-text-dim)] hover:text-[var(--dr-text-secondary)]
                       transition-all duration-200 text-[12px]"
                    >
                        <RotateCcw className="w-3 h-3" />
                        초기화
                    </button>
                </div>
            </div>

            {/* Tabs — horizontal scrollable */}
            <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-thin">
                {AVATAR_PART_LABELS.map((part) => (
                    <button
                        key={part.key}
                        onClick={() => setActiveTab(part.key)}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px]
                transition-all duration-200 flex-shrink-0 whitespace-nowrap
                ${activeTab === part.key
                                ? 'bg-[var(--dr-accent-soft)] text-[var(--dr-text)] font-semibold'
                                : 'text-[var(--dr-text-muted)] hover:bg-[var(--dr-bg-hover)] hover:text-[var(--dr-text-secondary)]'
                            }
              `}
                    >
                        <span className="text-[13px]">{part.icon}</span>
                        <span>{part.label}</span>
                    </button>
                ))}
            </div>

            {/* Option grid */}
            <div className="min-h-[120px]">
                {isColorPicker ? (
                    /* Color swatch grid */
                    <div className={`grid ${compact ? 'grid-cols-4 gap-2' : 'grid-cols-6 gap-2'}`}>
                        {currentOptions.map((opt) => (
                            <button
                                key={opt.value}
                                onClick={() => handlePartChange(activeTab, opt.value)}
                                className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all border-2
                    ${value[activeTab as PartKey] === opt.value
                                        ? 'border-[var(--dr-accent)] bg-[var(--dr-accent-soft)]'
                                        : 'border-transparent bg-[var(--dr-bg-card)] hover:bg-[var(--dr-bg-hover)]'
                                    }`}
                            >
                                <div
                                    className="w-8 h-8 rounded-full border border-white/10"
                                    style={{ backgroundColor: `#${opt.value}` }}
                                />
                                <span className="text-[10px] text-[var(--dr-text-secondary)]">{opt.label}</span>
                            </button>
                        ))}
                    </div>
                ) : (
                    /* Avatar preview grid */
                    <div className={`grid ${compact ? 'grid-cols-4 gap-2' : 'grid-cols-6 sm:grid-cols-8 gap-2'}`}>
                        {currentOptions.map((opt) => {
                            const previewConfig = { ...value, [activeTab]: opt.value }
                            const isSelected = value[activeTab as PartKey] === opt.value
                            return (
                                <button
                                    key={opt.value || '__none'}
                                    onClick={() => handlePartChange(activeTab, opt.value)}
                                    className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all border-2
                      ${isSelected
                                            ? 'border-[var(--dr-accent)] bg-[var(--dr-accent-soft)]'
                                            : 'border-transparent bg-[var(--dr-bg-card)] hover:bg-[var(--dr-bg-hover)]'
                                        }`}
                                >
                                    <AvatarRenderer config={previewConfig} size="sm" bgColor="#1c1c32" />
                                    <span className="text-[10px] text-[var(--dr-text-secondary)] truncate w-full text-center">
                                        {opt.label}
                                    </span>
                                </button>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
