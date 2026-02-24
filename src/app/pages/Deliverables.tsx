import { useState, useEffect, useCallback } from 'react';
import { Search, FileText, Loader2, RefreshCw, Calendar, User, Tag } from 'lucide-react';
import { motion } from 'motion/react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Document {
  id: string;
  title: string;
  content: string;
  doc_type: string;
  author_id?: string;
  author_name?: string;
  project?: string;
  created_at: string;
}

const DOC_TYPE_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  briefing: { label: '브리핑', color: '#DC143C', icon: '📊' },
  collaboration: { label: '협업 결과', color: '#3b82f6', icon: '🤝' },
  meeting: { label: '회의록', color: '#f59e0b', icon: '📋' },
  analysis: { label: '분석', color: '#6366f1', icon: '📈' },
  report: { label: '보고서', color: '#22c55e', icon: '📄' },
  security: { label: '보안', color: '#ef4444', icon: '🔒' },
};

const DOC_FILTERS = [
  { key: '', label: '전체' },
  { key: 'briefing', label: '브리핑' },
  { key: 'collaboration', label: '협업' },
  { key: 'meeting', label: '회의록' },
  { key: 'report', label: '보고서' },
];

export function Deliverables() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Document[] | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [typeFilter, setTypeFilter] = useState('');
  const [searching, setSearching] = useState(false);

  const fetchDocuments = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '30' });
      if (typeFilter) params.set('doc_type', typeFilter);
      const res = await fetch(`${API_BASE}/api/documents?${params}`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch { setDocuments([]); }
    setLoading(false);
  }, [typeFilter]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/documents/search?query=${encodeURIComponent(searchQuery)}&limit=10`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch { setSearchResults([]); }
    setSearching(false);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  const displayDocs = searchResults !== null ? searchResults : documents;

  const getRelativeTime = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '방금 전';
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    return `${Math.floor(hours / 24)}일 전`;
  };

  const tryParseContent = (content: string) => {
    try {
      return JSON.parse(content);
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--dr-accent)] mx-auto mb-3" />
          <p className="text-[13px] text-[var(--dr-text-muted)]">문서 로딩...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold text-[var(--dr-text)] mb-1">산출물</h1>
          <p className="text-[13px] text-[var(--dr-text-secondary)]">AI 직원이 생성한 문서와 보고서</p>
        </div>
        <button
          onClick={() => { setLoading(true); fetchDocuments(); }}
          className="px-3 py-2 rounded-lg bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                   text-[12px] text-[var(--dr-text-secondary)] hover:text-[var(--dr-text)] transition-all
                   flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" /> 새로고침
        </button>
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--dr-text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="문서 검색..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                     text-[13px] text-[var(--dr-text)] placeholder:text-[var(--dr-text-muted)]
                     focus:outline-none focus:border-[var(--dr-accent)]"
          />
          {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-[var(--dr-accent)]" />}
        </div>
        {searchResults !== null && (
          <button onClick={clearSearch} className="text-[11px] text-[var(--dr-accent)] hover:underline">
            검색 초기화
          </button>
        )}
        <div className="flex gap-1.5">
          {DOC_FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => { setTypeFilter(f.key); setSearchResults(null); }}
              className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors border ${typeFilter === f.key
                  ? 'bg-[var(--dr-accent)]/15 text-[var(--dr-accent)] border-[var(--dr-accent)]/30'
                  : 'text-[var(--dr-text-muted)] border-[var(--dr-glass-border)] hover:text-[var(--dr-text)]'
                }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Document List */}
        <div className="col-span-1 space-y-2 max-h-[70vh] overflow-y-auto pr-1">
          <p className="text-[12px] text-[var(--dr-text-muted)] mb-2">
            {searchResults !== null ? `${displayDocs.length}건 검색 결과` : `${displayDocs.length}건 문서`}
          </p>
          {displayDocs.length === 0 ? (
            <div className="glass-card p-8 text-center">
              <FileText className="w-10 h-10 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-30" />
              <p className="text-[12px] text-[var(--dr-text-muted)]">
                {searchResults !== null ? '검색 결과가 없습니다' : '문서가 없습니다. 브리핑이나 회의를 진행하면 자동 저장됩니다.'}
              </p>
            </div>
          ) : (
            displayDocs.map((doc, idx) => {
              const typeInfo = DOC_TYPE_LABELS[doc.doc_type] || { label: doc.doc_type, color: '#6b7280', icon: '📄' };
              const isSelected = selectedDoc?.id === doc.id;
              return (
                <motion.div
                  key={doc.id || idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  onClick={() => setSelectedDoc(doc)}
                  className={`glass-card p-3 cursor-pointer transition-all hover:border-[var(--dr-accent)]/40 ${isSelected ? 'border-[var(--dr-accent)]/60 bg-[var(--dr-accent)]/5' : ''
                    }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-[16px]">{typeInfo.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-[var(--dr-text)] line-clamp-2">{doc.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${typeInfo.color}15`, color: typeInfo.color }}>
                          {typeInfo.label}
                        </span>
                        {doc.author_name && <span className="text-[10px] text-[var(--dr-text-muted)]">{doc.author_name}</span>}
                        <span className="text-[10px] text-[var(--dr-text-muted)]">{getRelativeTime(doc.created_at)}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>

        {/* Document Detail */}
        <div className="col-span-2">
          {selectedDoc ? (() => {
            const typeInfo = DOC_TYPE_LABELS[selectedDoc.doc_type] || { label: selectedDoc.doc_type, color: '#6b7280', icon: '📄' };
            const parsed = tryParseContent(selectedDoc.content);
            return (
              <div className="space-y-4">
                <div className="glass-card p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[20px]">{typeInfo.icon}</span>
                    <div>
                      <h2 className="text-[16px] font-semibold text-[var(--dr-text)]">{selectedDoc.title}</h2>
                      <div className="flex items-center gap-3 mt-1 text-[11px] text-[var(--dr-text-muted)]">
                        {selectedDoc.author_name && (
                          <span className="flex items-center gap-1"><User className="w-3 h-3" />{selectedDoc.author_name}</span>
                        )}
                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{getRelativeTime(selectedDoc.created_at)}</span>
                        <span className="flex items-center gap-1"><Tag className="w-3 h-3" style={{ color: typeInfo.color }} />{typeInfo.label}</span>
                        {selectedDoc.project && <span className="px-1.5 py-0.5 rounded bg-[var(--dr-accent)]/10 text-[var(--dr-accent)]">{selectedDoc.project}</span>}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="glass-card p-5">
                  {parsed ? (
                    <div className="space-y-4">
                      {/* Briefing format */}
                      {parsed.greeting && (
                        <div className="p-3 rounded-lg bg-[var(--dr-bg-hover)]">
                          <p className="text-[13px] text-[var(--dr-text)]">{parsed.greeting}</p>
                          {parsed.summary && <p className="text-[12px] text-[var(--dr-text-secondary)] mt-1">{parsed.summary}</p>}
                        </div>
                      )}
                      {parsed.highlights && (
                        <div>
                          <h3 className="text-[13px] font-semibold text-[var(--dr-text)] mb-2">📌 하이라이트</h3>
                          <div className="space-y-1.5">
                            {parsed.highlights.map((h: any, i: number) => (
                              <div key={i} className="text-[12px] text-[var(--dr-text-secondary)] flex gap-2">
                                <span>•</span>
                                <span>{h.project}: {h.status} ({h.metric})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {parsed.recommendation && (
                        <div className="p-3 rounded-lg bg-[var(--dr-success)]/5 border border-[var(--dr-success)]/20">
                          <p className="text-[12px] text-[var(--dr-success)]">💡 {parsed.recommendation}</p>
                        </div>
                      )}
                      {/* Collaboration format */}
                      {parsed.coordinator_comment && (
                        <div className="p-3 rounded-lg bg-[var(--dr-bg-hover)]">
                          <p className="text-[12px] font-medium text-[var(--dr-text)]">{parsed.coordinator} 의견:</p>
                          <p className="text-[12px] text-[var(--dr-text-secondary)] mt-1">{parsed.coordinator_comment}</p>
                        </div>
                      )}
                      {parsed.steps && (
                        <div className="space-y-2">
                          {parsed.steps.map((s: any, i: number) => (
                            <div key={i} className="flex gap-3 items-start text-[12px]">
                              <div className="w-6 h-6 rounded-full bg-[var(--dr-accent)] text-white text-[10px] flex items-center justify-center flex-shrink-0">{i + 1}</div>
                              <div>
                                <span className="font-medium text-[var(--dr-text)]">{s.employee}</span>
                                <span className="text-[var(--dr-text-muted)]"> ({s.department})</span>
                                <p className="text-[var(--dr-text-secondary)]">{s.action} → {s.result}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {(parsed.summary && !parsed.greeting) && (
                        <div className="p-3 rounded-lg bg-[var(--dr-bg-hover)]">
                          <p className="text-[12px] text-[var(--dr-text-secondary)]">📝 {parsed.summary}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <pre className="text-[12px] text-[var(--dr-text-secondary)] whitespace-pre-wrap font-sans leading-relaxed">
                      {selectedDoc.content}
                    </pre>
                  )}
                </div>
              </div>
            );
          })() : (
            <div className="glass-card p-12 text-center">
              <FileText className="w-12 h-12 text-[var(--dr-text-muted)] mx-auto mb-3 opacity-20" />
              <p className="text-[13px] text-[var(--dr-text-muted)]">
                문서를 선택하면 상세 내용을 확인할 수 있습니다
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
