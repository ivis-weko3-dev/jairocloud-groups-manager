<script setup lang="ts">
import { h, resolveComponent } from 'vue'

import type { TableColumn } from '@nuxt/ui'

const properties = defineProps<{
  historyId: string
}>()

const emit = defineEmits<{
  restart: []
}>()

const UBadge = resolveComponent('UBadge')
const UIcon = resolveComponent('UIcon')

const { t: $t } = useI18n()

const {
  importResult,
  fetchUploadtResult,
} = useUserUpload()

const resultPagination = ref({
  pageIndex: 0,
  pageSize: 10,
})

const selectedFilters = ref<string[]>([])

const STATUS_CONFIG: Record<string, { color: string, label: string, icon: string }> = {
  create: { color: 'success', label: $t('bulk.status.create'), icon: 'i-lucide-plus-circle' },
  update: { color: 'info', label: $t('bulk.status.update'), icon: 'i-lucide-pencil' },
  delete: { color: 'error', label: $t('bulk.status.delete'), icon: 'i-lucide-trash-2' },
  skip: { color: 'neutral', label: $t('bulk.status.skip'), icon: 'i-lucide-minus-circle' },
}

const resultColumns: TableColumn<ImportResult>[] = [
  {
    accessorKey: 'row',
    header: $t('bulk.column.row'),
    cell: ({ row }) => {
      const rowNumber = row.getValue('row')
      return rowNumber ? `${rowNumber}` : '-'
    },
    meta: { class: { td: 'w-20' } },
  },
  {
    accessorKey: 'userName',
    header: $t('bulk.column.userName'),
    cell: ({ row }) => {
      const name = row.getValue('userName') as string
      return name || h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'eppn',
    header: $t('bulk.column.eppn'),
    cell: ({ row }) => {
      const eppn = row.getValue('eppn') as string | string[]
      const eppnArray = Array.isArray(eppn) ? eppn : [eppn]
      return eppnArray && eppnArray.length > 0
        ? h('div', { class: 'flex flex-col gap-1' },
            eppnArray.map(e => h('span', { class: 'font-mono text-sm' }, e)))
        : h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'groups',
    header: $t('bulk.column.groups'),
    cell: ({ row }) => {
      const groups = row.getValue('groups') as string[]
      return groups && groups.length > 0
        ? h('div', { class: 'flex flex-col gap-1' },
            groups.map(group => h('span', { class: 'font-mono text-sm' }, group)))
        : h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'status',
    header: $t('bulk.status'),
    cell: ({ row }) => {
      const data = row.original as ImportResult
      const status = data.status
      const message = data.code

      const config = STATUS_CONFIG[status]

      if (!config) {
        return h('span', { class: 'text-muted italic' }, status || '-')
      }

      return h('div', { class: 'flex items-center gap-2' }, [
        h(UBadge, { color: config.color, variant: 'subtle', class: 'gap-1' }, () => [
          h(UIcon, { name: config.icon, class: 'size-3' }),
          config.label,
        ]),
        message
          ? h('span', { class: 'text-sm text-muted' }, message)
          : undefined,
      ].filter(Boolean))
    },
  },
]

const filteredResults = computed(() => {
  if (!importResult.value?.results) return []

  if (selectedFilters.value.length === 0) {
    return importResult.value.results
  }

  return importResult.value.results.filter((result: ImportResult) => {
    return selectedFilters.value.includes(result.status)
  })
})

const paginatedResults = computed(() => {
  const start = resultPagination.value.pageIndex * resultPagination.value.pageSize
  const end = start + resultPagination.value.pageSize
  return filteredResults.value.slice(start, end)
})

const resultSummary = computed(() => ({
  total: filteredResults.value.length,
  success: importResult.value?.summary?.success || 0,
  failed: importResult.value?.summary?.failed || 0,
  create: importResult.value?.summary?.create || 0,
  update: importResult.value?.summary?.update || 0,
  delete: importResult.value?.summary?.delete || 0,
  skip: importResult.value?.summary?.skip || 0,
}))

async function reloadResults(queryParameters?: string) {
  if (!props.historyId) return

  try {
    await fetchUploadtResult(props.historyId, queryParameters)
  }
  catch (error) {
    console.error('Failed to reload import results:', error)
  }
}

function changeResultPageSize(size: number) {
  resultPagination.value.pageSize = size
  resultPagination.value.pageIndex = 0
}

function toggleFilter(filter: string) {
  const index = selectedFilters.value.indexOf(filter)
  if (index === -1) {
    selectedFilters.value.push(filter)
  }
  else {
    selectedFilters.value.splice(index, 1)
  }
  resultPagination.value.pageIndex = 0
}

function clearFilters() {
  selectedFilters.value = []
  resultPagination.value.pageIndex = 0
}

function handleRestart() {
  emit('restart')
}

const fileInfo = computed(() => importResult.value?.fileInfo || {})
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
        :data="paginatedResults"
        :columns="resultColumns"
        :total-count="resultSummary.total"
        :page-index="resultPagination.pageIndex"
        :page-size="resultPagination.pageSize"
        :selected-filters="selectedFilters"
        :filter-options="[
          { label: $t('bulk.status.create'), value: 'create' },
          { label: $t('bulk.status.update'), value: 'update' },
          { label: $t('bulk.status.delete'), value: 'delete' },
          { label: $t('bulk.status.skip'), value: 'skip' },
          { label: $t('bulk.status.error'), value: 'error' },
        ]"
        :title="$t('bulk.import-results')"
        @update:page-index="(v) => resultPagination.pageIndex = v"
        @update:page-size="(v) => resultPagination.pageSize = v"
        @update:selected-filters="(v) => selectedFilters = v"
        @clear-filters="clearFilters"
      />
    </div>
  </UCard>
</template>
