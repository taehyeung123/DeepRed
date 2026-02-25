import type { AvatarConfig } from './avatarParts'
import { EMPLOYEE_AVATARS, DEFAULT_AVATAR } from './avatarParts'

export interface Employee {
  id: string;
  name: string;
  role: string;
  department: string;
  departmentColor: string;
  emoji: string;
  avatar: AvatarConfig;
  status: 'working' | 'reporting' | 'meeting' | 'offline';
  personality: string;
  currentTask: string;
  currentProject: string;
  progress: number;
  contribution: number;
  accuracy: number;
  todayTasks: number;
  skills: string[];
  recentDeliverables: string[];
}

// ─── 7부서 체계 ─────────────────────────────
export const DEPARTMENTS = {
  control: { name: '컨트롤 타워', color: '#DC143C', emoji: '📊' },
  strategy: { name: '전략 기획실', color: '#3b82f6', emoji: '📋' },
  product: { name: '프로덕트 랩', color: '#ec4899', emoji: '🎨' },
  growth: { name: '콘텐츠 & 그로스', color: '#22c55e', emoji: '📈' },
  security_qa: { name: '보안 & 품질', color: '#f59e0b', emoji: '🔍' },
  analytics: { name: '분석 & 리서치', color: '#6366f1', emoji: '🧮' },
  customer: { name: '고객 경험', color: '#a855f7', emoji: '💬' },
};

// Backward-compatible departments array for OrganizationChart
export const departments = Object.entries(DEPARTMENTS).map(([id, dept]) => ({
  id,
  name: dept.name,
  icon: dept.emoji,
  color: dept.color,
}));

// Map department name → department id (for org chart compat)
export const DEPT_NAME_TO_ID: Record<string, string> = Object.fromEntries(
  Object.entries(DEPARTMENTS).map(([id, dept]) => [dept.name, id])
);

const activities = [
  '보고서 작성 중',
  '코드 리뷰 진행',
  '기획안 검토',
  'UI 디자인 수정',
  '데이터 분석 중',
  '회의 참석 중',
  '문서 업데이트',
  '버그 수정 중',
  '테스트 진행',
  '고객 응대 중',
];

