<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { useI18n, useRoute, useRouter } from '#imports'

import StatisticsCard from '~/components/history/StatisticsCard.vue'
import HistoryFilter from '~/components/history/HistoryFilter.vue'
import HistoryTable from '~/components/history/HistoryTable.vue'

type UserSummary = { id: string, user_name?: string | null }
type RepositorySummary = { id: string, display_name?: string | null }
type GroupSummary = { id: string, display_name?: string | null }

type DownloadHistoryData = {
  id: string
  timestamp: string
  operator: UserSummary
  public: boolean
  parent_id: string | null
  file_path: string
  file_id?: string
  repositories: RepositorySummary[]
  groups: GroupSummary[]
  users: UserSummary[]
  children_count: number
}

type UploadHistoryData = {
  id: string
  timestamp: string
  end_timestamp?: string | null
  public: boolean
  operator: UserSummary
  status: 'S' | 'F' | 'P'
  file_path: string
  file_id?: string
  repositories: RepositorySummary[]
  groups: GroupSummary[]
  users: UserSummary[]
}

type DownloadApiModel = {
  download_history_data: DownloadHistoryData[]
  sum_download?: number
  first_download?: number
  re_download?: number
  pagination?: { page: number, per_page: number, total: number }
  summary?: { total: number, first: number, redownload: number }
}

type UploadApiModel = {
  upload_history_data: UploadHistoryData[]
  sum_upload?: number
  success_upload?: number
  failed_upload?: number
  progress_upload?: number
  proggres_upload?: number // APIのタイポ対応
  pagination?: { page: number, per_page: number, total: number }
  summary?: { total: number, success: number, failed: number, progress: number }
}

// クエリパラメータの型定義
interface HistoryQueryParameters {
  tab?: string
  p?: string | number
  l?: string | number
  d?: string
  dir?: string
  s?: string
  e?: string
  o?: string
  r?: string
  g?: string
  u?: string
  i?: string[]
}

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const tabItems = computed(() => [
  { label: t('history.tub', 1), icon: 'i-lucide-download', slot: 'download', value: 'download' },
  { label: t('history.tub', 2), icon: 'i-lucide-upload', slot: 'upload', value: 'upload' },
])

const activeTab = computed<string>({
  get() {
    return (route.query.tab as string) || 'download'
  },
  set(tab) {
    router.push({ path: '/history', query: { ...route.query, tab } })
  },
})

function toPositiveInt(v: unknown, fallback: number) {
  if (!Number.isFinite(fallback) || fallback === undefined) fallback = 1
  if (v === undefined) return fallback
  const raw = Array.isArray(v) ? v[0] : v
  let n: number
  if (typeof raw === 'number') n = raw
  else if (typeof raw === 'string') n = Number.parseInt(raw, 10)
  else n = Number(raw) // anyキャストを削除
  return Number.isFinite(n) && Number.isInteger(n) && n > 0 ? n : fallback
}

const currentPage = ref<number>(toPositiveInt(route.query.p, 1))
const itemsPerPage = ref<number>(toPositiveInt(route.query.l, 10))

watch([currentPage, itemsPerPage], () => {
  const qp = toPositiveInt(route.query.p, 1)
  const ql = toPositiveInt(route.query.l, 10)
  if (qp === currentPage.value && ql === itemsPerPage.value) return
  router.replace({ path: '/history', query: { ...route.query,
    p: currentPage.value, l: itemsPerPage.value } })
})

const sortDirection = ref<'asc' | 'desc'>('desc')
onMounted(() => {
  const d = (route.query.d as string) || (route.query.dir as string)
  if (d === 'asc' || d === 'desc') sortDirection.value = d
})
function toggleSort() {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  router.push({ path: '/history', query: { ...route.query, d: sortDirection.value, p: 1 } })
}

const loading = ref(false)
const error = ref<string | undefined>(undefined)

watch(
  [
    () => route.query.tab,
    () => route.query.s,
    () => route.query.e,
    () => route.query.o,
    () => route.query.r,
    () => route.query.g,
    () => route.query.u,
    currentPage,
    itemsPerPage,
    () => sortDirection.value,
  ],
  () => { fetchHistory() },
  { immediate: true },
)

type DownloadGroupItem = {
  parent: DownloadHistoryData
  children: DownloadHistoryData[]
  hasMoreChildren: boolean
  childrenLimit: number
}
const downloadGroups = ref<DownloadGroupItem[]>([])
const uploadRows = ref<UploadHistoryData[]>([])

