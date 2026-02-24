import { useSyncExternalStore, useCallback, useEffect, useRef } from 'react'
import type { AvatarConfig } from '../../data/avatarParts'
import { DEFAULT_AVATAR, EMPLOYEE_AVATARS } from '../../data/avatarParts'

const STORAGE_KEY = 'deepred-avatars'
const STORE_VERSION = 2
const API_BASE = import.meta.env.VITE_API_URL || ''

interface AvatarStore {
    version: number
    ceo: AvatarConfig
    ceoName: string
    employees: Record<string, AvatarConfig>
}

function isValidConfig(cfg: any): cfg is AvatarConfig {
    return cfg && typeof cfg.top === 'string' && typeof cfg.clothing === 'string'
}

// ─── Singleton External Store (모든 컴포넌트가 같은 인스턴스 공유) ───
let _store: AvatarStore = loadFromLocal()
let _listeners: Set<() => void> = new Set()
let _serverLoaded = false

function loadFromLocal(): AvatarStore {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
            const parsed = JSON.parse(raw)
            if (parsed.version === STORE_VERSION && isValidConfig(parsed.ceo)) {
                return parsed
            }
        }
    } catch { }
    return {
        version: STORE_VERSION,
        ceo: DEFAULT_AVATAR,
        ceoName: '대표',
        employees: { ...EMPLOYEE_AVATARS },
    }
}

function saveToLocal(store: AvatarStore) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
    } catch { /* storage full */ }
}

function syncToServer(store: AvatarStore) {
    fetch(`${API_BASE}/api/avatars`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ceo: store.ceo,
            ceoName: store.ceoName,
            employees: store.employees,
        }),
    }).catch(() => { /* silent */ })
}

function emitChange() {
    _listeners.forEach(l => l())
}

function subscribe(listener: () => void) {
    _listeners.add(listener)
    return () => { _listeners.delete(listener) }
}

function getSnapshot(): AvatarStore {
    return _store
}

function updateStore(updater: (prev: AvatarStore) => AvatarStore) {
    _store = updater(_store)
    saveToLocal(_store)
    if (_serverLoaded) syncToServer(_store)
    emitChange()
}

// Load from server once on first import
fetch(`${API_BASE}/api/avatars`)
    .then(res => res.json())
    .then(data => {
        if (data && (isValidConfig(data.ceo) || Object.keys(data.employees || {}).length > 0)) {
            _store = {
                version: STORE_VERSION,
                ceo: isValidConfig(data.ceo) ? data.ceo : _store.ceo,
                ceoName: data.ceoName || _store.ceoName,
                employees: {
                    ...EMPLOYEE_AVATARS,
                    ..._store.employees,
                    ...(data.employees || {}),
                },
            }
            saveToLocal(_store)
            emitChange()
        }
        _serverLoaded = true
    })
    .catch(() => { _serverLoaded = true })


// ─── Hook (모든 컴포넌트에서 같은 상태 공유) ───
export function useAvatarStore() {
    const store = useSyncExternalStore(subscribe, getSnapshot)

    const setCeoAvatar = useCallback((avatar: AvatarConfig) => {
        updateStore(prev => ({ ...prev, ceo: avatar }))
    }, [])

    const setCeoName = useCallback((name: string) => {
        updateStore(prev => ({ ...prev, ceoName: name }))
    }, [])

    const setEmployeeAvatar = useCallback((employeeId: string, avatar: AvatarConfig) => {
        updateStore(prev => ({
            ...prev,
            employees: { ...prev.employees, [employeeId]: avatar },
        }))
    }, [])

    const getEmployeeAvatar = useCallback((employeeId: string): AvatarConfig => {
        return store.employees[employeeId] || EMPLOYEE_AVATARS[employeeId] || DEFAULT_AVATAR
    }, [store.employees])

    return {
        ceoAvatar: store.ceo,
        ceoName: store.ceoName,
        setCeoAvatar,
        setCeoName,
        setEmployeeAvatar,
        getEmployeeAvatar,
        employeeAvatars: store.employees,
    }
}
