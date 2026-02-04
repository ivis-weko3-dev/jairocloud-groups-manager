<script setup lang="ts" generic="T extends Record<string, any>">
import type { TableColumn } from '@nuxt/ui'

const properties = defineProps<{
  data: T[]
  columns: TableColumn<T>[]
  totalCount: number
  pageIndex: number
  pageSize: number
  selectedFilters: string[]
  filterOptions: Array<{ label: string, value: string }>
  title?: string
  description?: string
}>()

const emit = defineEmits<{
  'update:pageIndex': [value: number]
  'update:pageSize': [value: number]
  'update:selectedFilters': [value: string[]]
  'clearFilters': []
}>()

const { t: $t } = useI18n()

const isAllSelected = computed(() => properties.selectedFilters.length === 0)
const displayCount = computed(() => properties.data.length)

function changePageSize(size: number) {
  emit('update:pageSize', size)
  emit('update:pageIndex', 0)
}

function toggleFilter(filterValue: string) {
  const filters = [...properties.selectedFilters]
  const index = filters.indexOf(filterValue)
  if (index === -1) {
    filters.push(filterValue)
  }
  else {
    filters.splice(index, 1)
  }
  emit('update:selectedFilters', filters)
  emit('update:pageIndex', 0)
}

function selectAllFilters() {
  emit('clearFilters')
  emit('update:pageIndex', 0)
}
</script>

<template>
  <UCard variant="outline">
    <template #header>
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold">
            {{ title }}
          </h3>
          <p v-if="description" class="text-sm text-muted mt-0.5">
            {{ description }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <UDropdownMenu
            :items="[
              [
                {
                  label: $t('bulk.view-all'),
                  type: 'checkbox',
                  checked: isAllSelected,
                  onSelect: selectAllFilters,
                },
              ],
              filterOptions.map(option => ({
                label: option.label,
                type: 'checkbox' as const,
                checked: selectedFilters.includes(option.value),
                onSelect: () => toggleFilter(option.value),
              })),
            ]"
          >
            <UButton
              :label="$t('bulk.filter')"
              icon="i-lucide-filter"
              size="sm"
              color="neutral"
              variant="outline"
              trailing-icon="i-lucide-chevron-down"
            />
          </UDropdownMenu>
          <UDropdownMenu
            :items="[
              [
                { label: '10件', onSelect: () => changePageSize(10) },
                { label: '25件', onSelect: () => changePageSize(25) },
                { label: '50件', onSelect: () => changePageSize(50) },
                { label: '100件', onSelect: () => changePageSize(100) },
              ],
            ]"
          >
            <UButton
              :label="`${pageSize}${$t('bulk.table.count')}`"
              size="sm"
              color="neutral"
              variant="outline"
              trailing-icon="i-lucide-chevron-down"
            />
          </UDropdownMenu>
        </div>
      </div>
    </template>

    <UTable
      :data="data"
      :columns="columns"
      sticky
    />

    <template #footer>
      <div class="flex items-center">
        <div class="flex items-center gap-4 flex-1">
          <span class="text-sm text-muted">
            {{ (pageIndex * pageSize) + 1 }}-
            {{ Math.min((pageIndex + 1) * pageSize, displayCount) }}
            / {{ totalCount }}{{ $t('bulk.table.count') }}
          </span>
        </div>

        <UPagination
          :model-value="pageIndex + 1"
          :total="totalCount"
          :items-per-page="pageSize"
          size="xs"
          class="flex-center"
          @update:model-value="(page: number) => emit('update:pageIndex', page - 1)"
        />
        <div class="flex-1" />
      </div>
    </template>
  </UCard>
</template>
