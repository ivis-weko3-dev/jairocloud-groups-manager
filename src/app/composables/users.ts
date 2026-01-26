/**
 * Composable for user-related operations
 */

import { UButton, UCheckbox, UDropdownMenu, UIcon, ULink, UTooltip } from '#components'

import type { Row } from '@tanstack/table-core'
import type { ButtonProps, DropdownMenuItem, TableColumn, TableRow } from '@nuxt/ui'

const useUsersTable = () => {
  const route = useRoute()
  const router = useRouter()

  const toast = useToast()
  const { t: $t } = useI18n()
  const { copy } = useClipboard()

  /** Reactive query object */
  const query = computed<UsersSearchQuery>(() => normalizeUsersQuery(route.query))
  /** Update query parameters and push to router */
  const updateQuery = (newQuery: Partial<UsersSearchQuery>) => {
    router.push({
      query: {
        ...route.query,
        ...newQuery,
      },
    })
  }

  const searchTerm = ref(query.value.q)
  const sortKey = computed(() => query.value.k)
  const sortOrder = computed(() => query.value.d)
  const pageSize = ref(query.value.l)

  const searchIdentityKey = computed(() => {
    const { k, d, p, l, ...filters } = query.value
    return JSON.stringify(filters)
  })

  const selectedMap = useState<Record<string, boolean>>(
    `selection:${searchIdentityKey.value}`, () => ({}),
  )

  /** Number of selected users */
  const selectedCount = computed(() => {
    return Object.values(selectedMap.value).filter(value => value === true).length
  })
  const toggleSelection = (row: Row<UserSummary>) => {
    selectedMap.value[row.id] = !selectedMap.value[row.id]
    row.toggleSelected(selectedMap.value[row.id])
  }

  /** Column names with translations */
  const columnNames = {
    id: '#',
    userName: $t('users.table.column.user-name'),
    emails: $t('users.table.column.emails'),
    eppns: $t('users.table.column.eppns'),
    lastModified: $t('users.table.column.last-modified'),
  }

  /** Returns action buttons for a user entry */
  const creationButtons = computed<ButtonProps[]>(() => [
    {
      icon: 'i-lucide-user-plus',
      label: $t('button.create-new'),
      to: '/users/new',
      color: 'primary',
      variant: 'solid',
    },
    {
      icon: 'i-lucide-file-up',
      label: $t('button.upload-users'),
      to: '/upload',
      color: 'primary',
      variant: 'solid',
    },
  ])

  /** Actions to display when the list is empty */
  const emptyActions = computed<ButtonProps[]>(() => [
    {
      icon: 'i-lucide-refresh-cw',
      label: $t('button.reload'),
      color: 'neutral',
      variant: 'subtle',
      onClick: () => {
        refreshNuxtData()
      },
    },
  ])

  /** Actions for selected users */
  const selectedUsersActions = computed<DropdownMenuItem[]>(() => [
    {
      icon: 'i-lucide-download',
      label: $t('users.button.selected-users-export'),
      onSelect() {
      // Export selected users
      },
    },
    {
      type: 'separator' as const,
    },
    {
      icon: 'i-lucide-user-plus',
      label: $t('users.button.selected-users-add-to-group'),
      color: 'neutral',
      onSelect() {
      // Open add users modal
      },
    },
    {
      icon: 'i-lucide-user-minus',
      label: $t('users.button.selected-users-remove-from-group'),
      color: 'error',
      onSelect() {
      // Open remove users modal
      },
    },
  ])

  type badgableRoles = 'systemAdmin' | 'repositoryAdmin' | 'communityAdmin' | 'contributor'
  const isBadge = (role: UserRole): role is badgableRoles => {
    const roles = new Set(['systemAdmin', 'repositoryAdmin', 'communityAdmin', 'contributor'])
    return roles.has(role)
  }

  type UserTableColumn = TableColumn<UserSummary>
  const columns = computed<UserTableColumn[]>(() => [
    {
      id: 'select',
      header: ({ table }) =>
        h(UCheckbox, {
          'modelValue': table.getIsSomePageRowsSelected()
            ? 'indeterminate'
            : table.getIsAllPageRowsSelected(),
          'onUpdate:modelValue': value => table.toggleAllPageRowsSelected(!!value),
          'aria-label': 'Select all',
        }),
      cell: ({ row }) =>
        h(UCheckbox, {
          'modelValue': row.getIsSelected(),
          'onUpdate:modelValue': () => toggleSelection(row),
          'aria-label': 'Select row',
        }),
      enableHiding: false,
    },
    {
      accessorKey: 'id',
      header: () => sortableHeader('id'),
    },
    {
      accessorKey: 'userName',
      header: () => sortableHeader('userName'),
      cell: ({ row }) => {
        const name = row.original.userName
        const role = row.original.role
        const labelMap = {
          systemAdmin: {
            label: $t('users.roles.system-admin'),
            color: 'error',
          },
          repositoryAdmin: {
            label: $t('users.roles.repository-admin'),
            color: 'primary',
          },
          communityAdmin: {
            label: $t('users.roles.community-admin'),
            color: 'warning',
          },
          contributor: {
            label: $t('users.roles.contributor'),
            color: 'neutral',
          },
        } as const

        return h(ULink,
          {
            to: (`/users/${row.original.id}`),
            class: 'font-bold inline-flex items-center group text-neutral',
          },
          [
            h('span', { class: 'group-hover:underline' }, name),
            role && isBadge(role) && h(UTooltip, {
              text: labelMap[role].label,
              class: 'ml-2',
              arrow: true,
            }, () => h(
              UIcon, {
                name: 'i-lucide-badge-check',
                class: ['size-4.5', 'shrink-0', `text-${labelMap[role!].color}`],
              },
            )),
          ].filter(Boolean),
        )
      },
      enableHiding: false,
    },
    {
      accessorKey: 'emails',
      header: () => sortableHeader('emails'),
      cell: ({ row }) => row.original.emails?.[0] || '',
    },
    {
      accessorKey: 'eppns',
      header: () => sortableHeader('eppns'),
      cell: ({ row }) => row.original.eppns?.[0] || '',
    },
    {
      accessorKey: 'lastModified',
      header: () => sortableHeader('lastModified'),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) =>
        h(
          'div',
          { class: 'text-right' },
          h(
          // @ts-expect-error: props type mismatch
            UDropdownMenu,
            {
              'content': { align: 'end' },
              'items': getActionItems(row),
              'aria-label': 'Actions dropdown',
            },
            () =>
              h(UButton, {
                'icon': 'i-lucide-ellipsis-vertical',
                'color': 'neutral',
                'variant': 'ghost',
                'size': 'sm',
                'class': 'ml-auto',
                'aria-label': 'Actions dropdown',
              }),
          ),
        ),
      enableHiding: false,
    },
  ])

  function sortableHeader(key: UsersSortableKeys) {
    const label = columnNames[key]
    const sortDirection = sortKey?.value === key ? sortOrder?.value : undefined
    const iconSet = {
      asc: 'i-lucide-arrow-down-a-z',
      desc: 'i-lucide-arrow-up-a-z',
      none: 'i-lucide-arrow-up-down',
    } as const

    return h(UButton, {
      color: sortDirection ? 'primary' : 'neutral',
      variant: 'ghost',
      size: 'xs',
      label,
      icon: sortDirection ? iconSet[sortDirection] : iconSet.none,
      class: 'font-medium cursor-pointer',
      onClick() {
        if (sortDirection === 'asc') updateQuery({ k: key, d: 'desc' }) // to desc
        else if (sortDirection === 'desc') updateQuery({ k: undefined, d: undefined }) // to default
        else updateQuery({ k: key, d: 'asc' }) // to asc
      },
    })
  }

  function getActionItems(row: TableRow<UserSummary>): DropdownMenuItem[] {
    return [
      {
        type: 'label',
        label: $t('table.actions-label'),
      },
      {
        label: $t('user.actions.copy-id'),
        onSelect() {
          copy(row.original.id)

          toast.add({
            title: 'User ID copied to clipboard!',
            color: 'success',
            icon: 'i-lucide-circle-check',
          })
        },
        icon: 'i-lucide-clipboard-copy',
      },
      {
        label: $t('user.actions.copy-eppn'),
        onSelect() {
          copy(row.original.eppns?.[0] || '')

          toast.add({
            title: 'EPPN copied to clipboard!',
            color: 'success',
            icon: 'i-lucide-circle-check',
          })
        },
        icon: 'i-lucide-clipboard-copy',
      },
      {
        label: $t('table.actions.view-details'),
        to: `/users/${row.original.id}`,
        icon: 'i-lucide-eye',
      },
      {
        type: 'separator',
      },
    ]
  }

  const columnVisibility = ref({ id: false })

  return {
    query,
    updateQuery,
    criteria: {
      searchTerm,
      pageSize,
    },
    creationButtons,
    emptyActions,
    selectedCount,
    selectedUsersActions,
    columns,
    columnNames,
    columnVisibility,
  }
}

export { useUsersTable }
