<script setup lang="ts">
import { computed, onMounted, ref, toRef } from 'vue'

import type { HistoryFilterProperties, SelectOption } from '~/types/history'

const properties = defineProps<HistoryFilterProperties>()

const { t } = useI18n()

const {
  filterState,
  isFiltered,
  dateRange,
  formattedDateRange,
  resetFilters,
  targetLabel,
} = useHistoryFilter({ target: properties.target })

const targetReference = toRef(properties, 'target')
const {
  operatorOptions,
  repoOptions,
  groupOptions,
  userOptions,
  loading: loadingOptions,
  error: optionsError,
  loadOptions,
} = useHistoryFilterOptions(targetReference)

onMounted(loadOptions)

const operatorModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(filterState.value.o)) return []
    const set = new Set(filterState.value.o)
    return operatorOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    filterState.value.o = selected.map(s => s.value)
  },
})

const repoModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(filterState.value.r)) return []
    const set = new Set(filterState.value.r)
    return repoOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    filterState.value.r = selected.map(s => s.value)
  },
})

const groupModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(filterState.value.g)) return []
    const set = new Set(filterState.value.g)
    return groupOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    filterState.value.g = selected.map(s => s.value)
  },
})

const userModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(filterState.value.u)) return []
    const set = new Set(filterState.value.u)
    return userOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    filterState.value.u = selected.map(s => s.value)
  },
})
</script>

<template>
  <UCard variant="outline" class="mb-6">
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">
          {{ t('history.filter') }}
        </h2>
        <UButton
          v-if="isFiltered"
          :label="t('history.reset')"
          icon="i-lucide-rotate-ccw"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="resetFilters"
        />
      </div>
    </template>

    <div v-if="loadingOptions" class="text-sm text-muted mb-2">
      {{ t('common.loading') }}
    </div>

    <div v-if="optionsError" class="text-sm text-error mb-4">
      {{ optionsError }}
    </div>

    <UFormField :label="t('history.operation')" class="mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UPopover :popper="{ placement: 'bottom-start' }">
          <UInput
            icon="i-lucide-calendar"
            :placeholder="t('history.operation-date')"
            :model-value="formattedDateRange"
            readonly
            class="w-full"
          />
          <template #content>
            <UCalendar
              v-model="dateRange"
              range
              :number-of-months="2"
              class="p-2"
            />
          </template>
        </UPopover>

        <USelectMenu
          v-model="operatorModel"
          :placeholder="t('history.operator')"
          icon="i-lucide-user"
          :items="operatorOptions"
          multiple
          searchable
        />
      </div>
    </UFormField>

    <UFormField :label="targetLabel">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <USelectMenu
          v-model="repoModel"
          :placeholder="t('repositories.title')"
          icon="i-lucide-folder"
          :items="repoOptions"
          multiple
          searchable
        />
        <USelectMenu
          v-model="groupModel"
          :placeholder="t('groups.title')"
          icon="i-lucide-users"
          :items="groupOptions"
          multiple
          searchable
        />
        <USelectMenu
          v-model="userModel"
          :placeholder="t('users.title')"
          icon="i-lucide-user"
          :items="userOptions"
          multiple
          searchable
        />
      </div>
    </UFormField>
  </UCard>
</template>
