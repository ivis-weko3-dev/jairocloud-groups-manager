import { useDebounceFn } from '@vueuse/core'
import { computed, ref, watch } from 'vue'
import { CalendarDate, DateFormatter, getLocalTimeZone, parseDate } from '@internationalized/date'

import type { DateRange } from '@internationalized/date'
import type {
  DownloadApiModel,
  DownloadGroupItem,
  DownloadHistoryData,
  FilterOptionsResponse,
  HistoryQueryParameters,
  HistoryStats,
  SelectOption,
  UploadApiModel,
  UploadHistoryData,
} from '~/types/history'

export interface HistoryFilterOptions {
  target: 'download' | 'upload'
}

export function useHistoryFilter(options: HistoryFilterOptions) {
  const route = useRoute()
  const router = useRouter()
  const { t } = useI18n()

  function toArray(v: unknown): string[] {
    if (v == undefined) return []
    return Array.isArray(v) ? v.map(String).filter(Boolean) : [String(v)].filter(Boolean)
  }

  function toString_(v: unknown): string {
    return (typeof v === 'string' ? v : String(v ?? '')).trim()
  }

  const filterState = ref({
    s: toString_(route.query.s || ''),
    e: toString_(route.query.e || ''),
    o: toArray(route.query.o),
    r: toArray(route.query.r),
    g: toArray(route.query.g),
    u: toArray(route.query.u),
  })

  const isFiltered = computed(
    () => !!filterState.value.s
      || !!filterState.value.e
      || filterState.value.o.length > 0
      || filterState.value.r.length > 0
      || filterState.value.g.length > 0
      || filterState.value.u.length > 0,
  )

  function initializeDateRange(): DateRange | undefined {
    const start = filterState.value.s ? parseDate(filterState.value.s) : undefined
    const end = filterState.value.e ? parseDate(filterState.value.e) : undefined

    if (start) {
      return { start, end: end || start }
    }
    return undefined
  }

  const dateRange = ref<DateRange | undefined>(initializeDateRange())

  const df = new DateFormatter('ja-JP', {
    dateStyle: 'medium',
  })

  const formattedDateRange = computed(() => {
    if (!dateRange.value?.start) return ''

    const from = df.format(dateRange.value.start.toDate(getLocalTimeZone()))
    const to = dateRange.value.end
      ? df.format(dateRange.value.end.toDate(getLocalTimeZone()))
      : undefined

    return to ? `${from} - ${to}` : from
  })

  watch(dateRange, (newRange) => {
    if (!newRange || !newRange.start) {
      filterState.value.s = ''
      filterState.value.e = ''
      return
    }

    filterState.value.s = newRange.start.toString()
    filterState.value.e = newRange.end ? newRange.end.toString() : ''
  }, { deep: true })

  const updateQuery = useDebounceFn(() => {
    const newQuery: Record<string, any> = {
      ...route.query,
      tab: route.query.tab || options.target,
    }

    const setArray = (key: string, array: string[]) => {
      newQuery[key] = (array && array.length > 0) ? array : undefined
    }
    const setScalar = (key: string, value: string) => {
      newQuery[key] = (value && value.trim() !== '') ? value : undefined
    }

    setScalar('s', filterState.value.s)
    setScalar('e', filterState.value.e)
    setArray('o', filterState.value.o)
    setArray('r', filterState.value.r)
    setArray('g', filterState.value.g)
    setArray('u', filterState.value.u)

    router.replace({ path: '/history', query: newQuery })
  }, 200)

  watch(filterState, updateQuery, { deep: true })

  function resetFilters() {
    filterState.value = { s: '', e: '', o: [], r: [], g: [], u: [] }
    dateRange.value = undefined
    updateQuery()
  }

  const targetLabel = computed(() =>
    options.target === 'download' ? t('history.target', 1) : t('history.target', 2),
  )

  return {
    filterState,
    isFiltered,
    dateRange,
    formattedDateRange,
    resetFilters,
    targetLabel,
    updateQuery,
  }
}

