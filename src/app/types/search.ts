/**
 * Types related to recourse search
 */

/** Users query parameters */
interface UsersSearchQuery {
  q?: string
  i?: string[]
  r?: string[]
  g?: string[]
  a?: UserRoleValue[]
  s?: string
  e?: string
  k?: UsersSortableKeys
  d?: SortOrder
  p?: number
  l?: number
}

type UsersSortableKeys = 'id' | 'userName' | 'emails' | 'eppns' | 'lastModified'

type SortOrder = 'asc' | 'desc'

/** General search result structure */
interface SearchResult<T> {
  total: number
  pageSize: number
  offset: number
  resources: T[]
}

/** Repository search result structure */
type RepositoriesSearchResult = SearchResult<RepositorySummary>

/** Group search result structure */
type GroupsSearchResult = SearchResult<GroupSummary>

/** User search result structure */
type UsersSearchResult = SearchResult<UserSummary>

export type {
  UsersSearchQuery, UsersSortableKeys,
  SortOrder,
  SearchResult, UsersSearchResult, GroupsSearchResult, RepositoriesSearchResult,
}