export const employees: Employee[] = ([
  // ─── 컨트롤 타워 ────────────────────────────
  {
    id: 'sujin',
    name: '수진',
    role: 'COO (총괄이사)',
    department: '컨트롤 타워',
    departmentColor: DEPARTMENTS.control.color,
    emoji: '📊',
    status: 'offline',
    personality: '냉철하고 체계적인 참모형이지만 딱딱하지는 않음. 전체 그림을 보고 부서 간 마찰을 자연스럽게 조율.',
    currentTask: 'Q1 전략 브리핑 준비',
    currentProject: '2026 사업 계획',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['업무 조율', 'CEO 브리핑', '의사결정 지원', '리소스 배분'],
    recentDeliverables: [
      'Q1 경영 브리핑 자료',
      '부서별 KPI 설정 가이드',
      '2026 투자 계획서',
    ],
  },
  // ─── 전략 기획실 ────────────────────────────
  {
    id: 'minsu',
    name: '민수',
    role: '기획관',
    department: '전략 기획실',
    departmentColor: DEPARTMENTS.strategy.color,
    emoji: '📋',
    status: 'offline',
    personality: '논리 기계. 모든 주장에 근거를 대고, 우선순위를 수치로 매기는 분석형.',
    currentTask: '스프린트 백로그 정리',
    currentProject: '댕냥 앱 리뉴얼',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['사업 기획', '로드맵 설계', '스프린트 계획', 'PRD 작성'],
    recentDeliverables: [
      '댕냥 2.0 기획서',
      '사용자 시나리오 문서',
      'MVP 정의서',
    ],
  },
  {
    id: 'siwoo',
    name: '시우',
    role: '비즈니스 전략가',
    department: '전략 기획실',
    departmentColor: DEPARTMENTS.strategy.color,
    emoji: '📋',
    status: 'offline',
    personality: 'MBA 출신 느낌의 전략가. 모든 걸 PMF, LTV, CAC로 환산.',
    currentTask: '경쟁사 분석',
    currentProject: '신규 사업 진출 전략',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['수익 모델 설계', '가격 정책', '파트너십', '성장 전략'],
    recentDeliverables: [
      '시장 진입 전략서',
      '경쟁 분석 보고서',
      '사업성 검토 문서',
    ],
  },
  {
    id: 'yejun',
    name: '예준',
    role: '데이터 분석가',
    department: '전략 기획실',
    departmentColor: DEPARTMENTS.strategy.color,
    emoji: '📋',
    status: 'offline',
    personality: '가설→검증→결론의 과학자 마인드. 숫자를 예술처럼 다룸.',
    currentTask: '사용자 행동 분석',
    currentProject: '데이터 인사이트 리포트',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['퍼널 분석', '리텐션 추적', 'A/B 테스트', 'KPI 대시보드'],
    recentDeliverables: [
      '월간 데이터 리포트',
      'A/B 테스트 결과',
      '사용자 코호트 분석',
    ],
  },
  // ─── 프로덕트 랩 ────────────────────────────
  {
    id: 'seoyun',
    name: '서윤',
    role: '디자이너',
    department: '프로덕트 랩',
    departmentColor: DEPARTMENTS.product.color,
    emoji: '🎨',
    status: 'offline',
    personality: 'UI/UX 감각이 뛰어난 디자인 시스템 덕후. 접근성 챔피언.',
    currentTask: '랜딩 페이지 디자인',
    currentProject: '브랜드 리뉴얼',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['UI/UX 설계', '디자인 시스템', '프로토타입', '접근성 점검'],
    recentDeliverables: [
      '댕냥 디자인 시스템',
      '마케팅 배너 세트',
      '앱 아이콘 디자인',
    ],
  },
  {
    id: 'junseo',
    name: '준서',
    role: '자동화 엔지니어',
    department: '프로덕트 랩',
    departmentColor: DEPARTMENTS.product.color,
    emoji: '🎨',
    status: 'offline',
    personality: '수동으로 하면 지는 것이 인생 모토. 효율성에 집착.',
    currentTask: 'CI/CD 파이프라인 최적화',
    currentProject: '워크플로우 자동화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['에이전트 워크플로우', 'CI/CD', '서버 모니터링', 'API 연동'],
    recentDeliverables: [
      '배포 자동화 스크립트',
      '테스트 자동화 프레임워크',
      '모니터링 대시보드',
    ],
  },
  // ─── 콘텐츠 & 그로스 ────────────────────────
  {
    id: 'hajun',
    name: '하준',
    role: '콘텐츠 PD',
    department: '콘텐츠 & 그로스',
    departmentColor: DEPARTMENTS.growth.color,
    emoji: '📈',
    status: 'offline',
    personality: '콘텐츠 품질에 진심. 좋은 글은 수정에서 나온다는 장인 기질.',
    currentTask: '블로그 콘텐츠 기획',
    currentProject: '콘텐츠 마케팅 캠페인',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['콘텐츠 기획', '블로그 원고', '리라이팅', '에디토리얼 가이드'],
    recentDeliverables: [
      '2월 블로그 콘텐츠 10편',
      'SNS 콘텐츠 캘린더',
      '브랜드 스토리 가이드',
    ],
  },
  {
    id: 'eunseo',
    name: '은서',
    role: '카피라이터',
    department: '콘텐츠 & 그로스',
    departmentColor: DEPARTMENTS.growth.color,
    emoji: '📈',
    status: 'offline',
    personality: '단어 하나에 집착하는 완벽주의자. 한 줄이 결과를 바꾼다는 신념.',
    currentTask: '광고 카피 작성',
    currentProject: '봄 시즌 캠페인',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['광고 카피', '앱스토어 설명문', '랜딩페이지 카피', 'CTA 문구'],
    recentDeliverables: [
      '댕냥 광고 카피 20종',
      '이메일 뉴스레터 템플릿',
      '제품 설명 문구',
    ],
  },
  {
    id: 'jiyeon',
    name: '지연',
    role: 'SNS 마케터',
    department: '콘텐츠 & 그로스',
    departmentColor: DEPARTMENTS.growth.color,
    emoji: '📈',
    status: 'offline',
    personality: '트렌드에 민감한 2030 마케터. 에너지 넘치고 바이럴 감각이 뛰어남.',
    currentTask: '인스타그램 콘텐츠 제작',
    currentProject: 'SNS 성장 전략',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['SNS 채널 운영', '인플루언서 협업', '이벤트 기획', '프로모션 설계'],
    recentDeliverables: [
      'Instagram 릴스 10편',
      'SNS 광고 캠페인 기획',
      '인플루언서 협업 전략',
    ],
  },
  {
    id: 'doyun',
    name: '도윤',
    role: 'SEO 전문가',
    department: '콘텐츠 & 그로스',
    departmentColor: DEPARTMENTS.growth.color,
    emoji: '📈',
    status: 'offline',
    personality: '키워드에 진심인 조용한 승부사. 검색 1페이지가 전부.',
    currentTask: '키워드 리서치',
    currentProject: '검색 순위 개선',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['키워드 분석', '검색 최적화', 'ASO', '메타태그'],
    recentDeliverables: [
      'SEO 최적화 가이드',
      '키워드 전략 보고서',
      '백링크 구축 계획',
    ],
  },
  // ─── 보안 & 품질 ────────────────────────────
  {
    id: 'taehyun',
    name: '태현',
    role: '보안 담당자',
    department: '보안 & 품질',
    departmentColor: DEPARTMENTS.security_qa.color,
    emoji: '🔍',
    status: 'offline',
    personality: '편집증적 보안 감시자. 모든 것을 의심하고, API 키 하나도 놓치지 않음.',
    currentTask: '보안 취약점 스캔',
    currentProject: '인프라 보안 강화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['보안 모니터링', '취약점 스캔', 'API 키 관리', 'OWASP 점검'],
    recentDeliverables: [
      '보안 점검 보고서',
      'API 보안 가이드',
      '침투 테스트 결과',
    ],
  },
  {
    id: 'chaewon',
    name: '채원',
    role: 'QA 엔지니어',
    department: '보안 & 품질',
    departmentColor: DEPARTMENTS.security_qa.color,
    emoji: '🔍',
    status: 'offline',
    personality: '꼼꼼함의 끝판왕. 버그를 발견하면 진심으로 기뻐함.',
    currentTask: '테스트 케이스 작성',
    currentProject: '품질 보증 프로세스',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['테스트 케이스 실행', '품질 검수', '회귀 테스트', 'QA 체크리스트'],
    recentDeliverables: [
      '테스트 계획서',
      '자동화 테스트 스위트',
      '품질 지표 리포트',
    ],
  },
  // ─── 분석 & 리서치 ──────────────────────────
  {
    id: 'jieun',
    name: '지은',
    role: '회계사',
    department: '분석 & 리서치',
    departmentColor: DEPARTMENTS.analytics.color,
    emoji: '🧮',
    status: 'offline',
    personality: '숫자에 진심인 꼼꼼한 금고지기. 1원 단위까지 추적.',
    currentTask: 'API 비용 정산',
    currentProject: '비용 최적화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['수입/지출 관리', '비용 분석', '예산 수립', '재무 리포트'],
    recentDeliverables: [
      '월간 비용 정산서',
      'API 사용량 비용 환산표',
      '예산 대비 지출 리포트',
    ],
  },
  {
    id: 'soyul',
    name: '소율',
    role: 'BI 전문가',
    department: '분석 & 리서치',
    departmentColor: DEPARTMENTS.analytics.color,
    emoji: '🧮',
    status: 'offline',
    personality: '차분하고 분석적. 숫자가 거짓말을 하진 않는다는 신조.',
    currentTask: '대시보드 구축',
    currentProject: 'BI 시스템 고도화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['대시보드 제작', '매출 분석', 'LTV 계산', '코호트 분석'],
    recentDeliverables: [
      '경영진 대시보드',
      '매출 분석 리포트',
      'KPI 추적 시스템',
    ],
  },
  {
    id: 'yuna',
    name: '유나',
    role: '시장조사 전문가',
    department: '분석 & 리서치',
    departmentColor: DEPARTMENTS.analytics.color,
    emoji: '🧮',
    status: 'offline',
    personality: '호기심 많은 탐험가 기질. 경쟁사의 모든 움직임을 추적.',
    currentTask: '소비자 트렌드 조사',
    currentProject: '2026 시장 분석',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['트렌드 분석', '경쟁사 조사', '시장 기회 발굴', '벤치마킹'],
    recentDeliverables: [
      '펫테크 시장 리포트',
      '소비자 인사이트 조사',
      '경쟁사 벤치마킹',
    ],
  },
  // ─── 고객 경험 ──────────────────────────────
  {
    id: 'daeun',
    name: '다은',
    role: '고객 지원',
    department: '고객 경험',
    departmentColor: DEPARTMENTS.customer.color,
    emoji: '💬',
    status: 'offline',
    personality: '따뜻하고 공감적. 고객의 불편이 곧 우리의 기회.',
    currentTask: '고객 문의 응대',
    currentProject: 'CS 품질 개선',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['CS 응답', '불만 처리', 'FAQ 관리', '리뷰 분석'],
    recentDeliverables: [
      'CS 응대 가이드',
      '고객 만족도 분석',
      'FAQ 업데이트',
    ],
  },
  {
    id: 'jiho',
    name: '지호',
    role: '커뮤니티 매니저',
    department: '고객 경험',
    departmentColor: DEPARTMENTS.customer.color,
    emoji: '💬',
    status: 'offline',
    personality: '사교성 만점의 커뮤니티 리더. 밈과 트렌드를 잘 활용.',
    currentTask: '커뮤니티 이벤트 기획',
    currentProject: '사용자 커뮤니티 활성화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['커뮤니티 관리', '유저 소통', 'UGC 촉진', '이벤트 진행'],
    recentDeliverables: [
      '2월 커뮤니티 이벤트',
      '유저 피드백 정리',
      '커뮤니티 가이드라인',
    ],
  },
] as Omit<Employee, 'avatar'>[]).map(emp => ({
  ...emp,
  avatar: EMPLOYEE_AVATARS[emp.id] || DEFAULT_AVATAR,
})) as Employee[];

export function getRandomActivity() {
  return activities[Math.floor(Math.random() * activities.length)];
}

export function getEmployeesByDepartment(department: string) {
  return employees.filter((emp) => emp.department === department);
}

export function getDepartmentStats() {
  const stats = Object.values(DEPARTMENTS).map((dept) => {
    const deptEmployees = employees.filter((emp) => emp.department === dept.name);
    const activeCount = deptEmployees.filter(
      (emp) => emp.status === 'working' || emp.status === 'meeting'
    ).length;
    const avgContribution =
      deptEmployees.reduce((sum, emp) => sum + emp.contribution, 0) / deptEmployees.length || 0;

    return {
      ...dept,
      totalEmployees: deptEmployees.length,
      activeEmployees: activeCount,
      avgContribution: Math.round(avgContribution),
      productivity: Math.min(Math.round((avgContribution / 1000) * 100), 100),
    };
  });

  return stats;
}
