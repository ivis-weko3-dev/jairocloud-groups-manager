type StatusType = 'create' | 'update' | 'delete' | 'skip' | 'error'

interface ValidationResult {
  row: number
  id: string
  status: StatusType
  userName: string
  eppn: string[]
  emails: string[]
  groups: string[]
  code?: string
}

interface MissingUser {
  id: string
  name: string
  eppn: string
  groups: string[]
}

interface UploadResult {
  row: number
  id: string
  status: StatusType
  name: string
  eppn: string
  emails: string
  groups: string[]
  code?: string
}

interface Summary {
  total: number
  status: {
    create: number
    update: number
    delete: number
    skip: number
    error: number
  }
}

interface UploadResultResponse {
  results: UploadResult[]
  summary: Summary
  fileInfo?: {
    fileName: string
    startedAt: string
    completedAt: string
    executedBy: string
  }
}

interface UploadResponse {
  taskId: string
  repositoryId: string
  tempFileId: string
  deleteUser: UserDetail[]
}

export type { StatusType, ValidationResult, MissingUser, UploadResult, Summary,
  UploadResultResponse, UploadResponse }
