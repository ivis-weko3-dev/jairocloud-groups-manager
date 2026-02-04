// types/history.ts
type UserSummary = {
  id: string
  user_name?: string | null
}

type RepositorySummary = {
  id: string
  display_name?: string | null
}

type GroupSummary = {
  id: string
  display_name?: string | null
}

export type DownloadHistoryData = {
  id: string
  timestamp: string
  operator: UserSummary
  public: boolean
  parent_id: string | null
  file_path: string
  file_id: string
  repositories: RepositorySummary[]
  groups: GroupSummary[]
  users: UserSummary[]
  children_count: number
}

export type UploadHistoryData = {
  id: string
  timestamp: string
  end_timestamp?: string | null
  public: boolean
  operator: UserSummary
  status: 'S' | 'F' | 'P'
  file_path: string
  file_id: string
  repositories: RepositorySummary[]
  groups: GroupSummary[]
  users: UserSummary[]
}

export interface PaginationInfo {
  page: number
  per_page: number
  total: number
}

export type DownloadApiModel = {
  download_history_data: DownloadHistoryData[]
  pagination?: PaginationInfo
  summary?: {
    total: number
    first: number
    redownload: number
  }
  sum_download?: number
  first_download?: number
  re_download?: number
}

export type UploadApiModel = {
  upload_history_data: UploadHistoryData[]
  pagination?: PaginationInfo
  summary?: {
    total: number
    success: number
    failed: number
    progress: number
  }
  sum_upload?: number
  success_upload?: number
  failed_upload?: number
  progress_upload?: number
}

export interface HistoryQueryParameters {
  tab?: string
  p?: string | number
  l?: string | number
  d?: string
  dir?: string
  s?: string
  e?: string
  o?: string | string[]
  r?: string | string[]
  g?: string | string[]
  u?: string | string[]
  i?: string | string[]
}

export type DownloadGroupItem = {
  parent: DownloadHistoryData
  children: DownloadHistoryData[]
  hasMoreChildren: boolean
  childrenLimit: number
}

export type ActionRow = DownloadGroupItem | UploadHistoryData

export interface FilterQuery {
  s: string
  e: string
  o: string[]
  r: string[]
  g: string[]
  u: string[]
}

export interface TableColumn {
  id: string
  key: string
  label: string
  sortable?: boolean
}

export interface TableConfig {
  enableExpand?: boolean
  showStatus?: boolean
}

export interface FilterOptionsResponse {
  operators?: Array<{ id: string, user_name?: string | null }>
  target_repositories?: Array<{ id: string, display_name?: string | null }>
  target_groups?: Array<{ id: string, display_name?: string | null }>
  target_users?: Array<{ id: string, user_name?: string | null }>
}

export type SelectOption = {
  label: string
  value: string
}

export interface StatusConfig {
  label: string
  color: 'success' | 'error' | 'warning'
}

export interface HistoryStats {
  sum?: number
  firstDownload?: number
  reDownload?: number
  success?: number
  error?: number
}

export interface PublicStatusUpdateRequest {
  public: boolean
}
