/**
 * Types related to user-defined groups
 */

/** Member list visibility options */
type Visibility = 'public' | 'private' | 'hidden'

/** Group summary information */
interface GroupSummary {
  id: string
  displayName: string
  public: boolean
  memberListVisibility: Visibility
  usersCount: number
}

/** Group detailed information */
interface GroupDetails extends GroupSummary {
  userDefinedId?: string
  createdAt?: Date
  lastModified?: Date
}

export type { Visibility, GroupSummary, GroupDetails }
