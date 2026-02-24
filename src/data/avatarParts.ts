// ── DiceBear Avataaars Config ────────────────────────────────
// Options verified against @dicebear/avataaars schema.js

export interface AvatarConfig {
    top: string
    hairColor: string
    skinColor: string
    eyes: string
    eyebrows: string
    mouth: string
    clothing: string
    clothesColor: string
    facialHair: string
    accessories: string
}

// ── Available options per category (all values from actual schema) ──

export const TOP_OPTIONS = [
    { value: 'shortFlat', label: '짧은 머리' },
    { value: 'shortWaved', label: '웨이브 숏컷' },
    { value: 'shortCurly', label: '곱슬 숏컷' },
    { value: 'shortRound', label: '둥근 숏컷' },
    { value: 'theCaesar', label: '시저컷' },
    { value: 'theCaesarAndSidePart', label: '가르마 시저컷' },
    { value: 'sides', label: '투블럭' },
    { value: 'shaggy', label: '샤기컷' },
    { value: 'shaggyMullet', label: '멀렛' },
    { value: 'frizzle', label: '프리즐' },
    { value: 'straight01', label: '긴 생머리' },
    { value: 'straight02', label: '긴 생머리 2' },
    { value: 'straightAndStrand', label: '생머리+앞머리' },
    { value: 'bob', label: '단발' },
    { value: 'bun', label: '번헤어' },
    { value: 'curly', label: '긴 곱슬' },
    { value: 'curvy', label: '웨이브 롱' },
    { value: 'bigHair', label: '볼륨 헤어' },
    { value: 'miaWallace', label: '앞머리 롱' },
    { value: 'longButNotTooLong', label: '미디엄' },
    { value: 'fro', label: '아프로' },
    { value: 'froBand', label: '아프로+밴드' },
    { value: 'shavedSides', label: '사이드 쉐이브' },
    { value: 'dreads', label: '드레드' },
    { value: 'dreads01', label: '숏 드레드 1' },
    { value: 'dreads02', label: '숏 드레드 2' },
] as const

export const HAIR_COLOR_OPTIONS = [
    { value: '2c1b18', label: '검정' },
    { value: '4a312c', label: '다크브라운' },
    { value: '724133', label: '브라운' },
    { value: 'a55728', label: '라이트브라운' },
    { value: 'b58143', label: '카라멜' },
    { value: 'c93305', label: '오번' },
    { value: 'd6b370', label: '금발' },
    { value: 'f59797', label: '핑크' },
    { value: 'ecdcbf', label: '백금' },
    { value: 'e8e1e1', label: '실버' },
] as const

export const SKIN_COLOR_OPTIONS = [
    { value: 'ffdbb4', label: '밝은 살구' },
    { value: 'edb98a', label: '살구' },
    { value: 'f8d25c', label: '황금' },
    { value: 'fd9841', label: '꿀빛' },
    { value: 'd08b5b', label: '미디엄' },
    { value: 'ae5d29', label: '탄' },
    { value: '614335', label: '다크' },
] as const

export const EYES_OPTIONS = [
    { value: 'default', label: '기본' },
    { value: 'happy', label: '행복' },
    { value: 'side', label: '측면' },
    { value: 'squint', label: '찡긋' },
    { value: 'surprised', label: '놀람' },
    { value: 'wink', label: '윙크' },
    { value: 'winkWacky', label: '장난 윙크' },
    { value: 'hearts', label: '하트' },
    { value: 'closed', label: '감은 눈' },
    { value: 'cry', label: '울음' },
    { value: 'eyeRoll', label: '눈동자 굴림' },
    { value: 'xDizzy', label: 'X 눈' },
] as const

export const EYEBROWS_OPTIONS = [
    { value: 'defaultNatural', label: '기본' },
    { value: 'default', label: '각진' },
    { value: 'flatNatural', label: '일자' },
    { value: 'raisedExcitedNatural', label: '놀란' },
    { value: 'raisedExcited', label: '놀란 (각진)' },
    { value: 'upDownNatural', label: '비대칭' },
    { value: 'upDown', label: '비대칭 (각진)' },
    { value: 'sadConcernedNatural', label: '슬픈' },
    { value: 'sadConcerned', label: '슬픈 (각진)' },
    { value: 'angryNatural', label: '화난' },
    { value: 'angry', label: '화난 (각진)' },
    { value: 'frownNatural', label: '찡그린' },
    { value: 'unibrowNatural', label: '일자눈썹' },
] as const

export const MOUTH_OPTIONS = [
    { value: 'smile', label: '미소' },
    { value: 'default', label: '기본' },
    { value: 'twinkle', label: '반짝' },
    { value: 'serious', label: '진지' },
    { value: 'eating', label: '냠냠' },
    { value: 'tongue', label: '혀' },
    { value: 'grimace', label: '찡그림' },
    { value: 'sad', label: '슬픔' },
    { value: 'disbelief', label: '황당' },
    { value: 'concerned', label: '걱정' },
    { value: 'screamOpen', label: '비명' },
] as const

