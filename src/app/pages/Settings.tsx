import { useState, useEffect, useCallback } from 'react';
import {
    Save, Loader2, RefreshCw, FileText, Clock,
    Send, MessageSquare, CheckCircle, AlertCircle,
} from 'lucide-react';
import { motion } from 'motion/react';
import { API_BASE } from '../lib/api';

interface ReportItem {
    label: string;
    description: string;
    enabled: boolean;
    icon: string;
}

interface Settings {
    report_items: Record<string, ReportItem>;
    schedule: {
        morning_hour: number;
        morning_minute: number;
        evening_hour: number;
        evening_minute: number;
    };
    channels: {
        telegram: boolean;
        kakao: boolean;
        web: boolean;
    };
    kakao_status?: {
        available: boolean;
        token_exists: boolean;
    };
}

export function Settings() {
    const [settings, setSettings] = useState<Settings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [dirty, setDirty] = useState(false);

    const fetchSettings = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/report-settings`);
            const data = await res.json();
            setSettings(data);
        } catch { /* silent */ }
        setLoading(false);
    }, []);

    useEffect(() => { fetchSettings(); }, [fetchSettings]);

    const handleToggleItem = (key: string) => {
        if (!settings) return;
        setSettings({
            ...settings,
            report_items: {
                ...settings.report_items,
                [key]: {
                    ...settings.report_items[key],
                    enabled: !settings.report_items[key].enabled,
                },
            },
        });
        setDirty(true);
        setSaved(false);
    };

    const handleToggleChannel = (ch: 'telegram' | 'kakao' | 'web') => {
        if (!settings) return;
        setSettings({
            ...settings,
            channels: { ...settings.channels, [ch]: !settings.channels[ch] },
        });
        setDirty(true);
        setSaved(false);
    };

    const handleScheduleChange = (field: string, value: number) => {
        if (!settings) return;
        setSettings({
            ...settings,
            schedule: { ...settings.schedule, [field]: value },
        });
        setDirty(true);
        setSaved(false);
    };

    const handleSave = async () => {
        if (!settings) return;
        setSaving(true);
        try {
            await fetch(`${API_BASE}/api/report-settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_items: settings.report_items,
                    schedule: settings.schedule,
                    channels: settings.channels,
                }),
            });
            setSaved(true);
            setDirty(false);
            setTimeout(() => setSaved(false), 3000);
        } catch { /* silent */ }
        setSaving(false);
    };

    if (loading || !settings) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--dr-accent)] mx-auto mb-3" />
                    <p className="text-[13px] text-[var(--dr-text-muted)]">설정 로딩...</p>
                </div>
            </div>
        );
    }

    const enabledCount = Object.values(settings.report_items).filter(v => v.enabled).length;
    const totalCount = Object.keys(settings.report_items).length;

    return (
        <div className="space-y-6 max-w-[900px]">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">보고 설정</h1>
                    <p className="text-[13px] text-[var(--dr-text-secondary)]">
                        수진이 아침/저녁 브리핑에 포함할 항목과 알림 채널을 설정합니다
                    </p>
                </div>
                <button
                    onClick={handleSave}
                    disabled={!dirty || saving}
                    className={`px-4 py-2.5 rounded-lg text-[13px] font-medium flex items-center gap-2 transition-all
            ${dirty
                            ? 'bg-[var(--dr-accent)] text-white hover:opacity-90 shadow-[var(--shadow-glow-accent)]'
                            : saved
                                ? 'bg-[var(--dr-success)]/15 text-[var(--dr-success)] border border-[var(--dr-success)]/30'
                                : 'bg-[var(--dr-bg-card)] text-[var(--dr-text-muted)] border border-[var(--dr-glass-border)]'
                        } disabled:opacity-50`}
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> :
                        saved ? <CheckCircle className="w-4 h-4" /> :
                            <Save className="w-4 h-4" />}
                    {saving ? '저장 중...' : saved ? '저장됨' : '저장'}
                </button>
            </div>

            <div className="grid grid-cols-3 gap-6">
                {/* Left: Report Items */}
                <div className="col-span-2 space-y-6">
                    {/* Report Items Card */}
                    <div className="glass-card p-6">
                        <div className="flex items-center gap-3 mb-5">
                            <div className="w-9 h-9 rounded-lg bg-[var(--dr-accent)]/15 flex items-center justify-center">
                                <FileText className="w-4.5 h-4.5 text-[var(--dr-accent)]" />
                            </div>
                            <div className="flex-1">
                                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">보고 항목</h2>
                                <p className="text-[11px] text-[var(--dr-text-muted)]">
                                    {enabledCount}/{totalCount}개 활성
                                </p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            {Object.entries(settings.report_items).map(([key, item]) => (
                                <motion.div
                                    key={key}
                                    layout
                                    className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer
                    ${item.enabled
                                            ? 'bg-[var(--dr-accent-soft)] border-[var(--dr-accent)]/20'
                                            : 'bg-[var(--dr-bg-hover)] border-[var(--dr-glass-border)] opacity-60'
                                        }`}
                                    onClick={() => handleToggleItem(key)}
                                >
                                    <div className="flex items-center gap-3 flex-1">
                                        <span className="text-[20px]">{item.icon}</span>
                                        <div>
                                            <p className="text-[13px] font-medium text-[var(--dr-text)]">{item.label}</p>
                                            <p className="text-[11px] text-[var(--dr-text-muted)]">{item.description}</p>
                                        </div>
                                    </div>
                                    <div
                                        className={`w-11 h-6 rounded-full relative transition-colors duration-200
                      ${item.enabled ? 'bg-[var(--dr-accent)]' : 'bg-[var(--dr-bg-card)]'}`}
                                    >
                                        <div
                                            className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-all duration-200
                        ${item.enabled ? 'left-6' : 'left-1'}`}
                                        />
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Schedule + Channels */}
                <div className="space-y-6">
                    {/* Schedule */}
                    <div className="glass-card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <Clock className="w-4 h-4 text-[var(--dr-warning)]" />
                            <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">보고 시간</h2>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="text-[11px] text-[var(--dr-text-muted)] mb-1.5 block">☀️ 아침 브리핑</label>
                                <div className="flex items-center gap-2">
                                    <select
                                        value={settings.schedule.morning_hour}
                                        onChange={(e) => handleScheduleChange('morning_hour', Number(e.target.value))}
                                        className="flex-1 px-3 py-2 rounded-md bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                             text-[13px] text-[var(--dr-text)] focus:outline-none focus:border-[var(--dr-accent)]"
                                    >
                                        {Array.from({ length: 24 }, (_, i) => (
                                            <option key={i} value={i}>{String(i).padStart(2, '0')}시</option>
                                        ))}
                                    </select>
                                    <select
                                        value={settings.schedule.morning_minute}
                                        onChange={(e) => handleScheduleChange('morning_minute', Number(e.target.value))}
                                        className="w-20 px-3 py-2 rounded-md bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                             text-[13px] text-[var(--dr-text)] focus:outline-none focus:border-[var(--dr-accent)]"
                                    >
                                        {[0, 15, 30, 45].map(m => (
                                            <option key={m} value={m}>{String(m).padStart(2, '0')}분</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="text-[11px] text-[var(--dr-text-muted)] mb-1.5 block">🌙 저녁 보고</label>
                                <div className="flex items-center gap-2">
                                    <select
                                        value={settings.schedule.evening_hour}
                                        onChange={(e) => handleScheduleChange('evening_hour', Number(e.target.value))}
                                        className="flex-1 px-3 py-2 rounded-md bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                             text-[13px] text-[var(--dr-text)] focus:outline-none focus:border-[var(--dr-accent)]"
                                    >
                                        {Array.from({ length: 24 }, (_, i) => (
                                            <option key={i} value={i}>{String(i).padStart(2, '0')}시</option>
                                        ))}
                                    </select>
                                    <select
                                        value={settings.schedule.evening_minute}
                                        onChange={(e) => handleScheduleChange('evening_minute', Number(e.target.value))}
                                        className="w-20 px-3 py-2 rounded-md bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                             text-[13px] text-[var(--dr-text)] focus:outline-none focus:border-[var(--dr-accent)]"
                                    >
                                        {[0, 15, 30, 45].map(m => (
                                            <option key={m} value={m}>{String(m).padStart(2, '0')}분</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Channels */}
                    <div className="glass-card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <Send className="w-4 h-4 text-[var(--dr-info)]" />
                            <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">알림 채널</h2>
                        </div>
                        <div className="space-y-3">
                            {/* Telegram */}
                            <div
                                className="flex items-center justify-between p-3 rounded-lg bg-[var(--dr-bg-hover)] cursor-pointer"
                                onClick={() => handleToggleChannel('telegram')}
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-[16px]">📱</span>
                                    <div>
                                        <p className="text-[12px] font-medium text-[var(--dr-text)]">텔레그램</p>
                                        <p className="text-[10px] text-[var(--dr-text-muted)]">푸시 알림</p>
                                    </div>
                                </div>
                                <div className={`w-9 h-5 rounded-full relative transition-colors ${settings.channels.telegram ? 'bg-[var(--dr-accent)]' : 'bg-[var(--dr-bg-card)]'}`}>
                                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all ${settings.channels.telegram ? 'left-[18px]' : 'left-0.5'}`} />
                                </div>
                            </div>

                            {/* Kakao */}
                            <div
                                className="flex items-center justify-between p-3 rounded-lg bg-[var(--dr-bg-hover)] cursor-pointer"
                                onClick={() => handleToggleChannel('kakao')}
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-[16px]">💬</span>
                                    <div>
                                        <p className="text-[12px] font-medium text-[var(--dr-text)]">카카오톡</p>
                                        <p className="text-[10px] text-[var(--dr-text-muted)]">
                                            {settings.kakao_status?.available ? '✅ 연동됨' : '⚠️ 미연동'}
                                        </p>
                                    </div>
                                </div>
                                <div className={`w-9 h-5 rounded-full relative transition-colors ${settings.channels.kakao ? 'bg-[var(--dr-accent)]' : 'bg-[var(--dr-bg-card)]'}`}>
                                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all ${settings.channels.kakao ? 'left-[18px]' : 'left-0.5'}`} />
                                </div>
                            </div>

                            {/* Web */}
                            <div
                                className="flex items-center justify-between p-3 rounded-lg bg-[var(--dr-bg-hover)] cursor-pointer"
                                onClick={() => handleToggleChannel('web')}
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-[16px]">🖥️</span>
                                    <div>
                                        <p className="text-[12px] font-medium text-[var(--dr-text)]">웹 메신저</p>
                                        <p className="text-[10px] text-[var(--dr-text-muted)]">수진 자율 메시지</p>
                                    </div>
                                </div>
                                <div className={`w-9 h-5 rounded-full relative transition-colors ${settings.channels.web ? 'bg-[var(--dr-accent)]' : 'bg-[var(--dr-bg-card)]'}`}>
                                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all ${settings.channels.web ? 'left-[18px]' : 'left-0.5'}`} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Info */}
                    <div className="glass-card p-4">
                        <p className="text-[11px] text-[var(--dr-text-muted)] leading-relaxed">
                            💡 설정을 저장하면 다음 브리핑부터 반영됩니다.
                            수진이가 Claude AI로 활성화된 항목을 분석하여 보고합니다.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
