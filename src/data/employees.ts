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

export const DEPARTMENTS = {
  coo: { name: 'COO실', color: '#DC143C', emoji: '🎯' },
  planning: { name: '기획팀', color: '#3b82f6', emoji: '📋' },
  security: { name: '보안팀', color: '#475569', emoji: '🛡️' },
  design: { name: '디자인팀', color: '#ec4899', emoji: '🎨' },
  content: { name: '콘텐츠팀', color: '#D97706', emoji: '✍️' },
  marketing: { name: '마케팅팀', color: '#22c55e', emoji: '📢' },
  business: { name: '사업전략팀', color: '#f97316', emoji: '💼' },
  automation: { name: '자동화팀', color: '#06b6d4', emoji: '⚙️' },
  data: { name: '데이터팀', color: '#6366f1', emoji: '📊' },
  research: { name: '시장조사팀', color: '#14b8a6', emoji: '🔬' },
  support: { name: '고객지원팀', color: '#a855f7', emoji: '🤝' },
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
  {
    id: 'sujin',
    name: '수진',
    role: 'COO (총괄이사)',
    department: 'COO실',
    departmentColor: DEPARTMENTS.coo.color,
    emoji: '🎯',
    status: 'offline',
    personality: '전략적 사고와 실행력을 겸비한 리더',
    currentTask: 'Q1 전략 브리핑 준비',
    currentProject: '2026 사업 계획',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['전략 기획', '조직 관리', '의사결정', '리더십'],
    recentDeliverables: [
      'Q1 경영 브리핑 자료',
      '부서별 KPI 설정 가이드',
      '2026 투자 계획서',
    ],
  },
  {
    id: 'minsu',
    name: '민수',
    role: '기획관',
    department: '기획팀',
    departmentColor: DEPARTMENTS.planning.color,
    emoji: '📋',
    status: 'offline',
    personality: '체계적이고 논리적인 기획 전문가',
    currentTask: '신규 서비스 기획안 작성',
    currentProject: '댕냥 앱 리뉴얼',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['서비스 기획', '요구사항 분석', '프로젝트 관리', 'UX 리서치'],
    recentDeliverables: [
      '댕냥 2.0 기획서',
      '사용자 시나리오 문서',
      'MVP 정의서',
    ],
  },
  {
    id: 'taehyun',
    name: '태현',
    role: '보안관',
    department: '보안팀',
    departmentColor: DEPARTMENTS.security.color,
    emoji: '🛡️',
    status: 'offline',
    personality: '꼼꼼하고 신중한 보안 전문가',
    currentTask: '보안 취약점 스캔',
    currentProject: '인프라 보안 강화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['보안 감사', '취약점 분석', '암호화', '인증 시스템'],
    recentDeliverables: [
      '보안 점검 보고서',
      'API 보안 가이드',
      '침투 테스트 결과',
    ],
  },
  {
    id: 'seoyun',
    name: '서윤',
    role: '디자이너',
    department: '디자인팀',
    departmentColor: DEPARTMENTS.design.color,
    emoji: '🎨',
    status: 'offline',
    personality: '감각적이고 창의적인 비주얼 디자이너',
    currentTask: '랜딩 페이지 디자인',
    currentProject: '브랜드 리뉴얼',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['UI 디자인', '브랜딩', '타이포그래피', 'Figma'],
    recentDeliverables: [
      '댕냥 디자인 시스템',
      '마케팅 배너 세트',
      '앱 아이콘 디자인',
    ],
  },
  {
    id: 'hajun',
    name: '하준',
    role: '콘텐츠 PD',
    department: '콘텐츠팀',
    departmentColor: DEPARTMENTS.content.color,
    emoji: '✍️',
    status: 'offline',
    personality: '스토리텔링에 강한 콘텐츠 크리에이터',
    currentTask: '블로그 콘텐츠 기획',
    currentProject: '콘텐츠 마케팅 캠페인',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['콘텐츠 기획', '스토리텔링', 'SEO 작성', '편집'],
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
    department: '콘텐츠팀',
    departmentColor: DEPARTMENTS.content.color,
    emoji: '✍️',
    status: 'offline',
    personality: '감성적이고 설득력 있는 글쓰기 전문가',
    currentTask: '광고 카피 작성',
    currentProject: '봄 시즌 캠페인',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['카피라이팅', '네이밍', '브랜드 보이스', '편집'],
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
    department: '마케팅팀',
    departmentColor: DEPARTMENTS.marketing.color,
    emoji: '📢',
    status: 'offline',
    personality: '트렌드에 민감한 소셜 미디어 전문가',
    currentTask: '인스타그램 콘텐츠 제작',
    currentProject: 'SNS 성장 전략',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['SNS 마케팅', '콘텐츠 제작', '커뮤니티 관리', '광고 운영'],
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
    department: '마케팅팀',
    departmentColor: DEPARTMENTS.marketing.color,
    emoji: '📢',
    status: 'offline',
    personality: '데이터 기반 마케팅 최적화 전문가',
    currentTask: '키워드 리서치',
    currentProject: '검색 순위 개선',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['SEO', '키워드 분석', 'Google Analytics', '기술 SEO'],
    recentDeliverables: [
      'SEO 최적화 가이드',
      '키워드 전략 보고서',
      '백링크 구축 계획',
    ],
  },
  {
    id: 'siwoo',
    name: '시우',
    role: '비즈니스 전략가',
    department: '사업전략팀',
    departmentColor: DEPARTMENTS.business.color,
    emoji: '💼',
    status: 'offline',
    personality: '시장을 읽는 예리한 전략가',
    currentTask: '경쟁사 분석',
    currentProject: '신규 사업 진출 전략',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['사업 전략', '시장 분석', '재무 모델링', '파트너십'],
    recentDeliverables: [
      '시장 진입 전략서',
      '경쟁 분석 보고서',
      '사업성 검토 문서',
    ],
  },
  {
    id: 'junseo',
    name: '준서',
    role: '자동화 엔지니어',
    department: '자동화팀',
    departmentColor: DEPARTMENTS.automation.color,
    emoji: '⚙️',
    status: 'offline',
    personality: '효율을 추구하는 자동화 마스터',
    currentTask: 'CI/CD 파이프라인 최적화',
    currentProject: '워크플로우 자동화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['자동화', 'DevOps', 'Python', 'Docker'],
    recentDeliverables: [
      '배포 자동화 스크립트',
      '테스트 자동화 프레임워크',
      '모니터링 대시보드',
    ],
  },
  {
    id: 'chaewon',
    name: '채원',
    role: 'QA 엔지니어',
    department: '자동화팀',
    departmentColor: DEPARTMENTS.automation.color,
    emoji: '⚙️',
    status: 'offline',
    personality: '완벽을 추구하는 품질 관리 전문가',
    currentTask: '테스트 케이스 작성',
    currentProject: '품질 보증 프로세스',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['QA', '테스트 자동화', 'Selenium', '버그 추적'],
    recentDeliverables: [
      '테스트 계획서',
      '자동화 테스트 스위트',
      '품질 지표 리포트',
    ],
  },
  {
    id: 'yejun',
    name: '예준',
    role: '데이터 분석가',
    department: '데이터팀',
    departmentColor: DEPARTMENTS.data.color,
    emoji: '📊',
    status: 'offline',
    personality: '숫자로 말하는 인사이트 발굴자',
    currentTask: '사용자 행동 분석',
    currentProject: '데이터 인사이트 리포트',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['데이터 분석', 'SQL', 'Python', '통계'],
    recentDeliverables: [
      '월간 데이터 리포트',
      'A/B 테스트 결과',
      '사용자 코호트 분석',
    ],
  },
  {
    id: 'soyul',
    name: '소율',
    role: 'BI 전문가',
    department: '데이터팀',
    departmentColor: DEPARTMENTS.data.color,
    emoji: '📊',
    status: 'offline',
    personality: '비즈니스를 데이터로 시각화하는 전문가',
    currentTask: '대시보드 구축',
    currentProject: 'BI 시스템 고도화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['BI', '데이터 시각화', 'Tableau', 'SQL'],
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
    department: '시장조사팀',
    departmentColor: DEPARTMENTS.research.color,
    emoji: '🔬',
    status: 'offline',
    personality: '시장의 흐름을 읽는 리서처',
    currentTask: '소비자 트렌드 조사',
    currentProject: '2026 시장 분석',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['시장 조사', '설문 분석', '트렌드 분석', '통계'],
    recentDeliverables: [
      '펫테크 시장 리포트',
      '소비자 인사이트 조사',
      '경쟁사 벤치마킹',
    ],
  },
  {
    id: 'daeun',
    name: '다은',
    role: '고객 지원',
    department: '고객지원팀',
    departmentColor: DEPARTMENTS.support.color,
    emoji: '🤝',
    status: 'offline',
    personality: '따뜻하고 친절한 고객 응대 전문가',
    currentTask: '고객 문의 응대',
    currentProject: 'CS 품질 개선',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['고객 응대', '문제 해결', 'CRM', '커뮤니케이션'],
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
    department: '고객지원팀',
    departmentColor: DEPARTMENTS.support.color,
    emoji: '🤝',
    status: 'offline',
    personality: '커뮤니티와 소통하는 브릿지',
    currentTask: '커뮤니티 이벤트 기획',
    currentProject: '사용자 커뮤니티 활성화',
    progress: 0,
    contribution: 0,
    accuracy: 0,
    todayTasks: 0,
    skills: ['커뮤니티 관리', '이벤트 기획', '소통', '콘텐츠 큐레이션'],
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