export const CLOTHING_OPTIONS = [
    { value: 'blazerAndShirt', label: '정장 셔츠' },
    { value: 'blazerAndSweater', label: '정장 스웨터' },
    { value: 'collarAndSweater', label: '칼라 스웨터' },
    { value: 'shirtCrewNeck', label: '라운드 티' },
    { value: 'shirtScoopNeck', label: '스쿱넥' },
    { value: 'shirtVNeck', label: 'V넥' },
    { value: 'hoodie', label: '후디' },
    { value: 'overall', label: '오버올' },
    { value: 'graphicShirt', label: '그래픽 티' },
] as const

export const CLOTHES_COLOR_OPTIONS = [
    { value: '262e33', label: '블랙' },
    { value: '3c4f5c', label: '차콜' },
    { value: '929598', label: '그레이' },
    { value: 'e6e6e6', label: '화이트' },
    { value: '65c9ff', label: '스카이블루' },
    { value: '5199e4', label: '블루' },
    { value: '25557c', label: '네이비' },
    { value: 'ff5c5c', label: '레드' },
    { value: 'ff488e', label: '핑크' },
    { value: 'ffafb9', label: '연핑크' },
    { value: 'a7ffc4', label: '라임' },
    { value: 'ffffb1', label: '옐로우' },
] as const

export const FACIAL_HAIR_OPTIONS = [
    { value: '', label: '없음' },
    { value: 'beardLight', label: '수염 (가벼운)' },
    { value: 'beardMedium', label: '수염 (보통)' },
    { value: 'beardMajestic', label: '덥수룩 수염' },
    { value: 'moustacheFancy', label: '콧수염 (멋진)' },
    { value: 'moustacheMagnum', label: '콧수염 (매그넘)' },
] as const

export const ACCESSORIES_OPTIONS = [
    { value: '', label: '없음' },
    { value: 'prescription01', label: '안경 1' },
    { value: 'prescription02', label: '안경 2' },
    { value: 'round', label: '둥근 안경' },
    { value: 'sunglasses', label: '선글라스' },
    { value: 'wayfarers', label: '웨이퍼러' },
    { value: 'kurt', label: '커트 안경' },
    { value: 'eyepatch', label: '안대' },
] as const

// ── Part labels for tabs ──
export const AVATAR_PART_LABELS = [
    { key: 'top', label: '헤어', icon: '💇' },
    { key: 'hairColor', label: '머리색', icon: '🎨' },
    { key: 'skinColor', label: '피부톤', icon: '🧑' },
    { key: 'eyes', label: '눈', icon: '👁️' },
    { key: 'eyebrows', label: '눈썹', icon: '🤨' },
    { key: 'mouth', label: '입', icon: '👄' },
    { key: 'clothing', label: '옷', icon: '👔' },
    { key: 'clothesColor', label: '옷 색', icon: '🎨' },
    { key: 'facialHair', label: '수염', icon: '🧔' },
    { key: 'accessories', label: '악세사리', icon: '👓' },
] as const

// ── Options lookup map ──
export const OPTIONS_MAP: Record<string, readonly { value: string; label: string }[]> = {
    top: TOP_OPTIONS,
    hairColor: HAIR_COLOR_OPTIONS,
    skinColor: SKIN_COLOR_OPTIONS,
    eyes: EYES_OPTIONS,
    eyebrows: EYEBROWS_OPTIONS,
    mouth: MOUTH_OPTIONS,
    clothing: CLOTHING_OPTIONS,
    clothesColor: CLOTHES_COLOR_OPTIONS,
    facialHair: FACIAL_HAIR_OPTIONS,
    accessories: ACCESSORIES_OPTIONS,
}

// ── Default ──
export const DEFAULT_AVATAR: AvatarConfig = {
    top: 'shortFlat',
    hairColor: '2c1b18',
    skinColor: 'edb98a',
    eyes: 'default',
    eyebrows: 'defaultNatural',
    mouth: 'smile',
    clothing: 'blazerAndShirt',
    clothesColor: '262e33',
    facialHair: '',
    accessories: '',
}

// ── Random generator ──
export function generateRandomAvatar(): AvatarConfig {
    const pick = <T extends readonly { value: string }[]>(arr: T) =>
        arr[Math.floor(Math.random() * arr.length)].value

    return {
        top: pick(TOP_OPTIONS),
        hairColor: pick(HAIR_COLOR_OPTIONS),
        skinColor: pick(SKIN_COLOR_OPTIONS),
        eyes: pick(EYES_OPTIONS),
        eyebrows: pick(EYEBROWS_OPTIONS),
        mouth: pick(MOUTH_OPTIONS),
        clothing: pick(CLOTHING_OPTIONS),
        clothesColor: pick(CLOTHES_COLOR_OPTIONS),
        facialHair: Math.random() > 0.65 ? pick(FACIAL_HAIR_OPTIONS) : '',
        accessories: Math.random() > 0.65 ? pick(ACCESSORIES_OPTIONS) : '',
    }
}

