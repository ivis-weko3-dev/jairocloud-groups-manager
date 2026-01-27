/**
 * Utility functions for resource search
 */

import { camelCase } from 'scule'

import type { LocationQuery } from 'vue-router'

const pickSingle = <T = string>(
  value: unknown, { camel }: { camel?: boolean } = {},
): T | undefined => {
  const _ = Array.isArray(value) ? value[0]?.toString() : value?.toString()
  return camel ? camelCase(_ as string) as T : _ as T
}

const toArray = (value: unknown): string[] => (
  Array.isArray(value) ? value : (value ? [value.toString()] : [])
)

/**
 * Normalize location query to users search query
 */
const normalizeUsersQuery = (query: LocationQuery): UsersSearchQuery => {
  const { table: { pageSize } } = useAppConfig()
  return {
    q: query.q ? pickSingle(query.q) : undefined,
    i: query.i ? toArray(query.i) : undefined,
    r: query.r ? toArray(query.r) : undefined,
    g: query.g ? toArray(query.g) : undefined,
    a: query.a ? toArray(query.a).map(Number) as UserRoleValue[] : undefined,
    s: query.s?.toString() || undefined,
    e: query.e?.toString() || undefined,
    k: query.k ? pickSingle(query.k, { camel: true }) : undefined,
    d: query.d ? pickSingle(query.d) as SortOrder : undefined,
    p: Number(query.p) || 1,
    l: Number(query.l) || pageSize.users?.[0],
  }
}

/**
 * Normalize location query to cache groups search query
 */
const normalizeCacheGroupsQuery = (query: LocationQuery): CacheGroupsSearchQuery => {
  const { table: { pageSize } } = useAppConfig()
  return {
    q: query.q ? pickSingle(query.q) : undefined,
    f: query.f ? toArray(query.f) : undefined,
    p: Number(query.p) || 1,
    l: Number(query.l) || pageSize.cacheGroups?.[0],
  }
}

export { normalizeUsersQuery, normalizeCacheGroupsQuery }
