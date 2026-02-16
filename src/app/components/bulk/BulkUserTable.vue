<script setup lang="ts" generic="T extends UploadResult | ValidationResult">
import { UBadge, UIcon } from '#components'

import type { BadgeProps, TableColumn } from '@nuxt/ui'

const properties = defineProps<{
  data: T[]
  totalCount: number
  title?: string
  pageInfo?: string
  offset?: number
}>()
const { t: $t } = useI18n()

const { updateQuery, pageNumber, pageSize, makeStatusFilters } = useBulk()
const { table: { pageSize: { bulks: pageOptions } } } = useAppConfig()
const offset = computed(() => properties.offset ?? 1)

const STATUS_CONFIG = computed<{ [key in StatusType]: BadgeProps }>(() => ({
  create: { color: 'success', label: $t('bulk.status.create'), icon: 'i-lucide-plus-circle' },
  update: { color: 'info', label: $t('bulk.status.update'), icon: 'i-lucide-pencil' },
  delete: { color: 'error', label: $t('bulk.status.delete'), icon: 'i-lucide-trash-2' },
  skip: { color: 'neutral', label: $t('bulk.status.skip'), icon: 'i-lucide-minus-circle' },
  error: { color: 'error', label: $t('bulk.status.error'), icon: 'i-lucide-circle-x' },
}))
const columns: TableColumn<T>[] = [
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
    header: $t('bulk.column.user-name'),
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
            eppnArray.map(eppns => h('span', { class: 'font-mono text-sm' }, eppns)))
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
    header: $t('bulk.column.status'),
    cell: ({ row }) => {
      const data = row.original
      const status = data.status
      const message = data.code

      const badgeConfig = STATUS_CONFIG.value[status]

      return h('div', { class: 'flex items-center gap-2' }, [
        h(UBadge, { color: badgeConfig.color, variant: 'subtle', class: 'gap-1' }, () => [
          h(UIcon, { name: badgeConfig.icon, class: 'size-3' }),
          badgeConfig.label,
        ]),
        message
          ? h('span', { class: 'text-sm text-muted' }, message)
          : undefined,
      ].filter(Boolean))
    },
  },
]
const filterSelects = makeStatusFilters()
</script>

<template>
  <div class="flex items-center justify-between mb-4">
    <div>
      <h3 class="text-lg font-semibold">
        {{ title }}
      </h3>
    </div>
    <div class="flex items-center gap-2">
      <USelectMenu
        v-for="filter in filterSelects"
        :key="filter.key"
        :items="filter.items" :multiple="filter.multiple"
        :search-input="false"
        :ui="{ base: 'w-40' }"
        :placeholder="$t('table.filter-button-label')"
        @update:model-value="filter.onUpdated"
      />
      <USelect
        v-model="pageSize" :items="pageOptions"
        class="w-24"
        @update:model-value="() => updateQuery(
          { l: pageSize, p: Math.ceil(offset / pageSize!) },
        )"
      />
    </div>
  </div>

  <UTable
    :data="data"
    :columns="columns"
    sticky
  />

  <div class="flex items-center">
    <div class="flex items-center gap-4 flex-1">
      <span class="text-sm text-muted">
        {{ pageInfo }}
      </span>
    </div>

    <UPagination
      v-model:page="pageNumber"
      :items-per-page="pageSize"
      :total="properties.totalCount"
      @update:page="(value) => updateQuery({ p: value })"
    />

    <div class="flex-1" />
  </div>
</template>