const totalItems = ref<number>(0)
const stats = ref<Record<string, number>>({
  sum: 0,
  firstDownload: 0,
  reDownload: 0,
  success: 0,
  error: 0,
  cancel: 0,
})

function computeEffectiveTotal(itemsLength: number) {
  const base = (currentPage.value - 1) * itemsPerPage.value + itemsLength
  return base + (itemsPerPage.value === itemsLength ? 1 : 0)
}

const DOWNLOAD_TTL_HOURS = 0
function isWithinTTL(iso: string): boolean {
  if (!DOWNLOAD_TTL_HOURS || DOWNLOAD_TTL_HOURS <= 0) return true
  const d = new Date(iso).getTime()
  const now = Date.now()
  const ttlMs = DOWNLOAD_TTL_HOURS * 60 * 60 * 1000
  return now - d <= ttlMs
}

function buildQueryForApi(): HistoryQueryParameters {
  const q: HistoryQueryParameters = { ...route.query }
  delete q.tab
  q.p = currentPage.value
  q.l = itemsPerPage.value
  q.d = sortDirection.value
  return q
}

async function fetchHistory() {
  loading.value = true
  error.value = undefined
  try {
    const tub = activeTab.value as 'download' | 'upload'
    const payload = await $fetch<DownloadApiModel | UploadApiModel | null>(`/api/history/${tub}`, {
      method: 'GET',
      query: buildQueryForApi(),
    })
    if (!payload) throw new Error('Empty response')

    if (tub === 'download') {
      const s = payload as DownloadApiModel
      const list = s.download_history_data ?? []
      downloadGroups.value = list.map(p => ({
        parent: p,
        children: [],
        hasMoreChildren: (p.children_count ?? 0) > 0,
        childrenLimit: 0,
      }))
      const pg = s.pagination
      totalItems.value = typeof pg?.total === 'number'
        ? Number(pg.total)
        : computeEffectiveTotal(downloadGroups.value.length)

      if (s.summary && typeof s.summary.total === 'number') {
        stats.value.sum = Number(s.summary.total)
        stats.value.firstDownload = Number(s.summary.first ?? 0)
        stats.value.reDownload = Number(s.summary.redownload ?? 0)
      }
      else {
        stats.value.sum = Number(s.sum_download ?? downloadGroups.value.length)
        stats.value.firstDownload = Number(s.first_download ?? 0)
        stats.value.reDownload = Number(s.re_download ?? 0)
      }
      stats.value.success = 0
      stats.value.error = 0
      stats.value.cancel = 0
    }
    else {
      const s = payload as UploadApiModel
      const list = s.upload_history_data ?? []
      uploadRows.value = list.map(row => ({
        ...row,
        users: Array.isArray(row.users) ? row.users : [],
        groups: Array.isArray(row.groups) ? row.groups : [],
      }))
      const pg = s.pagination
      totalItems.value = typeof pg?.total === 'number'
        ? Number(pg.total)
        : computeEffectiveTotal(uploadRows.value.length)

      if (s.summary && typeof s.summary.total === 'number') {
        stats.value.sum = Number(s.summary.total)
        stats.value.success = Number(s.summary.success ?? 0)
        stats.value.error = Number(s.summary.failed ?? 0)
        stats.value.cancel = Number(s.summary.progress ?? 0)
      }
      else {
        stats.value.sum = Number(s.sum_upload ?? uploadRows.value.length)
        stats.value.success = Number(s.success_upload ?? 0)
        stats.value.error = Number(s.failed_upload ?? 0)
        stats.value.cancel = Number(s.progress_upload ?? s.proggres_upload ?? 0)
      }
      stats.value.firstDownload = 0
      stats.value.reDownload = 0
    }
  }
  catch (error_: unknown) {
    const message = error_ instanceof Error ? error_.message : String(error_)
    error.value = message
  }
  finally {
    loading.value = false
  }
}

const CHILD_PAGE_SIZE = 20
async function loadChildren(parentId: string, offset = 0, limit = CHILD_PAGE_SIZE) {
  const payload = await $fetch<DownloadApiModel | null>('/api/history/download', {
    method: 'GET',
    query: { ...buildQueryForApi(), i: [parentId], p: Math.floor(offset / limit) + 1, l: limit },
  })
  const items = (payload?.download_history_data ?? []) as DownloadHistoryData[]
  const group = downloadGroups.value.find(g => g.parent.id === parentId)
  if (!group) return
  group.children = [...group.children, ...items]
  const totalChildCount = group.parent.children_count ?? group.children.length
  group.hasMoreChildren = group.children.length < totalChildCount
}

