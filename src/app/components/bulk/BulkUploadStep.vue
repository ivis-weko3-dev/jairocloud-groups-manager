<script setup lang="ts">
const { t: $t } = useI18n()
const emit = defineEmits<{
  next: [taskId: string]
}>()

const {
  selectedFile,
  isProcessing,
} = useUserUpload()
const { table: { pageSize } } = useAppConfig()
const selectedRepository = inject<Ref<string | undefined>>('selectedRepository', ref(undefined))
const hasFileFormatError = ref(false)
const fileFormatError = computed(() => {
  return hasFileFormatError.value ? $t('bulk.file-format-error') : undefined
})

const validateFileFormat = (file: File | undefined) => {
  hasFileFormatError.value = false

  if (!file) return
  const fileName = file.name.toLowerCase()
  const allowedExtensions = ['.csv', '.tsv', '.xlsx']
  const allowedMimeTypes = [
    'text/csv',
    'text/tab-separated-values',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ]

  const hasValidExtension = allowedExtensions.some(extension => fileName.endsWith(extension))
  const hasValidMimeType = allowedMimeTypes.includes(file.type)

  if (!hasValidExtension && !hasValidMimeType) {
    hasFileFormatError.value = true
  }
}

watch(selectedFile, (newFile) => {
  validateFileFormat(newFile)
})
const toast = useToast()
const { handleFetchError } = useErrorHandling()
const handleNext = async () => {
  if (hasFileFormatError.value || !selectedFile.value || !selectedRepository.value) return

  isProcessing.value = true

  const formData = new FormData()
  if (!selectedFile.value) {
    return
  }

  formData.append('bulk_file', selectedFile.value)
  formData.append('repository_id', selectedRepository.value)

  const { data } = useFetch<BulkProcessingStatus>('/api/bulk/upload-file', {
    method: 'POST',
    body: formData,
    onResponseError({ response }) {
      handleFetchError({ response })
    },
    lazy: true,
    server: false,
  })
  try {
    const { taskId } = data.value!

    emit('next', taskId)
  }
  catch {
    toast.add({
      title: $t('bulk.status.error'),
      description: $t('bulk.file-validate-error'),
      color: 'error',
      icon: 'i-lucide-circle-x',
    })
  }
  finally {
    isProcessing.value = false
  }
}

const repositorySelect = useTemplateRef('repositorySelect')
const {
  items: repositoryNames,
  searchTerm: repoSearchTerm,
  status: repoSearchStatus,
  onOpen: onRepoOpen,
  setupInfiniteScroll: setupRepoScroll,
} = useSelectMenuInfiniteScroll<RepositorySummary>({
  url: '/api/repositories',
  limit: pageSize.repositories[0],
  transform: (repository: RepositorySummary) => ({
    label: repository.serviceName,
    value: repository.id,
  }),
})
setupRepoScroll(repositorySelect)

const canProceed = computed(() => {
  if (selectedFile.value == undefined)
    return false
  if (selectedRepository.value == undefined)
    return false
  return !hasFileFormatError.value
})
</script>

<template>
  <UCard>
    <div class="space-y-4">
      <UAlert
        icon="i-lucide-info"
        color="warning"
        variant="subtle"
        :title="$t('bulk.about')"
        :ui="{
          title: 'text-black',
          description: 'text-black',
        }"
      >
        <template #description>
          <ul class="list-disc list-inside space-y-1 text-sm">
            <li>{{ $t('bulk.about-description') }}</li>
            <li>{{ $t('bulk.about-description2') }}</li>
            <li>{{ $t('bulk.about-description3') }}</li>
            <li>{{ $t('bulk.about-description4') }}</li>
          </ul>
        </template>
      </UAlert>

      <UFormField
        :label="$t('bulk.select-repository')"
        name="repository"
      >
        <USelectMenu
          ref="repositorySelect"
          v-model="selectedRepository"
          :search-term="repoSearchTerm" value-key="value" size="xl"
          :placeholder="$t('group.placeholder.repository')"
          :items="repositoryNames" :loading="repoSearchStatus === 'pending'" ignore-filter
          :ui="{ base: 'w-full' }"
          @update:open="onRepoOpen"
        />
      </UFormField>

      <UFormField
        :label="$t('bulk.upload-file')"
        name="file"
        :error="fileFormatError"
      >
        <UFileUpload
          v-model="selectedFile"
          accept=".csv,.tsv,.xlsx,text/csv,text/tab-separated-values,application/vnd.ms-excel,
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          :label="$t('bulk.upload-field')"
          description="TSV, CSV, Excel"
          icon="i-lucide-file-up"
          layout="list"
          position="inside"
          color="primary"
        />
      </UFormField>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <UButton
          :label="$t('button.next')"
          icon="i-lucide-arrow-right"
          trailing
          :loading="isProcessing"
          :disabled="!canProceed"
          @click="handleNext"
        />
      </div>
    </template>
  </UCard>
</template>
