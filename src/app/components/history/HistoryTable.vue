<script setup lang="ts" generic="T extends Record<string, any>">
import { computed, ref } from 'vue'

interface Properties<T> {
  data: T[]
  currentPage: number
  itemsPerPage: number
  totalItems: number
  emptyMessage?: string
  columns?: any[]
  tableConfig?: {
    enableExpand?: boolean
    showStatus?: boolean
  }
  ttlCheck?: (iso: string) => boolean
}

const properties = withDefaults(defineProps<Properties<T>>(), {
  emptyMessage: 'データがありません',
  columns: () => [],
  tableConfig: () => ({ enableExpand: true, showStatus: false }),
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
  'update:itemsPerPage': [items: number]
  'action': [action: string, row: T]
  'sortChange': [payload?: any]
  'loadMoreChildren': [parentId: string, currentShown: number]
}>()

const slots = defineSlots<{
  table?: (properties_: {
    data: T[]
    expandedRows: Set<string>
    toggleExpand: (id: string) => void
  }) => any
}>()

const expandedRows = ref<Set<string>>(new Set())
function toggleExpand(id: string) {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
  }
  else {
    expandedRows.value.add(id)
  }
}

const columns = computed(() => {
  if (properties.columns && properties.columns.length > 0) {
    return properties.columns
  }

  const base = [
    {
      id: 'timestamp',
      key: 'timestamp',
      label: $t('history.operation-date'),
      sortable: true,
    },
    {
      id: 'operator',
      key: 'operator',
      label: $t('history.operator'),
    },
    { id: 'users', key: 'users', label: $t('history.user-count') },
    { id: 'groups', key: 'groups', label: $t('history.group-count') },
  ]

  if (properties.tableConfig.enableExpand) {
    base.push({ id: 'redownload', key: 'redownload', label: $t('history.re-download') })
  }

  base.push({ id: 'actions', key: 'actions', label: '' })
  return base
})

const tableRows = computed(() => {
  const first = (properties.data as any[])[0]
  const looksLikeGroup = first && typeof first === 'object'
    && 'parent' in first && 'children' in first

  if (looksLikeGroup) {
    return (properties.data as any[]).map((item: any) => {
      const base = {
        ...item.parent,
        _children: item.children ?? [],
        _hasMore: !!item.has_more_children,
        childrenCount: item.parent?.children_count ?? (item.children?.length ?? 0),
      }
      return {
        ...base,
        isDisabled: typeof properties.ttlCheck === 'function'
          ? !properties.ttlCheck(base.timestamp)
          : false,
      }
    })
  }
  return (properties.data as any[]).map((r: any) => ({
    ...r,
    isDisabled: typeof properties.ttlCheck === 'function'
      ? !properties.ttlCheck(r.timestamp)
      : false,
  }))
})

const pageStart = computed(() => properties.totalItems === 0
  ? 0
  : (properties.currentPage - 1) * properties.itemsPerPage + 1)

const pageEnd = computed(() => Math.min(
  properties.currentPage * properties.itemsPerPage,
  properties.totalItems,
))

const itemsPerPageOptions = [10, 25, 50, 100].map(v => ({ label: String(v), value: v }))

