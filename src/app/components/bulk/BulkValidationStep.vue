<script setup lang="ts">
import { h, resolveComponent } from 'vue'

import type { TableColumn } from '@nuxt/ui'

const emit = defineEmits<{
  next: [taskId: string]
  prev: []
}>()

const UBadge = resolveComponent('UBadge')
const UCheckbox = resolveComponent('UCheckbox')
const UIcon = resolveComponent('UIcon')

const { t: $t } = useI18n()

const {
  validationResults,
  MissingUsers,
  selectedMissingUsers,
  summary,
  executeUpload,
  isProcessing,
  taskId,
  fetchValidationResults,
} = useUserUpload()

onMounted(async () => {
  if (!taskId.value) {
    emit('prev')
    return
  }

  await loadValidationResults()
})

const pagination = ref({
  pageIndex: 0,
  pageSize: 10,
})

const selectedFilters = ref<StatusType[]>([])

const FILTER_MAP: Record<string, StatusType> = {
  create: 'create',
  update: 'update',
  delete: 'delete',
  skip: 'skip',
  error: 'error',
}

const STATUS_TO_NUMBER: Record<StatusType, number> = {
  create: 0,
  delete: 1,
  error: 2,
  skip: 3,
  update: 4,
}

const STATUS_CONFIG: Record<StatusType, { color: string, label: string, icon: string }> = {
  create: { color: 'success', label: $t('bulk.status.create'), icon: 'i-lucide-plus-circle' },
  update: { color: 'info', label: $t('bulk.status.update'), icon: 'i-lucide-pencil' },
  delete: { color: 'error', label: $t('bulk.status.delete'), icon: 'i-lucide-trash-2' },
  skip: { color: 'neutral', label: $t('bulk.status.skip'), icon: 'i-lucide-minus-circle' },
  error: { color: 'error', label: $t('bulk.status.error'), icon: 'i-lucide-circle-x' },
}