// ── Pre-built avatars for 16 employees (all unique!) ──
export const EMPLOYEE_AVATARS: Record<string, AvatarConfig> = {
    sujin: {
        top: 'straight01', hairColor: '2c1b18', skinColor: 'ffdbb4',
        eyes: 'default', eyebrows: 'defaultNatural', mouth: 'smile',
        clothing: 'blazerAndShirt', clothesColor: '262e33',
        facialHair: '', accessories: '',
    },
    minsu: {
        top: 'shortFlat', hairColor: '2c1b18', skinColor: 'edb98a',
        eyes: 'default', eyebrows: 'default', mouth: 'default',
        clothing: 'collarAndSweater', clothesColor: '3c4f5c',
        facialHair: '', accessories: 'prescription01',
    },
    taehyun: {
        top: 'theCaesar', hairColor: '2c1b18', skinColor: 'ffdbb4',
        eyes: 'squint', eyebrows: 'flatNatural', mouth: 'serious',
        clothing: 'blazerAndSweater', clothesColor: '25557c',
        facialHair: '', accessories: '',
    },
    seoyun: {
        top: 'curvy', hairColor: '724133', skinColor: 'ffdbb4',
        eyes: 'happy', eyebrows: 'raisedExcitedNatural', mouth: 'twinkle',
        clothing: 'shirtScoopNeck', clothesColor: 'ff488e',
        facialHair: '', accessories: '',
    },
    hajun: {
        top: 'shortWaved', hairColor: '4a312c', skinColor: 'edb98a',
        eyes: 'default', eyebrows: 'defaultNatural', mouth: 'smile',
        clothing: 'shirtCrewNeck', clothesColor: '65c9ff',
        facialHair: '', accessories: '',
    },
    eunseo: {
        top: 'bun', hairColor: '2c1b18', skinColor: 'ffdbb4',
        eyes: 'side', eyebrows: 'defaultNatural', mouth: 'smile',
        clothing: 'blazerAndShirt', clothesColor: '3c4f5c',
        facialHair: '', accessories: 'round',
    },
    jiyeon: {
        top: 'bob', hairColor: '4a312c', skinColor: 'edb98a',
        eyes: 'happy', eyebrows: 'flatNatural', mouth: 'twinkle',
        clothing: 'collarAndSweater', clothesColor: 'ff5c5c',
        facialHair: '', accessories: '',
    },
    doyun: {
        top: 'shortCurly', hairColor: '2c1b18', skinColor: 'd08b5b',
        eyes: 'default', eyebrows: 'default', mouth: 'default',
        clothing: 'hoodie', clothesColor: '5199e4',
        facialHair: 'beardLight', accessories: '',
    },
    siwoo: {
        top: 'theCaesarAndSidePart', hairColor: '4a312c', skinColor: 'edb98a',
        eyes: 'wink', eyebrows: 'raisedExcitedNatural', mouth: 'smile',
        clothing: 'blazerAndShirt', clothesColor: '262e33',
        facialHair: '', accessories: 'wayfarers',
    },
    junseo: {
        top: 'sides', hairColor: '2c1b18', skinColor: 'ffdbb4',
        eyes: 'default', eyebrows: 'defaultNatural', mouth: 'serious',
        clothing: 'shirtVNeck', clothesColor: '929598',
        facialHair: 'moustacheFancy', accessories: '',
    },
    chaewon: {
        top: 'miaWallace', hairColor: '724133', skinColor: 'ffdbb4',
        eyes: 'default', eyebrows: 'defaultNatural', mouth: 'smile',
        clothing: 'shirtCrewNeck', clothesColor: 'a7ffc4',
        facialHair: '', accessories: '',
    },
    yejun: {
        top: 'frizzle', hairColor: 'a55728', skinColor: 'edb98a',
        eyes: 'surprised', eyebrows: 'upDownNatural', mouth: 'eating',
        clothing: 'graphicShirt', clothesColor: '65c9ff',
        facialHair: '', accessories: 'prescription02',
    },
    soyul: {
        top: 'curly', hairColor: 'd6b370', skinColor: 'ffdbb4',
        eyes: 'happy', eyebrows: 'defaultNatural', mouth: 'twinkle',
        clothing: 'blazerAndSweater', clothesColor: 'ffafb9',
        facialHair: '', accessories: '',
    },
    yuna: {
        top: 'straight02', hairColor: '2c1b18', skinColor: 'f8d25c',
        eyes: 'side', eyebrows: 'flatNatural', mouth: 'smile',
        clothing: 'collarAndSweater', clothesColor: '5199e4',
        facialHair: '', accessories: '',
    },
    daeun: {
        top: 'bigHair', hairColor: 'c93305', skinColor: 'edb98a',
        eyes: 'default', eyebrows: 'raisedExcitedNatural', mouth: 'default',
        clothing: 'shirtScoopNeck', clothesColor: 'ffffb1',
        facialHair: '', accessories: '',
    },
    jiho: {
        top: 'dreads01', hairColor: '2c1b18', skinColor: 'ae5d29',
        eyes: 'default', eyebrows: 'defaultNatural', mouth: 'smile',
        clothing: 'hoodie', clothesColor: 'ff5c5c',
        facialHair: 'beardMedium', accessories: 'kurt',
    },
}
