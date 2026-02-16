<script setup lang="ts">
const { t: $t } = useI18n()

const properties = defineProps<{
  historyId: string
  taskId: string
}>()

const {
  uploadResult,
  fetchUploadResult,
} = useExecuteUpload()
const { makePageInfo } = useBulk()

const toast = useToast()

const { data: status, execute }
  = await useFetch<BulkProcessingStatus>(`/api/bulk/execute/status/${properties.taskId}`)
const { polling: { interval, maxAttempts } } = useAppConfig()
const pollExecuteStatus = async () => {
  for (let index = 0; index < maxAttempts; index++) {
    await execute()
    const st = (status.value?.status)
    if (st === 'SUCCESS') return
    if (st === 'FAILURE') {
      toast.add({
        title: $t('bulk.status.error'),
        description: $t('bulk.execute.failed'),
        color: 'error',
        icon: 'i-lucide-circle-x',
      })
      return
    }

    await new Promise(r => setTimeout(r, interval))
  }
  toast.add({
    title: $t('bulk.status.error'),
    description: $t('bulk.execute.timeout'),
    color: 'error',
    icon: 'i-lucide-circle-x',
  })
}
onMounted(async () => {
  await pollExecuteStatus()
})

uploadResult.value = await fetchUploadResult(properties.historyId)
const fileInfo = computed(() => uploadResult.value!.fileInfo)
const pageInfo = makePageInfo(uploadResult)
const resultSummary = computed(() => ({
  create: uploadResult.value!.summary.create,
  update: uploadResult.value!.summary.update,
  delete: uploadResult.value!.summary.delete,
  skip: uploadResult.value!.summary.skip,
  error: uploadResult.value!.summary.error,
}))
</script>

<template>
  <UCard>
    <div class="space-y-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <NumberIndicator
          :number="resultSummary.create" icon="i-lucide-plus-circle" color="success"
          :title="$t('bulk.status.create')"
        />
        <NumberIndicator
          :number="resultSummary.update" icon="i-lucide-pencil" color="info"
          :title="$t('bulk.status.update')"
        />
        <NumberIndicator
          :number="resultSummary.delete" icon="i-lucide-trash-2" color="error"
          :title="$t('bulk.status.delete')"
        />
        <NumberIndicator
          :number="resultSummary.skip" icon="i-lucide-minus-circle" color="warning"
          :title="$t('bulk.status.skip')"
        />
      </div>

      <UCard variant="outline">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">
              {{ $t('bulk.upload-file-info') }}
            </h3>
          </div>
        </template>

        <div class="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted">{{ $t('bulk.upload-file') }}:</span>
            <span class="font-medium">{{ fileInfo.fileName || '-' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted">{{ $t('bulk.start-at') }}:</span>
            <span class="font-medium">
              {{ fileInfo.startedAt ? new Date(fileInfo.startedAt).toLocaleString('ja-JP') : '-' }}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted">{{ $t('bulk.operator') }}:</span>
            <span class="font-medium">{{ fileInfo.executedBy || '-' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted">{{ $t('bulk.completed-at') }}:</span>
            <span class="font-medium">
              {{ fileInfo.completedAt ? new Date(fileInfo.completedAt).toLocaleString('ja-JP')
                : '-' }}
            </span>
          </div>
        </div>
      </UCard>

      <BulkUserTable
        :data="uploadResult!.results"
        :total-count="uploadResult!.total"
        :page-info="pageInfo"
        :offset="uploadResult!.offset"
        :title="$t('bulk.import-results')"
      />
    </div>
  </UCard>
</template>