const columns: TableColumn<ValidationResult>[] = [
  {
    accessorKey: 'row',
    header: '行',
    cell: ({ row }) => `${row.getValue('row')}`,
    meta: { class: { td: 'w-20' } },
  },
  {
    accessorKey: 'userName',
    header: '名前',
    cell: ({ row }) => {
      const name = row.getValue('userName') as string
      return name || h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'email',
    header: 'email',
    cell: ({ row }) => {
      const email = row.getValue('email') as string[]
      return email && email.length > 0
        ? h('div', { class: 'flex flex-col gap-1' },
            email.map(email => h('span', { class: 'font-mono text-sm' }, email)))
        : h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'eppn',
    header: 'eppn',
    cell: ({ row }) => {
      const eppn = row.getValue('eppn') as string[]
      return eppn && eppn.length > 0
        ? h('div', { class: 'flex flex-col gap-1' },
            eppn.map(eppn => h('span', { class: 'font-mono text-sm' }, eppn)))
        : h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    accessorKey: 'groups',
    header: 'グループ',
    cell: ({ row }) => {
      const groups = row.getValue('groups') as string[]
      return groups && groups.length > 0
        ? h('div', { class: 'flex flex-col gap-1' },
            groups.map(group => h('span', { class: 'font-mono text-sm' }, group)))
        : h('span', { class: 'text-muted italic' }, $t('bulk.empty'))
    },
  },
  {
    id: 'statusColumn',
    header: 'ステータス',
    cell: ({ row }) => {
      const data = row.original as ValidationResult
      const status = data.status
      const messageCode = data.code

      const config = STATUS_CONFIG[status]

      const translatedMessage = messageCode
        ? ($t(`bulk.codes.${messageCode}`, messageCode) as string)
        : undefined

      return h('div', { class: 'flex items-center gap-2' }, [
        h(UBadge, { color: config.color, variant: 'subtle', class: 'gap-1' }, () => [
          h(UIcon, { name: config.icon, class: 'size-3' }),
          config.label,
        ]),
        translatedMessage
          ? h('span', { class: 'text-sm text-muted' }, translatedMessage)
          : undefined,
      ].filter(Boolean))
    },
  },
]

async function loadValidationResults() {
  if (!taskId.value) return

  try {
    const parameters = new URLSearchParams()

    if (selectedFilters.value.length > 0) {
      for (const StatusType of selectedFilters.value) {
        const statusNumber = STATUS_TO_NUMBER[StatusType]
        parameters.append('f', statusNumber.toString())
      }
    }

    parameters.set('p', (pagination.value.pageIndex).toString())
    parameters.set('l', pagination.value.pageSize.toString())

    await fetchValidationResults(taskId.value, parameters.toString())
  }
  catch (error) {
    console.error('Failed to load validation results:', error)
    useToast().add({
      title: $t('bulk.status.error'),
      description: $t('bulk.validation.fetch_failed'),
      color: 'error',
      icon: 'i-lucide-circle-x',
    })
  }
}

function toggleFilter(filterValue: StatusType) {
  const index = selectedFilters.value.indexOf(filterValue)
  if (index === -1) {
    selectedFilters.value.push(filterValue)
  }
  else {
    selectedFilters.value.splice(index, 1)
  }

  pagination.value.pageIndex = 0
  loadValidationResults()
}

function selectAllFilters() {
  selectedFilters.value = []
  pagination.value.pageIndex = 0
  loadValidationResults()
}

watch([() => pagination.value.pageIndex, () => pagination.value.pageSize], () => {
  loadValidationResults()
})

const canProceed = computed(() => summary.value.status.error === 0)

async function handleNext() {
  if (!canProceed.value) return

  isProcessing.value = true

  try {
    const result = await executeUpload()
    const uploadHistoryId = result?.history_id

    if (uploadHistoryId) {
      emit('next', uploadHistoryId)
    }
  }
  catch (error) {
    console.error('Import error:', error)
    useToast().add({
      title: $t('bulk.status.error'),
      description: $t('bulk.import.failed'),
      color: 'error',
      icon: 'i-lucide-circle-x',
    })
  }
  finally {
    isProcessing.value = false
  }
}

function handlePrevious() {
  emit('prev')
}

function changePageSize(size: number) {
  pagination.value.pageSize = size
  pagination.value.pageIndex = 0
}

function selectAllMissingUsers() {
  selectedMissingUsers.value = MissingUsers.value
}

function deselectAllMissingUsers() {
  selectedMissingUsers.value = []
}

function toggleMissingUser(userId: string) {
  const index = selectedMissingUsers.value.indexOf(userId)
  if (index === -1) {
    selectedMissingUsers.value.push(userId)
  }
  else {
    selectedMissingUsers.value.splice(index, 1)
  }
}

const totalCount = computed(() => summary.value.total)
</script>

<template>
  <UCard>
    <div class="space-y-4">
      <UAlert
        v-if="summary.status.error > 0"
        color="error"
        icon="i-lucide-alert-circle"
        title="エラーが見つかりました"
        description="$t('bulk.validation.error')"
      />

      <div class="sticky top-0 z-10 bg-background">
        <div
          class="flex items-center justify-between gap-4 p-4 rounded-lg border border-default
        bg-background shadow-sm"
        >
          <NumberIndicator
            :title="$t('bulk.status.create')" icon="i-lucide-plus-circle"
            :number="summary.status.create ?? 0" color="success"
          />
          <NumberIndicator
            :title="$t('bulk.status.update')" icon="i-lucide-pencil"
            :number="summary.status.update ?? 0" color="info"
          />
          <NumberIndicator
            :title="$t('bulk.status.delete')" icon="i-lucide-trash-2"
            :number="summary.status.delete ?? 0" color="error"
          />
          <NumberIndicator
            :title="$t('bulk.status.skip')" icon="i-lucide-minus-circle"
            :number="summary.status.skip ?? 0" color="warning"
          />
          <NumberIndicator
            :title="$t('bulk.status.error')" icon="i-lucide-circle-x"
            :number="summary.status.error ?? 0" color="error"
          />
        </div>
      </div>

      <BulkUserTable
        :data="validationResults"
        :columns="columns"
        :total-count="totalCount"
        :page-index="pagination.pageIndex"
        :page-size="pagination.pageSize"
        :selected-filters="selectedFilters"
        :filter-options="[
          { label: $t('bulk.status.create'), value: FILTER_MAP.create },
          { label: $t('bulk.status.update'), value: FILTER_MAP.update },
          { label: $t('bulk.status.delete'), value: FILTER_MAP.delete },
          { label: $t('bulk.status.skip'), value: FILTER_MAP.skip },
          { label: $t('bulk.status.error'), value: FILTER_MAP.error },
        ]"
        :title="$t('bulk.validation.results')"
        @update:page-index="(v) => pagination.pageIndex = v"
        @update:page-size="(v) => pagination.pageSize = v"
        @update:selected-filters="(v) => selectedFilters = v"
        @clear-filters="selectAllFilters"
      />

      <UCard v-if="MissingUsers.length > 0" variant="outline">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h3 class="font-semibold">
                {{ $t('bulk.missing_user') }} ({{ MissingUsers.length }}件)
              </h3>
            </div>
            <div class="flex items-center gap-2">
              <UButton
                :label="$t('bulk.select_all')"
                size="xs"
                color="neutral"
                variant="outline"
                @click="selectAllMissingUsers"
              />
              <UButton
                :label="$t('bulk.deselect_all')"
                size="xs"
                color="neutral"
                variant="outline"
                @click="deselectAllMissingUsers"
              />
            </div>
          </div>
          <p class="text-sm text-muted">
            {{ $t('bulk.missing-user.select') }}
          </p>
        </template>

        <UAlert
          v-if="selectedMissingUsers.length > 0"
          color="error"
          icon="i-lucide-alert-triangle"
          :title="$t('bulk.missing-user.confirm')"
          :description="$t('bulk.missing-user.confirm_desc',
                           { count: selectedMissingUsers.length })"
          class="mb-4"
          variant="solid"
        />

        <div class="space-y-2">
          <div
            v-for="user in MissingUsers"
            :key="user.id"
            class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer
              hover:bg-elevated/50 transition-colors"
            :class="selectedMissingUsers.includes(user.id)
              ? 'border-error bg-error/5' : 'border-default'"
            @click="toggleMissingUser(user.id)"
          >
            <UCheckbox
              :model-value="selectedMissingUsers.includes(user.id)"
              @click.stop
              @update:model-value="toggleMissingUser(user.id)"
            />
            <div class="flex-1">
              <p class="font-medium">
                {{ user.name }}
              </p>
              <p class="text-sm text-muted font-mono">
                {{ user.eppn }}
              </p>
            </div>
            <div class="flex flex-col text-sm">
              <div v-for="group in user.groups" :key="group">
                <span class="font-mono text-sm">{{ group }}</span>
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </div>

    <template #footer>
      <div class="flex justify-between">
        <UButton
          :label="$t('button.back')"
          color="neutral"
          variant="outline"
          icon="i-lucide-arrow-left"
          :disabled="isProcessing"
          @click="handlePrevious"
        />
        <UButton
          :label="$t('bulk.import.execute')"
          icon="i-lucide-arrow-right"
          trailing
          :loading="isProcessing"
          :disabled="!canProceed || isProcessing"
          @click="handleNext"
        >
          <template v-if="!canProceed && summary.status.error > 0" #trailing>
            <UTooltip :text="$t('bulk.validation.fix_error')">
              <UIcon name="i-lucide-alert-circle" class="size-4" />
            </UTooltip>
          </template>
        </UButton>
      </div>
    </template>
  </UCard>
</template>
