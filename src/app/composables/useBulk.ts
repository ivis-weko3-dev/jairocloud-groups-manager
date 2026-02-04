import type { ImportResultResponse, MissingUser, StatusType, ValidationResult } from "~/types/bulks"

export const useUserUpload = () => {
  const selectedFile = useState<File | undefined>('userUpload:selectedFile', () => {})
  const selectedRepository = useState<string | undefined>('userUpload:selectedRepository', () => {})
  const validationResults = useState<ValidationResult[]>('userUpload:validationResults', () => [])
  const MissingUsers = useState<MissingUser[]>('userUpload:MissingUsers', () => [])
  const selectedMissingUsers = useState<string[]>('userUpload:selectedMissingUsers', () => [])
  const temporaryFileId = useState<string | undefined>('userUpload:tempFileId', () => {})
  const summary = useState('userUpload:summary', () => ({
    total: 0,
    status: { create: 0, update: 0, delete: 0, skip: 0, error: 0 },
  }))
  const isProcessing = useState('userUpload:isProcessing', () => false)
  const taskId = useState<string | undefined>('userUpload:taskId', () => {})

  const importResult = useState<ImportResultResponse | undefined>('userUpload:importResult', () => {})

  function mapBackendOperation(backendStatus: string): StatusType {
    const operationMap: Record<string, StatusType> = {
      create: 'create',
      update: 'update',
      delete: 'delete',
      skip: 'skip',
      error: 'error',
    }
    return operationMap[backendStatus] || 'skip'
  }

  async function fetchValidationResults(taskIdValue: string, queryParameters?: string) {
    try {
      const url = queryParameters
        ? `/api/bulk/validate/result/${taskIdValue}?${queryParameters}`
        : `/api/bulk/validate/result/${taskIdValue}`

      const result = await $fetch<{
        results: Array<{
          id: string
          eppn: string[]
          emails: string[]
          userName: string
          groups: string[]
          status: string
          code: string
        }>
        summary: {
          create: number
          update: number
          delete: number
          skip: number
          error: number
        }
        missingUser: Array<{
          id: string
          eppns: string[]
          userName: string
          emails: string[]
          preferredLanguage: string
          isSystemAdmin: boolean
          repositories: Array<{
            id: string
            displayName: string
            serviceUrl: string | null
            spConnecterId: string | null
            userRoles: any | null
          }>
          groups: Array<{
            id: string
            displayName: string | null
            public: boolean | null
            memberListVisibility: string | null
            usersCount: number | null
          }>
          created: string
          lastModified: string
        }>
      }>(url)

      const parameters = new URLSearchParams(queryParameters || '')
      const pageIndex = Number.parseInt(parameters.get('p') || '0', 10)
      const pageSize = Number.parseInt(parameters.get('l') || '10', 10)

      validationResults.value = result.results.map((item, index) => {
        return {
          row: pageIndex * pageSize + index + 1,
          id: item.id,
          status: item.status,
          userName: item.userName,
          email: item.emails || '',
          eppn: item.eppn || '',
          groups: item.groups,
          code: item.code,
        }
      })

      MissingUsers.value = (result.missingUser || []).map(user => ({
        id: user.id,
        name: user.userName,
        eppn: user.eppns[0] || '',
        groups: user.groups.map(g => g.displayName || g.id),
      }))

      summary.value = {
        total: result.summary.create + result.summary.update + result.summary.delete + result.summary.skip + result.summary.error,
        status: {
          create: result.summary.create,
          update: result.summary.update,
          delete: result.summary.delete,
          skip: result.summary.skip,
          error: result.summary.error,
        },
      }

      return result
    }
    catch (error) {
      console.error('Failed to fetch validation results:', error)
      throw error
    }
  }

  async function validateFile(taskIdValue: string) {
    taskId.value = taskIdValue
    await fetchValidationResults(taskIdValue)
  }

  async function executeUpload() {
    if (!taskId.value || !selectedRepository.value) {
      throw new Error('Missing required data')
    }

    isProcessing.value = true

    try {
      const result = await $fetch<{
        history_id: string
        task_id: string
        temp_file_id?: string
      }>(`/api/bulk/execute`, {
        method: 'POST',
        body: {
          task_id: taskId.value,
          temp_file_id: temporaryFileId.value,
          repository_id: selectedRepository.value,
          delete_users: selectedMissingUsers.value,
        },
      })

      const uploadTaskId = result.task_id
      const uploadHistoryId = result.history_id

      await pollExecuteStatus(uploadTaskId)

      await fetchUploadtResult(uploadHistoryId)

      return { task_id: uploadTaskId,
        history_id: uploadHistoryId,
      }
    }
    finally {
      isProcessing.value = false
    }
  }

  async function pollExecuteStatus(uploadTaskId: string) {
    const maxAttempts = 100
    const interval = 2000

    for (let index = 0; index < maxAttempts; index++) {
      const res = await $fetch(`/api/bulk/execute/status/${uploadTaskId}`)
      const st = (res.status) as string | undefined

      if (st === 'SUCCESS') return
      if (st === 'FAILURE') throw new Error(res.error ?? 'Validation task failed')

      await new Promise(r => setTimeout(r, interval))
    }

    throw new Error('Validation timeout')
  }

  async function fetchUploadtResult(historyIdValue: string, queryParameters?: string) {
    try {
      const url = queryParameters
        ? `/api/bulk/result/${historyIdValue}?${queryParameters}`
        : `/api/bulk/result/${historyIdValue}`

      const result = await $fetch<{
        results: Array<{
          id: string
          eppn: string[]
          emails: string[]
          userName: string
          groups: string[]
          operation: string
          status: string
          message?: string
          code?: string
        }>
        summary: {
          create: number
          update: number
          delete: number
          skip: number
          error: number
        }
        fileInfo?: {
          fileName: string
          startedAt: string
          completedAt: string
          executedBy: string
        }
      }>(url)

      const parameters = new URLSearchParams(queryParameters || '')
      const pageIndex = Number.parseInt(parameters.get('p') || '0', 10)
      const pageSize = Number.parseInt(parameters.get('l') || '10', 10)

      importResult.value = {
        results: result.results.map((item, index) => ({
          id: item.id,
          row: pageIndex * pageSize + index + 1,
          eppn: item.eppn,
          emails: item.emails,
          userName: item.userName,
          groups: item.groups,
          operation: item.operation as 'create' | 'update' | 'delete' | 'skip',
          status: item.status as 'success' | 'failed',
          message: item.message,
          code: item.code,
        })),
        summary: {
          total: result.summary.create + result.summary.update + result.summary.delete + result.summary.skip + result.summary.error,
          success: result.summary.create + result.summary.update + result.summary.delete,
          failed: result.summary.error,
          create: result.summary.create,
          update: result.summary.update,
          delete: result.summary.delete,
          skip: result.summary.skip,
        },
        fileInfo: result.fileInfo,
      }

      return importResult.value
    }
    catch (error) {
      console.error('Failed to fetch import result:', error)
      throw error
    }
  }

  function resetUpload() {
    selectedFile.value = undefined
    selectedRepository.value = undefined
    validationResults.value = []
    MissingUsers.value = []
    selectedMissingUsers.value = []
    taskId.value = undefined
    importResult.value = undefined
    temporaryFileId.value = undefined
    summary.value = {
      total: 0,
      status: { create: 0, update: 0, delete: 0, skip: 0, error: 0 },
    }
  }

  return {
    selectedFile,
    selectedRepository,
    validationResults,
    MissingUsers,
    selectedMissingUsers,
    summary,
    taskId,
    tempFileId: temporaryFileId,
    isProcessing,
    importResult,
    validateFile,
    executeUpload,
    fetchValidationResults,
    fetchUploadtResult,
    resetUpload,
  }
}
