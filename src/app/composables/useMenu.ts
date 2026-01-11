/*
 * Copyright (C) 2026 National Institute of Informatics.
 */

/**
 * Composable to manage the application menu items
 */

export function useMenu() {
  const { t: $t } = useI18n()
  const management = computed(() => ({
    label: $t('menu.management'),
    children: [
      { label: $t('repositories.title'), to: '/repositories' },
      { label: $t('groups.title'), to: '/groups' },
      { label: $t('users.title'), to: '/users' },
    ],
  }))
  const other = computed(() => ({
    label: $t('menu.other'),
    children: [
      { label: $t('history.title'), to: '/history' },
      { label: $t('cache-groups.title'), to: '/cache-groups' },
    ],
  }))
  return {
    management,
    other,
  }
}
