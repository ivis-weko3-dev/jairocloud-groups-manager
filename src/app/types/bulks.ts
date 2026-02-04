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
  message?: string
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

 interface ImportResult {
  id: string
  row?: number
  eppn: string | string[]
  userName: string
  emails: string[]
  groups: string[]
  status: StatusType
  code?: string
}

 interface ImportResultResponse {
  results: ImportResult[]
  summary: {
    total: number
    success: number
    failed: number
    create: number
    update: number
    delete: number
    skip: number
  }
  fileInfo?: {
    fileName: string
    startedAt: string
    completedAt: string
    executedBy: string
  }
}

 interface ImportResultResponse {
  results: ImportResult[]
  summary: {
    total: number
    success: number
    failed: number
    create: number
    update: number
    delete: number
    skip: number
  }
  fileInfo?: {
    fileName: string
    startedAt: string
    completedAt: string
    executedBy: string
  }
}

export type { StatusType, ValidationResult, MissingUser, UploadResult, Summary, ImportResult, ImportResultResponse }