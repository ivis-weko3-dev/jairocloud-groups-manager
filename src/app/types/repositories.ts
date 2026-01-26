/**
 * Types related to repositories
 */

/** Repository summary information */
interface RepositorySummary {
  id: string
  displayName: string
  serviceURL: string
  spConnectorId?: string
}

/** Repository detailed information */
interface RepositoryDetail extends RepositorySummary {
  suspended?: boolean
  serviceId?: string
  entityId?: string
  lastModified?: Date
  usersCount?: number
  groupsCount?: number
}

export type { RepositorySummary, RepositoryDetail }
