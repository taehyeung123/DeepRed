import { useState, useCallback } from 'react';
import { Search, Plus, Loader2, Users, ArrowRight, CheckCircle, Lightbulb, X } from 'lucide-react';
import { employees as baseEmployees } from '../../data/employees';
import { motion, AnimatePresence } from 'motion/react';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface CollabStep {
  employee: string;
  department: string;
  action: string;
  result: string;
}

interface CollabResult {
  id: string;
  task: string;
  project?: string;
  coordinator: string;
  coordinator_comment: string;
  steps: CollabStep[];
  summary: string;
  timestamp: string;
}

const PROJECTS = [
  { key: 'dangnyang', label: '댕냥' },
  { key: 'redrank', label: '레드랭크' },
  { key: 'deepred', label: 'DeepRed' },
];

export function Tasks() {
  const employees = useEmployees();
  const [showNewForm, setShowNewForm] = useState(false);
  const [taskInput, setTaskInput] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<CollabResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<CollabResult | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  const submitTask = useCallback(async () => {
    if (!taskInput.trim() || isLoading) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaborate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskInput.trim(),
          project: selectedProject || undefined,
        }),
      });
      const data = await res.json();

      const result: CollabResult = {
        id: Date.now().toString(),
        task: taskInput.trim(),
        project: selectedProject || undefined,
        coordinator: data.coordinator || '수진',
        coordinator_comment: data.coordinator_comment || '',
        steps: data.steps || [],
        summary: data.summary || '',
        timestamp: new Date().toISOString(),
      };

      setResults(prev => [result, ...prev]);
      setSelectedResult(result);
      setTaskInput('');
      setShowNewForm(false);
    } catch (err) {
      console.error('Collaborate error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [taskInput, selectedProject, isLoading]);

  const filteredResults = results.filter(r =>
    !searchFilter || r.task.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">업무 지시</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">
            CEO 지시 → 수진(COO)이 자동 배분 → AI 직원 협업
          </p>
        </div>
        <button
          onClick={() => setShowNewForm(true)}
          disabled={isLoading}
          className="px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white
                   text-[13px] font-medium hover:shadow-[var(--shadow-glow-accent)] transition-all
                   flex items-center gap-2 disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          새 업무 지시
        </button>
      </div>

      {/* New Task Form */}
      <AnimatePresence>
        {showNewForm && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">📋 CEO 업무 지시</h2>
              <button onClick={() => setShowNewForm(false)} className="text-[var(--dr-text-muted)] hover:text-[var(--dr-text)]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[12px] text-[var(--dr-text-secondary)] mb-4">
              업무를 자연어로 입력하면 수진(COO)이 적합한 직원 2~5명을 배정하고 협업 플로우를 설계합니다.
            </p>
            <div className="space-y-3">
              <div className="flex gap-2">
                {PROJECTS.map(p => (
                  <button
                    key={p.key}
                    onClick={() => setSelectedProject(selectedProject === p.key ? '' : p.key)}
                    className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors border ${selectedProject === p.key
                      ? 'bg-[var(--dr-accent)]/15 text-[var(--dr-accent)] border-[var(--dr-accent)]/30'
                      : 'text-[var(--dr-text-muted)] border-[var(--dr-glass-border)] hover:text-[var(--dr-text)]'
                      }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={taskInput}
                  onChange={(e) => setTaskInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && submitTask()}
                  placeholder='예: "댕냥 앱의 결제 시스템 보안 강화 방안을 마련하라"'
                  className="flex-1 px-4 py-3 rounded-lg bg-[var(--dr-bg-hover)] border border-[var(--dr-glass-border)]
                           text-[13px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                           focus:outline-none focus:border-[var(--dr-accent)]"
                  disabled={isLoading}
                />
                <button
                  onClick={submitTask}
                  disabled={isLoading || !taskInput.trim()}
                  className="px-6 py-3 rounded-lg bg-[var(--dr-accent)] text-white text-[13px] font-medium
                           hover:bg-[#b91c3c] transition-colors flex items-center gap-2
                           disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  {isLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> 처리 중...</>
                  ) : (
                    '지시'
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading */}
      {isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--dr-accent)] mx-auto mb-4" />
          <p className="text-[14px] font-medium text-[var(--dr-text)]">수진(COO)이 팀을 배정하고 있습니다...</p>
          <p className="text-[12px] text-[var(--dr-text-muted)] mt-1">적합한 직원을 선별하고 협업 플로우를 설계합니다.</p>
        </motion.div>
      )}

      {/* Search */}
      {results.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--dr-text-muted)]" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="업무 검색..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                     text-[12px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                     focus:outline-none focus:border-[var(--dr-accent)]"
          />
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Results List */}
        <div className="col-span-1 space-y-3">
          <h2 className="text-[14px] font-semibold text-[var(--dr-text)]">지시 기록 ({filteredResults.length})</h2>
          {filteredResults.length === 0 && !isLoading && (
            <div className="glass-card p-8 text-center">
              <Lightbulb className="w-10 h-10 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-30" />
              <p className="text-[12px] text-[var(--dr-text-muted)]">
                아직 업무 지시 기록이 없습니다.<br />"새 업무 지시"를 클릭하세요.
              </p>
            </div>
          )}
          {filteredResults.map((r) => {
            const isSelected = selectedResult?.id === r.id;
            return (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => setSelectedResult(r)}
                className={`glass-card p-4 cursor-pointer transition-all hover:border-[var(--dr-accent)]/40 ${isSelected ? 'border-[var(--dr-accent)]/60 bg-[var(--dr-accent)]/5' : ''
                  }`}
              >
                <h3 className="text-[13px] font-semibold text-[var(--dr-text)] mb-1 line-clamp-2">{r.task}</h3>
                <div className="flex items-center gap-2 text-[10px]">
                  {r.project && (
                    <span className="px-1.5 py-0.5 rounded bg-[var(--dr-accent)]/10 text-[var(--dr-accent)]">
                      {PROJECTS.find(p => p.key === r.project)?.label || r.project}
                    </span>
                  )}
                  <span className="text-[var(--dr-text-muted)]">{r.steps.length}명 배정</span>
                </div>
                <p className="text-[10px] text-[var(--dr-text-muted)] mt-1">
                  {new Date(r.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Detail */}
        <div className="col-span-2">
          {selectedResult ? (
            <div className="space-y-4">
              {/* Task Header */}
              <div className="glass-card p-5">
                <h2 className="text-[16px] font-semibold text-[var(--dr-text)] mb-2">
                  📋 {selectedResult.task}
                </h2>
                <div className="flex items-center gap-3 text-[12px] text-[var(--dr-text-muted)]">
                  {selectedResult.project && (
                    <span className="px-2 py-0.5 rounded bg-[var(--dr-accent)]/10 text-[var(--dr-accent)]">
                      {PROJECTS.find(p => p.key === selectedResult.project)?.label}
                    </span>
                  )}
                  <span><Users className="w-3 h-3 inline mr-1" />{selectedResult.steps.length}명 배정</span>
                </div>
              </div>

              {/* Coordinator Comment */}
              <div className="glass-card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-[#DC143C]/15 border border-[#DC143C]/30 flex items-center justify-center text-[14px]">
                    👩‍💼
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold text-[var(--dr-text)]">{selectedResult.coordinator} (COO)</p>
                    <p className="text-[10px] text-[var(--dr-text-muted)]">총괄이사 지시</p>
                  </div>
                </div>
                <p className="text-[12px] text-[var(--dr-text-secondary)] leading-relaxed p-3 rounded-lg bg-[var(--dr-bg-hover)]">
                  {selectedResult.coordinator_comment}
                </p>
              </div>

              {/* Collaboration Steps */}
              <div className="glass-card p-5">
                <h3 className="text-[14px] font-semibold text-[var(--dr-text)] mb-4">협업 플로우</h3>
                <div className="space-y-3">
                  {selectedResult.steps.map((step, idx) => {
                    const emp = employees.find(e => e.name === step.employee);
                    return (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="flex gap-3"
                      >
                        {/* Step Number */}
                        <div className="flex flex-col items-center">
                          <div className="w-7 h-7 rounded-full bg-[var(--dr-accent)] text-white text-[11px] font-bold flex items-center justify-center">
                            {idx + 1}
                          </div>
                          {idx < selectedResult.steps.length - 1 && (
                            <div className="w-0.5 h-full bg-[var(--dr-glass-border)] mt-1" />
                          )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 pb-4">
                          <div className="flex items-center gap-2 mb-1">
                            {emp && (
                              <AvatarRenderer config={emp.avatar} size="xs" bgColor={`${emp.departmentColor}15`} />
                            )}
                            <span className="text-[13px] font-medium text-[var(--dr-text)]">{step.employee}</span>
                            <span className="text-[10px] text-[var(--dr-text-muted)]">{step.department}</span>
                          </div>
                          <p className="text-[12px] text-[var(--dr-text-secondary)] mb-1">{step.action}</p>
                          <div className="flex items-center gap-1 text-[11px] text-[var(--dr-success)]">
                            <ArrowRight className="w-3 h-3" />
                            <span>산출물: {step.result}</span>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Summary */}
              {selectedResult.summary && (
                <div className="glass-card p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-[var(--dr-success)]" />
                    <h3 className="text-[13px] font-semibold text-[var(--dr-text)]">결과 요약</h3>
                  </div>
                  <p className="text-[12px] text-[var(--dr-text-secondary)] leading-relaxed">
                    {selectedResult.summary}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <Users className="w-12 h-12 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-20" />
              <p className="text-[13px] text-[var(--dr-text-muted)]">
                업무 지시를 선택하면 협업 결과를 확인할 수 있습니다
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
