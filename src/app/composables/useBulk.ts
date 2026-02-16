/**
 * Composable for bulk user upload operations
 */
import type { FetchError } from 'ofetch'

const toast = useToast()

const useBulk = () => {
  const currentStep = ref<'upload' | 'validate' | 'result'>('upload')

  const { t: $t } = useI18n()
  const items = computed(() => [
    {
      title: $t('bulk.step.select_file'),
      description: $t('bulk.step.select_file_description'),
      value: 'upload',
      icon: 'i-lucide-file-up',
    },
    {
      title: $t('bulk.step.validate'),
      description: $t('bulk.step.validate_description'),
      value: 'validate',
      icon: 'i-lucide-shield-check',
    },
    {
      title: $t('bulk.step.complete'),
      description: $t('bulk.step.complete_description'),
      value: 'result',
      icon: 'i-lucide-circle-check-big',
    },
  ])

  const route = useRoute()
  const query = computed<UploadQuery>(() => normalizeUploadQuery(route.query))
  const updateQuery = async (newQuery: Partial<UploadQuery>) => {
    await navigateTo({
      query: {
        ...route.query,
        ...newQuery,
      },
    })
  }
  const pageSize = ref(query.value.l)
  const pageNumber = ref(query.value.p)
  const sortOrder = ref(query.value.d)
  const makePageInfo = (result: Ref<ResultSummary | undefined>) => {
    return computed(() => {
      const start = result.value?.offset ?? 1
      const total = result.value?.total ?? 0
      const end = Math.min(start + pageSize.value!, total)
      return `${start} - ${end} / ${total}`
    })
  }

  const makeStatusFilters = () => {
    const filterOptions: { label: string, value: StatusType }[] = [
      { label: $t('bulk.status.create'), value: 'create' },
      { label: $t('bulk.status.delete'), value: 'delete' },
      { label: $t('bulk.status.error'), value: 'error' },
      { label: $t('bulk.status.skip'), value: 'skip' },
      { label: $t('bulk.status.update'), value: 'update' },
    ]

    const filters = computed(() => [
      {
        key: 'f',
        items: filterOptions ?? [],
        multiple: true,
        onUpdated: (values: unknown) => {
          const selectedValues = (values as { value: StatusType }[]).map(v => v.value)
          updateQuery({ f: selectedValues.map(String), p: 1 })
        },
      },
    ])
    return filters
  }

  return {
    query,
    currentStep,
    items,
    pageSize,
    pageNumber,
    sortOrder,
    makePageInfo,
    updateQuery,
    makeStatusFilters,
  }
}

const useUserUpload = () => {
  const selectedFile = ref<File | undefined>(undefined)
  const isProcessing = ref<boolean>(false)

  return {
    selectedFile,
    isProcessing,
  }
}

const useValidation = ({ taskId, selectedRepository }: { taskId: Ref<string | undefined>
  selectedRepository: Ref<string | undefined> }) => {
  const { query } = useBulk()
  const validationResults = ref<ValidationResult[]>([])
  const missingUsers = ref<MissingUser[]>([])

  const selectedMissingUsers = useState<Record<string, boolean>>(
    `selection-missing-users:${taskId}`, () => ({}),
  )

  /** Number of selected groups */
  const selectedCount = computed(() => {
    return Object.values(selectedMissingUsers.value).filter(value => value === true).length
  })
  const toggleSelection = (userId: string) => {
    selectedMissingUsers.value[userId] = !selectedMissingUsers.value[userId]
  }
  const temporaryFileId = ref<string | undefined>(undefined)
  const summary = ref({
    total: 0, create: 0, update: 0, delete: 0, skip: 0, error: 0,
  })

  const { handleFetchError } = useErrorHandling()
  const executeBulkUpdate = async () => {
    if (!taskId || !selectedRepository.value) {
      throw new Error('Missing required data')
    }
    try {
      const results = await $fetch<BulkProcessingStatus>(`/api/bulk/execute`, {
        method: 'POST',
        body: {
          taskId: taskId.value,
          tempFileId: temporaryFileId.value,
          repositoryId: selectedRepository.value,
          deleteUsers:
          Object.keys(selectedMissingUsers.value).filter(key => selectedMissingUsers.value[key]),
        } as ExcuteRequest,
      })
      return results
    }
    catch (error) {
      handleFetchError({ response: (error as FetchError).response! })
      return { taskId: undefined, historyId: undefined }
    }
  }

  return {
    query,
    validationResults,
    missingUsers,
    selectedMissingUsers,
    selectedCount,
    summary,
    taskId,
    temporaryFileId,
    executeBulkUpdate,
    toggleSelection,
  }
}

const useExecuteUpload = () => {
  const { query } = useBulk()
  const uploadResult = ref<ResultSummary | undefined>(undefined)
  const { handleFetchError } = useErrorHandling()
  const fetchUploadResult = async (historyId: string) => {
    const url = `/api/bulk/result/${historyId}`

    const { data } = await useFetch<ResultSummary>(url, {
      method: 'GET',
      query,
      lazy: true,
      server: false,
      onResponseError({ response }) {
        switch (response.status) {
          case 400: { {
            toast.add({
              title: $t('bulk.status.error'),
              description: $t('bulk.execute.result_failed'),
              color: 'error',
              icon: 'i-lucide-circle-x',
            }) }
          break
          }
          default:{
            handleFetchError({ response })
            break
          }
        }
      },

    })
    return data.value
  }

  return {
    uploadResult,
    fetchUploadResult,
  }
}
export { useBulk, useUserUpload, useValidation, useExecuteUpload }
