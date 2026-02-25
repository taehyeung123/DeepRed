import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Search, Send, ChevronDown, Loader2, Bot, Zap, Users } from 'lucide-react';
import { employees as baseEmployees, DEPARTMENTS } from '../../data/employees';
import type { Employee } from '../../data/employees';
import { AvatarRenderer } from '../components/avatar/AvatarRenderer';
import { useEmployees } from '../hooks/useEmployees';

import { API_BASE } from '../lib/api';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  time: string;
  name?: string;
  model?: string;
}

// Map frontend employee data to server employee IDs
const EMPLOYEE_ID_MAP: Record<string, string> = {
  '수진': 'sujin', '민수': 'minsu', '태현': 'taehyun', '서윤': 'seoyun',
  '하준': 'hajun', '은서': 'eunseo', '지연': 'jiyeon', '도윤': 'doyun',
  '시우': 'siwoo', '준서': 'junseo', '채원': 'chaewon', '예준': 'yejun',
  '소율': 'soyul', '유나': 'yuna', '다은': 'daeun', '지호': 'jiho',
};

interface GroupMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  time: string;
  name?: string;
  responses?: { name: string; message: string }[];
}

export function Messenger() {
  const employees = useEmployees();
  const [selectedChat, setSelectedChat] = useState<Employee>(baseEmployees[0]);
  const [message, setMessage] = useState('');
  const [loadingChatId, setLoadingChatId] = useState<string | null>(null);
  const [collapsedDepts, setCollapsedDepts] = useState<Set<string>>(new Set());
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [chatMode, setChatMode] = useState<'dm' | 'group'>('dm');
  const [groupMessages, setGroupMessages] = useState<GroupMessage[]>([]);
  const [groupLoading, setGroupLoading] = useState(false);

  // Per-employee message history — persisted to localStorage
  const [chatHistories, setChatHistories] = useState<Record<string, Message[]>>(() => {
    try {
      const saved = localStorage.getItem('deepred-chat-histories');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const currentMessages = chatHistories[selectedChat.id] || [];

  // Save chat histories to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('deepred-chat-histories', JSON.stringify(chatHistories));
    } catch { /* storage full — ignore */ }
  }, [chatHistories]);

  // Load conversation from DB on employee selection
  useEffect(() => {
    const loadFromDb = async () => {
      try {
        const employeeId = EMPLOYEE_ID_MAP[selectedChat.name] || selectedChat.id;
        const res = await fetch(`${API_BASE}/api/conversations/${employeeId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.messages?.length) {
          // Convert DB format to Message format
          const dbMessages: Message[] = data.messages.map((msg: any, i: number) => ({
            id: `db-${i}`,
            sender: msg.isUser ? 'user' as const : 'ai' as const,
            text: msg.content || '',
            name: msg.name || selectedChat.name,
            time: msg.time || '',
          }));
          setChatHistories(prev => {
            const local = prev[selectedChat.id] || [];
            // DB takes priority if it has more messages
            if (dbMessages.length >= local.length) {
              return { ...prev, [selectedChat.id]: dbMessages };
            }
            return prev;
          });
        }
      } catch { /* DB unavailable — use localStorage cache */ }
    };
    loadFromDb();
  }, [selectedChat.id]);

  // Check server availability on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(res => res.ok ? setServerStatus('online') : setServerStatus('offline'))
      .catch(() => setServerStatus('offline'));
  }, []);

  // Poll for proactive messages from Sujin (every 30s)
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/proactive/messages?employee_id=sujin`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          const newMsgs: Message[] = data.messages.map((m: any) => ({
            id: m.id,
            sender: 'ai' as const,
            text: m.text,
            name: m.employee_name,
            time: new Date(m.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
            model: 'claude',
          }));
          // Inject into sujin's chat
          setChatHistories(prev => {
            const sujinId = baseEmployees.find(e => e.name === '수진')?.id || 'sujin';
            const existing = prev[sujinId] || [];
            const existingIds = new Set(existing.map(m => m.id));
            const fresh = newMsgs.filter(m => !existingIds.has(m.id));
            if (fresh.length === 0) return prev;
            return { ...prev, [sujinId]: [...existing, ...fresh] };
          });
          // Mark as read
          const ids = data.messages.map((m: any) => m.id);
          fetch(`${API_BASE}/api/proactive/read`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message_ids: ids }),
          }).catch(() => { });
        }
      } catch { /* server offline */ }
    };
    poll(); // initial check
    const interval = setInterval(poll, 30000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages]);

  const handleSend = useCallback(async () => {
    if (!message.trim() || loadingChatId) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: message,
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    };

    const updatedHistory = [...currentMessages, userMsg];
    setChatHistories(prev => ({ ...prev, [selectedChat.id]: updatedHistory }));
    setMessage('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setLoadingChatId(selectedChat.id);

    try {
      const apiHistory = updatedHistory.map(msg => ({
        isUser: msg.sender === 'user',
        content: msg.text,
        name: msg.sender === 'ai' ? selectedChat.name : undefined,
      }));

      const employeeId = EMPLOYEE_ID_MAP[selectedChat.name] || selectedChat.id;

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId,
          employee_name: selectedChat.name,
          employee_role: selectedChat.role,
          message: message,
          history: apiHistory.slice(0, -1), // exclude current message (it's in 'message' field)
        }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const data = await response.json();

      const isSujinChat = employeeId === 'sujin';

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: data.message,
        name: data.name || selectedChat.name,
        time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
        model: data.model?.includes('claude') ? 'claude' : data.model?.includes('kimi') ? 'kimi' : data.model ? 'gemini' : (isSujinChat ? 'claude' : 'gemini'),
      };

      setChatHistories(prev => {
        const finalHistory = [...(prev[selectedChat.id] || []), aiMsg];

        // Save to DB asynchronously (fire-and-forget)
        const eid = EMPLOYEE_ID_MAP[selectedChat.name] || selectedChat.id;
        fetch(`${API_BASE}/api/conversations/${eid}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: finalHistory.map(m => ({
              isUser: m.sender === 'user',
              content: m.text,
              name: m.sender === 'ai' ? m.name : undefined,
              time: m.time,
            })),
            employee_name: selectedChat.name,
          }),
        }).catch(() => { /* DB save failed — localStorage still has it */ });

        return { ...prev, [selectedChat.id]: finalHistory };
      });

    } catch (error) {
      // Fallback: show error message
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: `⚠️ 서버 연결 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}.\n서버가 실행 중인지 확인하세요 (python server/main.py)`,
        name: '시스템',
        time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };

      setChatHistories(prev => ({
        ...prev,
        [selectedChat.id]: [...(prev[selectedChat.id] || []), errMsg],
      }));
    } finally {
      setLoadingChatId(null);
    }
  }, [message, loadingChatId, selectedChat, currentMessages]);

  const handleGroupSend = useCallback(async () => {
    if (!message.trim() || groupLoading) return;
    const userMsg: GroupMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: message,
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    };
    setGroupMessages(prev => [...prev, userMsg]);
    const outMsg = message;
    setMessage('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setGroupLoading(true);

    try {
      const apiHistory = groupMessages.slice(-8).map(m => ({
        isUser: m.sender === 'user',
        content: m.text,
        name: m.name,
      }));

      const res = await fetch(`${API_BASE}/api/group-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: outMsg, history: apiHistory }),
      });
      const data = await res.json();
      const responses: { name: string; message: string }[] = data.responses || [];

      // Add each response as a separate group message
      for (const r of responses) {
        const aiMsg: GroupMessage = {
          id: `${Date.now()}-${r.name}`,
          sender: 'ai',
          text: r.message,
          name: r.name,
          time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
        };
        setGroupMessages(prev => [...prev, aiMsg]);
      }
    } catch (err) {
      setGroupMessages(prev => [...prev, {
        id: `${Date.now()}-err`,
        sender: 'ai',
        text: `⚠️ 서버 연결 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`,
        name: '시스템',
        time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setGroupLoading(false);
    }
  }, [message, groupLoading, groupMessages]);

  const departments = Object.values(DEPARTMENTS);

  // Group employees by department
  const employeesByDept = departments.map((dept) => ({
    ...dept,
    employees: employees.filter((emp) => emp.department === dept.name),
  })).filter((dept) => dept.employees.length > 0);

  const toggleDepartment = (deptName: string) => {
    const newCollapsed = new Set(collapsedDepts);
    if (newCollapsed.has(deptName)) {
      newCollapsed.delete(deptName);
    } else {
      newCollapsed.add(deptName);
    }
    setCollapsedDepts(newCollapsed);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4">
      {/* Chat List */}
      <div className="w-80 glass-card flex flex-col">
        {/* Mode Tabs */}
        <div className="p-3 border-b border-[var(--dr-glass-border)]">
          <div className="flex gap-1 p-1 rounded-lg bg-[var(--dr-bg-hover)]">
            <button
              onClick={() => setChatMode('dm')}
              className={`flex-1 py-1.5 rounded-md text-[11px] font-medium transition-all flex items-center justify-center gap-1.5 ${chatMode === 'dm'
                ? 'bg-[var(--dr-bg-card)] text-[var(--dr-text)] shadow-sm'
                : 'text-[var(--dr-text-muted)] hover:text-[var(--dr-text)]'
                }`}
            >
              <Send className="w-3 h-3" /> 1:1 DM
            </button>
            <button
              onClick={() => setChatMode('group')}
              className={`flex-1 py-1.5 rounded-md text-[11px] font-medium transition-all flex items-center justify-center gap-1.5 ${chatMode === 'group'
                ? 'bg-[var(--dr-bg-card)] text-[var(--dr-text)] shadow-sm'
                : 'text-[var(--dr-text-muted)] hover:text-[var(--dr-text)]'
                }`}
            >
              <Users className="w-3 h-3" /> 단체 채팅
            </button>
          </div>
        </div>

        {/* Search */}
        {chatMode === 'dm' && (
          <div className="p-4 border-b border-[var(--dr-glass-border)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--dr-text-muted)]" />
              <input
                type="text"
                placeholder="검색..."
                className="w-full h-9 pl-10 pr-4 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                       rounded-lg text-[12px] text-[var(--dr-text)]
                       placeholder:text-[var(--dr-text-muted)]
                       focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30"
              />
            </div>
          </div>
        )}

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto">
          {chatMode === 'group' ? (
            <div className="p-4 text-center">
              <div className="w-16 h-16 rounded-full bg-[var(--dr-accent)]/10 flex items-center justify-center mx-auto mb-3">
                <Users className="w-7 h-7 text-[var(--dr-accent)]" />
              </div>
              <h3 className="text-[14px] font-semibold text-[var(--dr-text)] mb-1">전체 채팅방</h3>
              <p className="text-[11px] text-[var(--dr-text-muted)] leading-relaxed">
                사장님이 메시지를 보내면<br />관련 직원 2~4명이 반응합니다
              </p>
              <div className="mt-4 flex flex-wrap gap-1 justify-center">
                {employees.slice(0, 8).map(e => (
                  <AvatarRenderer key={e.id} config={e.avatar} size="xs" bgColor={`${e.departmentColor}15`} />
                ))}
                <div className="w-7 h-7 rounded-full bg-[var(--dr-bg-hover)] flex items-center justify-center text-[10px] text-[var(--dr-text-muted)]">+8</div>
              </div>
            </div>
          ) : (
            <>
              {/* Individual DMs - Grouped by Department */}
              <div className="p-3">
                <div className="text-[10px] text-[var(--dr-text-muted)] uppercase tracking-wider font-medium mb-2 px-2">
                  개인 DM
                </div>
                <div className="space-y-3">
                  {employeesByDept.map((dept) => (
                    <div key={dept.name}>
                      {/* Department Header */}
                      <button
                        onClick={() => toggleDepartment(dept.name)}
                        className="w-full flex items-center justify-between px-2 py-1.5 hover:bg-[var(--dr-bg-hover)] rounded-lg transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[14px]">{dept.emoji}</span>
                          <span className="text-[11px] font-medium text-[var(--dr-text-secondary)]">{dept.name}</span>
                          <span className="text-[10px] text-[var(--dr-text-muted)]">({dept.employees.length})</span>
                        </div>
                        <ChevronDown
                          className={`w-3.5 h-3.5 text-[var(--dr-text-muted)] transition-transform ${collapsedDepts.has(dept.name) ? '-rotate-90' : ''
                            }`}
                        />
                      </button>

                      {/* Department Employees */}
                      {!collapsedDepts.has(dept.name) && (
                        <div className="space-y-1 mt-1">
                          {dept.employees.map((emp) => {
                            const isSujin = EMPLOYEE_ID_MAP[emp.name] === 'sujin';
                            const hasUnread = (chatHistories[emp.id]?.length || 0) > 0;
                            return (
                              <button
                                key={emp.id}
                                onClick={() => setSelectedChat(emp)}
                                className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-all text-left ml-4
                              ${selectedChat.id === emp.id
                                    ? 'bg-[var(--dr-accent-soft)] border border-[var(--dr-accent)]/20'
                                    : 'hover:bg-[var(--dr-bg-hover)]'
                                  }`}
                              >
                                <div className="flex-shrink-0 border-2 rounded-full" style={{ borderColor: emp.status === 'working' ? emp.departmentColor : 'transparent' }}>
                                  <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${emp.departmentColor}20`} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[13px] font-medium text-[var(--dr-text)] truncate">
                                      {emp.name}
                                      {isSujin && (
                                        <span className="ml-1 text-[9px] px-1.5 py-0.5 rounded-full bg-[#7c3aed]/20 text-[#a78bfa] font-medium">
                                          Claude
                                        </span>
                                      )}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-[var(--dr-text-muted)] truncate">
                                    {emp.role}
                                  </p>
                                </div>
                                {hasUnread && (
                                  <div className="w-2 h-2 rounded-full bg-[var(--dr-accent)]" />
                                )}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chat Window */}
      <div className="flex-1 glass-card flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-[var(--dr-glass-border)] flex items-center gap-3">
          {chatMode === 'group' ? (
            <>
              <div className="w-12 h-12 rounded-full bg-[var(--dr-accent)]/15 flex items-center justify-center">
                <Users className="w-6 h-6 text-[var(--dr-accent)]" />
              </div>
              <div className="flex-1">
                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">전체 채팅방</h2>
                <span className="text-[11px] text-[var(--dr-text-secondary)]">16명 참여 · 관련 직원 자동 반응</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]">
                <Bot className="w-3.5 h-3.5 text-[var(--dr-text-muted)]" />
                <span className="text-[10px] text-[var(--dr-text-muted)]">Gemini AI</span>
              </div>
            </>
          ) : (
            <>
              <div className="border-2 rounded-full" style={{ borderColor: selectedChat.departmentColor }}>
                <AvatarRenderer config={selectedChat.avatar} size="md" bgColor={`${selectedChat.departmentColor}20`} />
              </div>
              <div className="flex-1">
                <h2 className="text-[15px] font-semibold text-[var(--dr-text)]">
                  {selectedChat.name}
                </h2>
                <div className="flex items-center gap-2">
                  <div
                    className="w-1.5 h-1.5 rounded-full status-dot-pulse"
                    style={{
                      backgroundColor:
                        selectedChat.status === 'working' ? 'var(--dr-success)' : 'var(--dr-text-muted)',
                    }}
                  />
                  <span className="text-[11px] text-[var(--dr-text-secondary)]">
                    {selectedChat.role}
                  </span>
                  {EMPLOYEE_ID_MAP[selectedChat.name] === 'sujin' && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#7c3aed]/15 text-[#a78bfa] border border-[#7c3aed]/20 flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Claude AI
                    </span>
                  )}
                </div>
              </div>
              {/* Model indicator */}
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]">
                <Bot className="w-3.5 h-3.5 text-[var(--dr-text-muted)]" />
                <span className="text-[10px] text-[var(--dr-text-muted)]">
                  {EMPLOYEE_ID_MAP[selectedChat.name] === 'sujin' ? 'Claude' : 'Gemini'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {chatMode === 'group' ? (
            <>
              {groupMessages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <Users className="w-12 h-12 text-[var(--dr-text-muted)] opacity-30 mb-3" />
                  <p className="text-[14px] font-medium text-[var(--dr-text)]">전체 채팅방</p>
                  <p className="text-[12px] text-[var(--dr-text-muted)] mt-1">메시지를 보내면 관련 직원 2~4명이 자동 반응합니다</p>
                </div>
              )}
              {groupMessages.map((msg) => {
                const emp = msg.name ? employees.find(e => e.name === msg.name) : null;
                return (
                  <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.sender === 'ai' && emp && (
                      <div className="mr-2 flex-shrink-0 mt-1">
                        <AvatarRenderer config={emp.avatar} size="sm" bgColor={`${emp.departmentColor}15`} />
                      </div>
                    )}
                    <div className={`max-w-[70%] ${msg.sender === 'user'
                      ? 'bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white'
                      : 'glass-card'
                      } p-3 rounded-2xl`}>
                      {msg.sender === 'ai' && msg.name && (
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[11px] font-semibold" style={{ color: emp?.departmentColor || 'var(--dr-text)' }}>{msg.name}</span>
                          {emp && <span className="text-[9px] text-[var(--dr-text-muted)]">{emp.role}</span>}
                        </div>
                      )}
                      <p className={`text-[13px] whitespace-pre-wrap ${msg.sender === 'user' ? 'text-white' : 'text-[var(--dr-text)]'}`}>{msg.text}</p>
                      <p className={`text-[10px] mt-1 ${msg.sender === 'user' ? 'text-white/70' : 'text-[var(--dr-text-muted)]'}`}>{msg.time}</p>
                    </div>
                  </div>
                );
              })}
              {groupLoading && (
                <div className="flex justify-start">
                  <div className="glass-card p-3 rounded-2xl flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-[var(--dr-accent)]" />
                    <span className="text-[12px] text-[var(--dr-text-muted)]">직원들이 반응하는 중...</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              {currentMessages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="mb-3"><AvatarRenderer config={selectedChat.avatar} size="xl" bgColor={`${selectedChat.departmentColor}20`} /></div>
                  <p className="text-[14px] font-medium text-[var(--dr-text)]">{selectedChat.name}</p>
                  <p className="text-[12px] text-[var(--dr-text-muted)] mt-1">{selectedChat.role} · {selectedChat.department}</p>
                  <p className="text-[12px] text-[var(--dr-text-muted)] mt-3 max-w-xs">
                    메시지를 보내서 대화를 시작하세요
                  </p>
                  {EMPLOYEE_ID_MAP[selectedChat.name] === 'sujin' && (
                    <div className="mt-4 px-4 py-2 rounded-lg bg-[#7c3aed]/10 border border-[#7c3aed]/20">
                      <p className="text-[11px] text-[#a78bfa]">
                        🤖 수진은 Claude AI로 구동됩니다
                      </p>
                    </div>
                  )}
                </div>
              )}
              {currentMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'ai' && (
                    <div className="mr-2 flex-shrink-0 mt-1">
                      <AvatarRenderer config={selectedChat.avatar} size="sm" bgColor={`${selectedChat.departmentColor}15`} />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] ${msg.sender === 'user'
                      ? 'bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white'
                      : 'glass-card'
                      } p-3 rounded-2xl`}
                  >
                    {msg.sender === 'ai' && msg.name && (
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-semibold" style={{ color: selectedChat.departmentColor }}>
                          {msg.name}
                        </span>
                        {msg.model && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${msg.model?.includes('claude') ? 'bg-[#7c3aed]/15 text-[#a78bfa]' : 'bg-[#3b82f6]/15 text-[#7dd3fc]'
                            }`}>
                            {msg.model?.includes('claude') ? 'Claude' : 'Gemini'}
                          </span>
                        )}
                      </div>
                    )}
                    <p className={`text-[13px] whitespace-pre-wrap ${msg.sender === 'user' ? 'text-white' : 'text-[var(--dr-text)]'}`}>
                      {msg.text}
                    </p>
                    <p className={`text-[10px] mt-1 ${msg.sender === 'user' ? 'text-white/70' : 'text-[var(--dr-text-muted)]'}`}>
                      {msg.time}
                    </p>
                  </div>
                </div>
              ))}
              {loadingChatId === selectedChat.id && (
                <div className="flex justify-start">
                  <div className="glass-card p-3 rounded-2xl flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-[var(--dr-accent)]" />
                    <span className="text-[12px] text-[var(--dr-text-muted)]">{selectedChat.name} 입력 중...</span>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[var(--dr-glass-border)]">
          <div className="flex gap-3 items-end">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                // Auto-resize: reset height then set to scrollHeight
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !e.altKey) {
                  e.preventDefault();
                  chatMode === 'group' ? handleGroupSend() : handleSend();
                }
                // Shift+Enter or Alt+Enter → default behavior (newline)
              }}
              placeholder={chatMode === 'group' ? '전체 채팅방에 메시지 보내기...' : `${selectedChat.name}에게 메시지 보내기...`}
              disabled={chatMode === 'group' ? groupLoading : !!loadingChatId}
              rows={1}
              className="flex-1 min-h-[40px] max-h-[120px] px-4 py-2.5 bg-[var(--dr-bg-card)] border border-[var(--dr-glass-border)]
                       rounded-lg text-[13px] text-[var(--dr-text)] resize-none
                       placeholder:text-[var(--dr-text-muted)]
                       focus:outline-none focus:ring-2 focus:ring-[var(--dr-accent)]/30
                       disabled:opacity-50"
            />
            <button
              onClick={chatMode === 'group' ? handleGroupSend : handleSend}
              disabled={(chatMode === 'group' ? groupLoading : !!loadingChatId) || !message.trim()}
              className="px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--dr-accent)] to-[#b91c3c] text-white
                       hover:shadow-[var(--shadow-glow-accent)] transition-all duration-300
                       flex items-center gap-2
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {(chatMode === 'group' ? groupLoading : !!loadingChatId) ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span className="text-[13px] font-medium">전송</span>
            </button>
          </div>
          {/* Server status bar */}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${serverStatus === 'online' ? 'bg-[var(--dr-success)]' :
                serverStatus === 'checking' ? 'bg-[var(--dr-warning)]' : 'bg-[var(--dr-error)]'
                }`} />
              <span className="text-[10px] text-[var(--dr-text-muted)]">
                서버 {serverStatus === 'online' ? '연결됨' : serverStatus === 'checking' ? '확인 중...' : '오프라인'}
              </span>
            </div>
            <span className="text-[10px] text-[var(--dr-text-muted)]">
              {chatMode === 'group'
                ? 'Gemini AI · 2~4명 자동 반응'
                : EMPLOYEE_ID_MAP[selectedChat.name] === 'sujin' ? 'Claude AI · 프리미엄 응답' : 'Gemini AI'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}