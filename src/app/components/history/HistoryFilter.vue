<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'

import { useI18n, useRoute, useRouter } from '#imports'

type Properties = { target: 'download' | 'upload' }
const properties = defineProps<Properties>()

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

function toArray(v: unknown): string[] {
  if (v == undefined) return []
  return Array.isArray(v) ? v.map(String).filter(Boolean) : [String(v)].filter(Boolean)
}
function toString_(v: unknown): string {
  return (typeof v === 'string' ? v : String(v ?? '')).trim()
}

const q = ref({
  s: toString_(route.query.s || ''),
  e: toString_(route.query.e || ''),
  o: toArray(route.query.o),
  r: toArray(route.query.r),
  g: toArray(route.query.g),
  u: toArray(route.query.u),
})

const dirty = computed(
  () => !!q.value.s || !!q.value.e || q.value.o.length > 0
    || q.value.r.length > 0 || q.value.g.length > 0 || q.value.u.length > 0,
)

type DateRange = { start: Date | undefined, end: Date | undefined }
const dateRange = ref<DateRange>({ start: undefined, end: undefined })

function toIsoLocalDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const da = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${da}`
}

function toDisplayDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const da = String(d.getDate()).padStart(2, '0')
  return `${y}/${m}/${da}`
}

const formattedDateRange = computed(() => {
  if (!q.value.s) return ''

  const s = toDisplayDate(q.value.s)
  const end = q.value.e ? toDisplayDate(q.value.e) : ''
  if (!end || s === end) return s
  return `${s} - ${end}`
})

watch(dateRange, (newRange) => {
  if (!newRange) {
    q.value.s = ''
    q.value.e = ''
    return
  }

  const { start, end } = newRange

  q.value.s = start ? toIsoLocalDate(start) : ''

  q.value.e = end ? toIsoLocalDate(end) : ''
}, { deep: true })

function safeDate(iso?: string): Date | undefined {
  if (!iso) return undefined
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? undefined : d
}

function initDateRangeFromQuery() {
  const s = safeDate(q.value.s)
  const end = safeDate(q.value.e)
  dateRange.value = { start: s, end: end }
}
initDateRangeFromQuery()

type SelectOption = { label: string, value: string }

const operatorOptions = ref<SelectOption[]>([])
const repoOptions = ref<SelectOption[]>([])
const groupOptions = ref<SelectOption[]>([])
const userOptions = ref<SelectOption[]>([])

const loadingOptions = ref(false)
const optionsError = ref<string | undefined>(undefined)

async function loadOptionsOnce() {
  if (loadingOptions.value) return
  loadingOptions.value = true
  optionsError.value = undefined
  try {
    const tub = properties.target
    const payload = await $fetch<{
      operators?: { id: string, user_name?: string | undefined }[]
      target_repositories?: { id: string, display_name?: string | undefined }[]
      target_groups?: { id: string, display_name?: string | undefined }[]
      target_users?: { id: string, user_name?: string | undefined }[]
    } | undefined>(`/api/history/${tub}/filter-options`, { method: 'GET' })

    if (!payload) throw new Error('Empty filter options')

    operatorOptions.value = (payload.operators ?? []).map(o => ({
      label: o.user_name ?? o.id,
      value: o.id,
    }))
    repoOptions.value = (payload.target_repositories ?? []).map(r => ({
      label: r.display_name ?? r.id,
      value: r.id,
    }))
    groupOptions.value = (payload.target_groups ?? []).map(g => ({
      label: g.display_name ?? g.id,
      value: g.id,
    }))
    userOptions.value = (payload.target_users ?? []).map(u => ({
      label: u.user_name ?? u.id,
      value: u.id,
    }))
  }
  finally {
    loadingOptions.value = false
  }
}
onMounted(loadOptionsOnce)

const pushQuery = useDebounceFn(() => {
  const newQuery: Record<string, any> = { ...route.query, tab: route.query.tab
    || properties.target }

  const setArray = (key: string, array: string[]) => {
    newQuery[key] = (array && array.length > 0) ? array : undefined
  }
  const setScalar = (key: string, value: string) => {
    newQuery[key] = (value && value.trim() !== '') ? value : undefined
  }

  setScalar('s', q.value.s)
  setScalar('e', q.value.e)
  setArray('o', q.value.o)
  setArray('r', q.value.r)
  setArray('g', q.value.g)
  setArray('u', q.value.u)

  router.replace({ path: '/history', query: newQuery })
}, 200)

watch(q, pushQuery, { deep: true })

function resetFilters() {
  q.value = { s: '', e: '', o: [], r: [], g: [], u: [] }
  dateRange.value = { start: undefined, end: undefined }
  pushQuery()
}

const targetLabel = computed(() =>
  properties.target === 'download' ? t('history.target', 1) : t('history.target', 2),
)

const operatorModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(q.value.o)) return []
    const set = new Set(q.value.o)
    return operatorOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    q.value.o = selected.map(s => s.value)
  },
})

const repoModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(q.value.r)) return []
    const set = new Set(q.value.r)
    return repoOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    q.value.r = selected.map(s => s.value)
  },
})

const groupModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(q.value.g)) return []
    const set = new Set(q.value.g)
    return groupOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    q.value.g = selected.map(s => s.value)
  },
})

const userModel = computed<SelectOption[]>({
  get() {
    if (!Array.isArray(q.value.u)) return []
    const set = new Set(q.value.u)
    return userOptions.value.filter(opt => set.has(opt.value))
  },
  set(selected: SelectOption[]) {
    q.value.u = selected.map(s => s.value)
  },
})
</script>

<template>
  <UCard variant="outline" class="mb-6">
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-highlighted">
          {{ $t('history.filter') }}
        </h2>
        <UButton
          v-if="dirty"
          :label="$t('history.reset')"
          icon="i-lucide-rotate-ccw"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="resetFilters"
        />
      </div>
    </template>

    <div v-if="loadingOptions" class="text-sm text-muted mb-2">
      {{ $t('common.loading') }}
    </div>
    <div v-else-if="optionsError" class="text-sm text-red-500 mb-2">
      {{ optionsError }}
    </div>

    <UFormField :label="$t('history.operation')" class="mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UPopover :popper="{ placement: 'bottom-start' }">
          <UInput
            icon="i-lucide-calendar"
            :placeholder="$t('history.operation-date')"
            :model-value="formattedDateRange"
            readonly
            class="w-full"
            @click="() => {}"
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
          :placeholder="$t('history.operator')"
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
          :placeholder="$t('repositories.title')"
          icon="i-lucide-folder"
          :items="repoOptions"
          multiple
          searchable
        />
        <USelectMenu
          v-model="groupModel"
          :placeholder="$t('groups.title')"
          icon="i-lucide-users"
          :items="groupOptions"
          multiple
          searchable
        />
        <USelectMenu
          v-model="userModel"
          :placeholder="$t('users.title')"
          icon="i-lucide-user"
          :items="userOptions"
          multiple
          searchable
        />
      </div>
    </UFormField>
  </UCard>
</template>