const statusConfig: Record<string, { label: string, color: 'success' | 'error' | 'warning' }> = {
  S: { label: $t('history.succes'), color: 'success' },
  F: { label: $t('history.failed'), color: 'error' },
  P: { label: $t('history.progress'), color: 'warning' },
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('ja-JP', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <UCard variant="outline" :ui="{ body: { padding: 'p-0' } }">
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">
          {{ $t('history.table-title') }}
        </h2>
        <div class="flex items-center gap-2">
          <span class="text-sm text-muted">{{ $t('history.view') }}:</span>
          <USelectMenu
            :model-value="properties.itemsPerPage"
            :items="itemsPerPageOptions"
            value-key="value"
            class="w-24"
            @update:model-value="(v) => $emit('update:itemsPerPage', v.value)"
          />
        </div>
      </div>
    </template>
    <slot
      v-if="slots.table"
      name="table"
      :data="properties.data"
      :expanded-rows="expandedRows"
      :toggle-expand="toggleExpand"
    />

    <UTable
      v-else
      :key="`ut-${properties.tableConfig.enableExpand?'d':'u'}-${properties.currentPage}
      -${properties.itemsPerPage}`"
      :rows="[...tableRows]"
      :columns="[...columns]"
      row-key="id"
      :loading="false"
      @sort="(s) => emit('sortChange', s)"
    >
      <template #empty>
        <UEmpty
          icon="i-lucide-search-x"
          :title="properties.emptyMessage"
        />
      </template>

      <template #timestamp-data="{ row }">
        <div class="flex items-center gap-2">
          <UIcon
            v-if="row._matchedFields?.length"
            name="i-lucide-search-check"
            class="text-success"
          />
          <span :class="{ 'text-success font-bold': row._matchedFields?.includes('date') }">
            {{ formatDate(row.timestamp) }}
          </span>
        </div>
      </template>

      <template #operator-data="{ row }">
        <div class="flex items-center gap-2">
          <span>{{ row.operator?.user_name }}</span>
          <UBadge
            v-if="row.childrenCount > 0"
            :label="`+${row.childrenCount}`"
            size="xs"
            color="neutral"
            variant="subtle"
          />
        </div>
      </template>

      <template #users-data="{ row }">
        <UPopover mode="hover">
          <UButton
            color="neutral"
            variant="ghost"
            size="xs"
            :label="`${row.users?.length ?? 0}人`"
            trailing-icon="i-lucide-chevron-down"
          />
          <template #content>
            <div class="p-2 max-h-40 overflow-y-auto w-48">
              <div
                v-for="user in row.users"
                :key="user.id"
                class="text-sm py-1 border-b last:border-0 border-default"
              >
                {{ user.user_name }}
              </div>
            </div>
          </template>
        </UPopover>
      </template>

      <template #groups-data="{ row }">
        {{ row.groups?.length ?? 0 }}件
      </template>

      <template #redownload-data="{ row }">
        <UButton
          v-if="!row.isDisabled"
          :label="$t('history.re-download')"
          icon="i-lucide-download"
          size="sm"
          variant="outline"
          @click="$emit('action', 'redownload', row)"
        />
        <UBadge v-else :label="$t('history.expired')" color="neutral" variant="outline" />
      </template>

      <template #status-data="{ row }">
        <UBadge
          v-if="statusConfig[row.status]"
          :label="statusConfig[row.status].label"
          :color="statusConfig[row.status].color"
          variant="subtle"
        />
      </template>

      <template #actions-data="{ row }">
        <UDropdownMenu
          :items="[[{
            label: '公開切替',
            icon: 'i-lucide-eye',
            click: () => $emit('action', 'toggle-public', row),
          }]]"
        >
          <UButton icon="i-lucide-ellipsis-vertical" color="neutral" variant="ghost" />
        </UDropdownMenu>
      </template>

      <template #expand="{ row }">
        <div class="bg-elevated/5 px-12 py-2">
          <div
            v-for="child in row._children"
            :key="child.id"
            class="flex items-center py-2 text-sm border-b border-default/50"
          >
            <UIcon name="i-lucide-corner-down-right" class="mr-2 text-muted" />
            <span class="w-48">{{ formatDate(child.timestamp) }}</span>
            <span>{{ child.operator?.user_name }}</span>
          </div>
          <UButton
            v-if="row._hasMore"
            label="さらに表示"
            variant="soft"
            size="xs"
            class="mt-2"
            @click="$emit('loadMoreChildren', row.id, row._children.length)"
          />
        </div>
      </template>
    </UTable>

    <template #footer>
      <div class="grid grid-cols-3 items-center">
        <p class="text-sm text-muted">
          {{ pageStart }}〜{{ pageEnd }} / {{ properties.totalItems }}件
        </p>
        <div class="flex justify-center">
          <UPagination
            :model-value="properties.currentPage"
            :total="properties.totalItems"
            :page-count="properties.itemsPerPage"
            @update:model-value="(p) => $emit('update:currentPage', p)"
          />
        </div>
        <div />
      </div>
    </template>
  </UCard>
</template>
