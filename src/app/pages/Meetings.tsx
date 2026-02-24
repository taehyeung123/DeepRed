import { useState, useCallback } from 'react';
import { Plus, Video, Users, CheckCircle, Loader2, ThumbsUp, ThumbsDown, Minus, FileText, X } from 'lucide-react';
import { employees as baseEmployees } from '../../data/employees';
import { motion, AnimatePresence } from 'motion/react';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface MeetingResponse {
  name: string;
  decision: '찬성' | '반대' | '보류' | '오류';
  reason: string;
}

interface MeetingResult {
  id: string;
  topic: string;
  responses: MeetingResponse[];
  minutes: string;
  timestamp: string;
}

export function Meetings() {
  const employees = useEmployees();
  const [showNewForm, setShowNewForm] = useState(false);
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [meetings, setMeetings] = useState<MeetingResult[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingResult | null>(null);

  const runMeeting = useCallback(async () => {
    if (!topic.trim() || isLoading) return;
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/meeting`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim() }),
      });
      const data = await res.json();

      const meeting: MeetingResult = {
        id: Date.now().toString(),
        topic: topic.trim(),
        responses: data.responses || [],
        minutes: data.minutes || '',
        timestamp: new Date().toISOString(),
      };

      setMeetings(prev => [meeting, ...prev]);
      setSelectedMeeting(meeting);
      setTopic('');
      setShowNewForm(false);
    } catch (err) {
      console.error('Meeting error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [topic, isLoading]);

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case '찬성': return <ThumbsUp className="w-3.5 h-3.5 text-[var(--dr-success)]" />;
      case '반대': return <ThumbsDown className="w-3.5 h-3.5 text-[var(--dr-error)]" />;
      default: return <Minus className="w-3.5 h-3.5 text-[var(--dr-text-muted)]" />;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case '찬성': return 'bg-[var(--dr-success)]/10 text-[var(--dr-success)] border-[var(--dr-success)]/20';
      case '반대': return 'bg-[var(--dr-error)]/10 text-[var(--dr-error)] border-[var(--dr-error)]/20';
      default: return 'bg-[var(--dr-text-muted)]/10 text-[var(--dr-text-muted)] border-[var(--dr-text-muted)]/20';
    }
  };

  const getStats = (responses: MeetingResponse[]) => ({
    yes: responses.filter(r => r.decision === '찬성').length,
    no: responses.filter(r => r.decision === '반대').length,
    hold: responses.filter(r => r.decision !== '찬성' && r.decision !== '반대').length,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">회의실</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">긴급 회의를 소집하고 16명 전원의 의견을 받으세요</p>
        </div>
        <button
          onClick={() => setShowNewForm(true)}
          disabled={isLoading}
          className="px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white
                   text-[13px] font-medium hover:shadow-[var(--shadow-glow-accent)] transition-all duration-300
                   flex items-center gap-2 disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          긴급 회의 소집
        </button>
      </div>

      {/* New Meeting Form */}
      <AnimatePresence>
        {showNewForm && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">🚨 긴급 회의 소집</h2>
              <button onClick={() => setShowNewForm(false)} className="text-[var(--dr-text-muted)] hover:text-[var(--dr-text)]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[12px] text-[var(--dr-text-secondary)] mb-4">
              안건을 입력하면 16명 전원이 각자 성격과 전문 분야에 맞게 의견을 밝힙니다.
            </p>
            <div className="flex gap-3">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && runMeeting()}
                placeholder="예: 댕냥 앱 해외 진출 시기를 앞당겨야 하는가?"
                className="flex-1 px-4 py-3 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                         text-[13px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                         focus:outline-none focus:border-[var(--dr-accent)]"
                disabled={isLoading}
              />
              <button
                onClick={runMeeting}
                disabled={isLoading || !topic.trim()}
                className="px-6 py-3 rounded-lg bg-[var(--dr-accent)] text-white text-[13px] font-medium
                         hover:bg-[#b91c3c] transition-colors flex items-center gap-2
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> 회의 진행 중...</>
                ) : (
                  <><Users className="w-4 h-4" /> 소집</>
                )}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-8 text-center"
        >
          <Loader2 className="w-8 h-8 animate-spin text-[var(--dr-accent)] mx-auto mb-4" />
          <p className="text-[14px] font-medium text-[var(--dr-text)]">16명 전원 회의 진행 중...</p>
          <p className="text-[12px] text-[var(--dr-text-muted)] mt-1">각 직원이 의견을 내고 있습니다. 잠시만 기다려주세요.</p>
          <div className="flex justify-center gap-2 mt-4">
            {employees.slice(0, 8).map(emp => (
              <motion.div
                key={emp.id}
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity, delay: Math.random() }}
              >
                <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${emp.departmentColor}15`} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Meeting List */}
        <div className="col-span-1 space-y-3">
          <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">회의 기록 ({meetings.length})</h2>
          {meetings.length === 0 && !isLoading && (
            <div className="glass-card p-8 text-center">
              <Video className="w-10 h-10 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-30" />
              <p className="text-[12px] text-[var(--dr-text-muted)]">
                아직 진행된 회의가 없습니다.<br />상단의 "긴급 회의 소집"을 클릭하세요.
              </p>
            </div>
          )}
          {meetings.map((m) => {
            const stats = getStats(m.responses);
            const isSelected = selectedMeeting?.id === m.id;
            return (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => setSelectedMeeting(m)}
                className={`glass-card p-4 cursor-pointer transition-all hover:border-[var(--dr-accent)]/40 ${isSelected ? 'border-[var(--dr-accent)]/60 bg-[var(--dr-accent)]/5' : ''
                  }`}
              >
                <h3 className="text-[13px] font-semibold text-[var(--dr-text)] mb-2 line-clamp-2">{m.topic}</h3>
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="text-[var(--dr-success)]">찬성 {stats.yes}</span>
                  <span className="text-[var(--dr-error)]">반대 {stats.no}</span>
                  <span className="text-[var(--dr-text-muted)]">보류 {stats.hold}</span>
                </div>
                <p className="text-[10px] text-[var(--dr-text-muted)] mt-1">
                  {new Date(m.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Meeting Detail */}
        <div className="col-span-2">
          {selectedMeeting ? (
            <div className="space-y-4">
              {/* Topic */}
              <div className="glass-card p-5">
                <h2 className="text-[16px] font-semibold text-[var(--dr-text)] mb-2">
                  🚨 {selectedMeeting.topic}
                </h2>
                <div className="flex items-center gap-4 text-[12px]">
                  {(() => {
                    const stats = getStats(selectedMeeting.responses);
                    return (
                      <>
                        <span className="flex items-center gap-1 text-[var(--dr-success)]">
                          <ThumbsUp className="w-3.5 h-3.5" /> 찬성 {stats.yes}
                        </span>
                        <span className="flex items-center gap-1 text-[var(--dr-error)]">
                          <ThumbsDown className="w-3.5 h-3.5" /> 반대 {stats.no}
                        </span>
                        <span className="flex items-center gap-1 text-[var(--dr-text-muted)]">
                          <Minus className="w-3.5 h-3.5" /> 보류 {stats.hold}
                        </span>
                        <span className="text-[var(--dr-text-muted)]">
                          총 {selectedMeeting.responses.length}명 참석
                        </span>
                      </>
                    );
                  })()}
                </div>
              </div>

              {/* Responses Grid */}
              <div className="grid grid-cols-2 gap-3">
                {selectedMeeting.responses.map((r, idx) => {
                  const emp = employees.find(e => e.name === r.name);
                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.03 }}
                      className="glass-card p-3"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {emp && (
                          <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${emp.departmentColor}15`} />
                        )}
                        <div className="flex-1 min-w-0">
                          <span className="text-[12px] font-medium text-[var(--dr-text)]">{r.name}</span>
                          {emp && <span className="text-[10px] text-[var(--dr-text-muted)] ml-1">{emp.role}</span>}
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border flex items-center gap-1 ${getDecisionColor(r.decision)}`}>
                          {getDecisionIcon(r.decision)} {r.decision}
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--dr-text-secondary)] leading-relaxed">
                        {r.reason}
                      </p>
                    </motion.div>
                  );
                })}
              </div>

              {/* Minutes */}
              {selectedMeeting.minutes && (
                <div className="glass-card p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-4 h-4 text-[var(--dr-accent)]" />
                    <h3 className="text-[14px] font-semibold text-[var(--dr-text)]">수진(COO) 회의록</h3>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]">
                    <pre className="text-[12px] text-[var(--dr-text-secondary)] whitespace-pre-wrap font-sans leading-relaxed">
                      {selectedMeeting.minutes}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <CheckCircle className="w-12 h-12 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-20" />
              <p className="text-[13px] text-[var(--dr-text-muted)]">
                회의를 선택하면 상세 내용을 확인할 수 있습니다
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
