import { useMemo } from 'react'
import { createAvatar } from '@dicebear/core'
import { avataaars } from '@dicebear/collection'
import type { AvatarConfig } from '../../../data/avatarParts'
import { DEFAULT_AVATAR } from '../../../data/avatarParts'

interface AvatarRendererProps {
    config?: AvatarConfig
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    className?: string
    bgColor?: string
}

const SIZE_MAP = {
    xs: 24,
    sm: 32,
    md: 48,
    lg: 72,
    xl: 120,
}

export function AvatarRenderer({
    config = DEFAULT_AVATAR,
    size = 'md',
    className = '',
    bgColor,
}: AvatarRendererProps) {
    const px = SIZE_MAP[size]

    const dataUri = useMemo(() => {
        const options: Record<string, any> = {
            backgroundColor: [bgColor?.replace('#', '') || 'transparent'],
            top: [config.top || 'shortFlat'],
            hairColor: [config.hairColor || '2c1b18'],
            skinColor: [config.skinColor || 'edb98a'],
            eyes: [config.eyes || 'default'],
            eyebrows: [config.eyebrows || 'defaultNatural'],
            mouth: [config.mouth || 'smile'],
            clothing: [config.clothing || 'blazerAndShirt'],
            clothesColor: [config.clothesColor || '262e33'],
            style: ['circle'],
        }

        // Facial hair
        if (config.facialHair) {
            options.facialHair = [config.facialHair]
            options.facialHairProbability = 100
            options.facialHairColor = [config.hairColor || '2c1b18']
        } else {
            options.facialHairProbability = 0
        }

        // Accessories
        if (config.accessories) {
            options.accessories = [config.accessories]
            options.accessoriesProbability = 100
        } else {
            options.accessoriesProbability = 0
        }

        const avatar = createAvatar(avataaars, options)
        return avatar.toDataUri()
    }, [config, bgColor])

    return (
        <img
            src={dataUri}
            width={px}
            height={px}
            alt="avatar"
            className={`rounded-full flex-shrink-0 ${className}`}
            style={{ width: px, height: px, minWidth: px }}
        />
    )
}
