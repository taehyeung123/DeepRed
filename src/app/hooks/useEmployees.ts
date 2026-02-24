import { useMemo } from 'react'
import { employees as baseEmployees } from '../../data/employees'
import type { Employee } from '../../data/employees'
import { useAvatarStore } from './useAvatarStore'

/**
 * Returns employees with avatar configs overridden from the avatar store.
 * Use this instead of importing `employees` directly so that
 * profile-page customizations are reflected everywhere.
 */
export function useEmployees(): Employee[] {
    const { employeeAvatars } = useAvatarStore()

    return useMemo(() =>
        baseEmployees.map(emp => ({
            ...emp,
            avatar: employeeAvatars[emp.id] || emp.avatar,
        })),
        [employeeAvatars]
    )
}