async function handleLoadMoreChildren(parentId: string, currentShown: number) {
  await loadChildren(parentId, currentShown, CHILD_PAGE_SIZE)
}

type ActionRow = DownloadGroupItem | UploadHistoryData

async function handleAction(action: string, row: ActionRow) {
  // ダウンロード（グループ型）かアップロード（フラット型）かを判定して実データを抽出
  // 'parent' プロパティがあればダウンロードグループとみなす
  const isDownload = 'parent' in row
  const data = isDownload ? row.parent : row
  // 以降は data (DownloadHistoryData | UploadHistoryData) に対して処理を行う
  switch (action) {
    case 'toggle-public': {
      const tub = activeTab.value as 'download' | 'upload'
      const body = { public: !data.public }
      try {
        const result = await $fetch<boolean>(`/api/history/${tub}/${data.id}/public-status`, {
          method: 'PUT',
          body,
        })
        // サーバーの応答に合わせて reactive な値を更新
        if (result === body.public) {
          data.public = result
        }
      }
      catch (error_: unknown) {
        error.value = error_ instanceof Error ? error_.message : 'Failed to update status'
      }
      break
    }
    case 'redownload': {
      if (data.file_id) {
        const url = `/api/history/files/${data.file_id}`
        window.open(url, '_blank')
      }
      break
    }
    case 'show-detail': {
      router.push({ path: `/upload/history/${data.id}` })
      break
    }
  }
}

const sum = computed(() => String(stats.value.sum ?? 0))
const firstDownload = computed(() => String(stats.value.firstDownload ?? 0))
const reDownload = computed(() => String(stats.value.reDownload ?? 0))
const success = computed(() => String(stats.value.success ?? 0))
const failed = computed(() => String(stats.value.error ?? 0))
</script>

<template>
  <div>
    <UPageHeader
      :title="$t('history.title')"
      :description="$t('history.description')"
      :ui="{ root: 'py-2', description: 'mt-2' }"
    />
  </div>

  <div>
    <UTabs
      v-model="activeTab"
      :items="tabItems"
      class="w-full"
      variant="link"
      :ui="{ trigger: 'min-w-50' }"
    >
      <template #download>
        <div class="container mx-auto px-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <StatisticsCard
              icon="i-lucide-download" :title="$t('history.sum', 1)"
              :value="sum" color="primary"
            />
            <StatisticsCard
              icon="i-lucide-file-check" :title="$t('history.first-download')"
              :value="firstDownload" color="primary"
            />
            <StatisticsCard
              icon="i-lucide-refresh-cw" :title="$t('history.re-download')"
              :value="reDownload" color="secondary"
            />
          </div>

          <HistoryFilter target="download" />

          <div v-if="loading" class="text-center text-sm text-muted py-10">
            {{ $t('common.loading') }}
          </div>
          <div v-else-if="error" class="text-center text-sm text-red-500 py-10">
            {{ error }}
          </div>
          <div v-else>
            <HistoryTable
              key="download-table"
              v-model:current-page="currentPage"
              v-model:items-per-page="itemsPerPage"
              :data="downloadGroups"
              :total-items="totalItems"
              :table-config="{ enableExpand: true, showStatus: false }"
              :ttl-check="isWithinTTL"
              @action="handleAction"
              @sort-change="toggleSort"
              @load-more-children="handleLoadMoreChildren"
            />
          </div>
        </div>
      </template>

      <template #upload>
        <div class="container mx-auto px-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <StatisticsCard
              icon="i-lucide-upload" :title="$t('history.sum', 2)"
              :value="sum" color="primary"
            />
            <StatisticsCard
              icon="i-lucide-check-circle" :title="$t('history.success-count')"
              :value="success" color="primary"
            />
            <StatisticsCard
              icon="i-lucide-x-circle" :title="$t('history.failed-count')"
              :value="failed" color="error"
            />
          </div>

          <HistoryFilter target="upload" />

          <div v-if="loading" class="text-center text-sm text-muted py-10">
            {{ $t('common.loading') }}
          </div>
          <div v-else-if="error" class="text-center text-sm text-red-500 py-10">
            {{ error }}
          </div>
          <div v-else>
            <HistoryTable
              key="upload-table"
              v-model:current-page="currentPage"
              v-model:items-per-page="itemsPerPage"
              :data="uploadRows"
              :total-items="totalItems"
              :table-config="{ enableExpand: false, showStatus: true }"
              @action="handleAction"
              @sort-change="toggleSort"
            />
          </div>
        </div>
      </template>
    </UTabs>
  </div>
</template>
