/**
 * Types related to user information
 */

/**
 * User role definitions and values
 */
const USER_ROLES = {
  systemAdmin: 0,
  repositoryAdmin: 1,
  communityAdmin: 2,
  contributor: 3,
  generalUser: 4,
} as const

/** User role type */
type UserRole = keyof typeof USER_ROLES

type UserRoleValue = typeof USER_ROLES[keyof typeof USER_ROLES]

/** User summary information */
interface UserSummary {
  id: string
  userName: string
  role?: UserRole
  emails?: string[]
  eppns?: string[]
  lastModified?: Date
}

/** Repository affiliated with user including role */
type AffiliatedRepository = RepositorySummary & {
  userRole?: UserRoleValue
}

/** User detailed information */
interface UserDetails extends UserSummary {
  preferredLanguage?: 'en' | 'ja' | ''
  isSystemAdmin?: boolean
  repositoryRoles?: AffiliatedRepository[]
}

export { USER_ROLES }
export type { UserRole, UserRoleValue, UserSummary, UserDetails, AffiliatedRepository }