export function useHistoryFilterOptions(target: Ref<'download' | 'upload'>) {
  const operatorOptions = ref<SelectOption[]>([])
  const repoOptions = ref<SelectOption[]>([])
  const groupOptions = ref<SelectOption[]>([])
  const userOptions = ref<SelectOption[]>([])

  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function loadOptions() {
    if (loading.value) return

    loading.value = true
    error.value = undefined

    try {
      const payload = await $fetch<FilterOptionsResponse>(
        `/api/history/${target.value}/filter-options`,
        { method: 'GET' },
      )

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
    catch {}
    finally {
      loading.value = false
    }
  }

  return {
    operatorOptions,
    repoOptions,
    groupOptions,
    userOptions,
    loading,
    error,
    loadOptions,
  }
}

export function useHistory(target: 'download' | 'upload') {
  const route = useRoute()

  const loading = ref(false)
  const error = ref<string | undefined>(undefined)
  const downloadGroups = ref<DownloadGroupItem[]>([])
  const uploadRows = ref<UploadHistoryData[]>([])
  const totalItems = ref<number>(0)
  const stats = ref<HistoryStats>({
    sum: 0,
    firstDownload: 0,
    reDownload: 0,
    success: 0,
    error: 0,
  })
  const fileExistsCache = ref<Map<string, boolean>>(new Map())

  function computeEffectiveTotal(itemsLength: number, currentPage: number, itemsPerPage: number): number {
    const base = (currentPage - 1) * itemsPerPage + itemsLength
    return base + (itemsPerPage === itemsLength ? 1 : 0)
  }

  async function checkFileExists(fileId: string): Promise<boolean> {
    if (fileExistsCache.value.has(fileId)) {
      return fileExistsCache.value.get(fileId)!
    }

    try {
      const result = await $fetch<boolean>(`/api/history/files/${fileId}/exists`)
      fileExistsCache.value.set(fileId, result)
      return result
    }
    catch {
      fileExistsCache.value.set(fileId, false)
      return false
    }
  }

  async function preloadFileExistence(items: DownloadHistoryData[]) {
    const fileIds = items
      .filter(item => item.file_id)
      .map(item => item.file_id!)

    await Promise.all(fileIds.map(id => checkFileExists(id)))
  }

  function isFileAvailable(data: DownloadHistoryData): boolean {
    if (!data.file_id) return false
    return fileExistsCache.value.get(data.file_id) ?? true
  }

  function buildQueryForApi(
    currentPage: number,
    itemsPerPage: number,
    sortDirection: 'asc' | 'desc',
  ): HistoryQueryParameters {
    const q: HistoryQueryParameters = { ...route.query }
    delete q.tab
    q.p = currentPage
    q.l = itemsPerPage
    q.d = sortDirection
    return q
  }

  async function fetchDownloadHistory(
    currentPage: number,
    itemsPerPage: number,
    sortDirection: 'asc' | 'desc',
  ) {
    const payload = await $fetch<DownloadApiModel | null>('/api/history/download', {
      method: 'GET',
      query: buildQueryForApi(currentPage, itemsPerPage, sortDirection),
    })

    if (!payload) throw new Error('Empty response')

    const list = payload.download_history_data ?? []
    downloadGroups.value = list.map(p => ({
      parent: p,
      children: [],
      hasMoreChildren: (p.children_count ?? 0) > 0,
      childrenLimit: 0,
    }))

    await preloadFileExistence(list)

    const pg = payload.pagination
    totalItems.value = typeof pg?.total === 'number'
      ? Number(pg.total)
      : computeEffectiveTotal(downloadGroups.value.length, currentPage, itemsPerPage)

    if (payload.summary && typeof payload.summary.total === 'number') {
      stats.value.sum = Number(payload.summary.total)
      stats.value.firstDownload = Number(payload.summary.first ?? 0)
      stats.value.reDownload = Number(payload.summary.redownload ?? 0)
    }
    else {
      stats.value.sum = Number(payload.sum_download ?? downloadGroups.value.length)
      stats.value.firstDownload = Number(payload.first_download ?? 0)
      stats.value.reDownload = Number(payload.re_download ?? 0)
    }
    stats.value.success = 0
    stats.value.error = 0
  }

  async function fetchUploadHistory(
    currentPage: number,
    itemsPerPage: number,
    sortDirection: 'asc' | 'desc',
  ) {
    const payload = await $fetch<UploadApiModel | null>('/api/history/upload', {
      method: 'GET',
      query: buildQueryForApi(currentPage, itemsPerPage, sortDirection),
    })

    if (!payload) throw new Error('Empty response')

    const list = payload.upload_history_data ?? []
    uploadRows.value = list.map(row => ({
      ...row,
      users: Array.isArray(row.users) ? row.users : [],
      groups: Array.isArray(row.groups) ? row.groups : [],
    }))

    const pg = payload.pagination
    totalItems.value = typeof pg?.total === 'number'
      ? Number(pg.total)
      : computeEffectiveTotal(uploadRows.value.length, currentPage, itemsPerPage)

    if (payload.summary && typeof payload.summary.total === 'number') {
      stats.value.sum = Number(payload.summary.total)
      stats.value.success = Number(payload.summary.success ?? 0)
      stats.value.error = Number(payload.summary.failed ?? 0)
    }
    else {
      stats.value.sum = Number(payload.sum_upload ?? uploadRows.value.length)
      stats.value.success = Number(payload.success_upload ?? 0)
      stats.value.error = Number(payload.failed_upload ?? 0)
    }
    stats.value.firstDownload = 0
    stats.value.reDownload = 0
  }

  async function fetchHistory(
    currentPage: number,
    itemsPerPage: number,
    sortDirection: 'asc' | 'desc',
  ) {
    loading.value = true
    error.value = undefined

    try {
      await (target === 'download'
        ? fetchDownloadHistory(currentPage, itemsPerPage, sortDirection)
        : fetchUploadHistory(currentPage, itemsPerPage, sortDirection))
    }
    catch (error_: unknown) {
      const message = error_ instanceof Error ? error_.message : String(error_)
      error.value = message
    }
    finally {
      loading.value = false
    }
  }

  async function loadChildren(
    parentId: string,
    offset: number,
    limit: number,
    currentPage: number,
    itemsPerPage: number,
    sortDirection: 'asc' | 'desc',
  ) {
    const payload = await $fetch<DownloadApiModel | null>('/api/history/download', {
      method: 'GET',
      query: {
        ...buildQueryForApi(currentPage, itemsPerPage, sortDirection),
        i: [parentId],
        p: Math.floor(offset / limit) + 1,
        l: limit,
      },
    })

    const items = (payload?.download_history_data ?? []) as DownloadHistoryData[]
    await preloadFileExistence(items)

    const group = downloadGroups.value.find(g => g.parent.id === parentId)
    if (!group) return

    group.children = [...group.children, ...items]
    const totalChildCount = group.parent.children_count ?? group.children.length
    group.hasMoreChildren = group.children.length < totalChildCount
  }

  async function togglePublicStatus(
    id: string,
    currentPublic: boolean,
  ) {
    const body = { public: !currentPublic }
    const result = await $fetch<boolean>(`/api/history/${target}/${id}/public-status`, {
      method: 'PUT',
      body,
    })
    return result
  }

  return {
    loading,
    error,
    downloadGroups,
    uploadRows,
    totalItems,
    stats,
    fetchHistory,
    loadChildren,
    togglePublicStatus,
    isFileAvailable,
  }
}

export type UseHistoryReturn = ReturnType<typeof useHistory>
