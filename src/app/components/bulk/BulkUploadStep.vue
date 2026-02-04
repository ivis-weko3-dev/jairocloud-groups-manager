<script setup lang="ts">
const emit = defineEmits<{
  next: []
}>()

const {
  selectedFile,
  selectedRepository,
  validateFile,
  isProcessing,
  taskId,
  tempFileId,
} = useUserUpload()

const hasFileFormatError = ref(false)
const fileFormatError = computed(() => {
  return hasFileFormatError.value ? $t('bulk.file-format-error') : undefined
})
const canProceed = computed(() => selectedFile.value !== undefined
  && selectedRepository.value !== undefined
  && !hasFileFormatError.value)

function validateFileFormat(file: File | File[] | null) {
  hasFileFormatError.value = false

  if (!file) return
  const targetFile = Array.isArray(file) ? file[0] : file
  const fileName = targetFile.name.toLowerCase()
  const allowedExtensions = ['.csv', '.tsv', '.xlsx']
  const allowedMimeTypes = [
    'text/csv',
    'text/tab-separated-values',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ]

  const hasValidExtension = allowedExtensions.some(extension => fileName.endsWith(extension))
  const hasValidMimeType = allowedMimeTypes.includes(targetFile.type)

  if (!hasValidExtension && !hasValidMimeType) {
    hasFileFormatError.value = true
  }
}

watch(selectedFile, (newFile) => {
  validateFileFormat(newFile)
})

async function handleNext() {
  if (hasFileFormatError.value || !selectedFile.value || !selectedRepository.value) return

  isProcessing.value = true

  try {
    const formData = new FormData()
    if (!selectedFile.value) {
      return
    }

    formData.append('bulk_file', selectedFile.value)
    formData.append('repository_id', selectedRepository.value)

    const { task_id, temp_file_id } = await $fetch('/api/bulk/upload-file', {
      method: 'POST',
      body: formData,
    })

    taskId.value = task_id
    tempFileId.value = temp_file_id
    await pollValidationStatus(task_id)

    await validateFile(task_id)

    emit('next')
  }
  catch {
    useToast().add({
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

async function pollValidationStatus(taskId: string) {
  const maxAttempts = 100
  const interval = 2000

  for (let index = 0; index < maxAttempts; index++) {
    const res = await $fetch(`/api/bulk/validate/status/${taskId}`)
    const st = (res.status) as string | undefined

    if (st === 'SUCCESS') return
    if (st === 'FAILURE') throw new Error(res.error ?? 'Validation task failed')

    await new Promise(r => setTimeout(r, interval))
  }

  throw new Error('Validation timeout')
}

const repositories = ref([])
const isLoadingRepositories = ref(false)

onMounted(async () => {
  isLoadingRepositories.value = true
  try {
    const data = await $fetch('/api/repositories')
    repositories.value = data.resources.map(repo => ({
      value: repo.id,
      label: repo.displayName,
    }))
  }
  catch {
    repositories.value = []
  }
  finally {
    isLoadingRepositories.value = false
  }
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
          v-model="selectedRepository"
          :items="repositories"
          :loading="isLoadingRepositories"
          :placeholder="$t('bulk.target-repository')"
          value-key="value"
          class="w-full"
        >
          <template #item-leading="{ item }">
            <UIcon name="i-lucide-folder" class="size-5" />
          </template>
        </USelectMenu>
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
          :disabled="!canProceed || isProcessing"
          @click="handleNext"
        />
      </div>
    </template>
  </UCard>
</template>
