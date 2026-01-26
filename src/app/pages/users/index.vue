<script setup lang="ts">
const {
  query, updateQuery, criteria, creationButtons, emptyActions,
  selectedCount, selectedUsersActions, columns, columnNames, columnVisibility,
} = useUsersTable()

const { searchTerm, pageSize } = criteria

const table = useTemplateRef('table')
const { table: { pageSize: { users: pageOptions } } } = useAppConfig()

const { data: result } = useFetch<UsersSearchResult>('/api/users', {
  method: 'GET',
  query,
  lazy: true,
  server: false,
})

const offset = computed(() => (result.value?.offset ?? 1))
</script>

<template>
  <div>
    <UPageHeader
      :title="$t('users.table.title')"
      :description="$t('users.description')"
      :ui="{ root: 'py-2', description: 'mt-2' }"
    />
  </div>

  <dev>
    <div class="flex justify-between items-center my-4">
      <div class="flex space-x-2">
        <UButton
          v-for="(button, index) in creationButtons"
          :key="index"
          :icon="button.icon" :label="button.label"
          :to="button.to" :color="button.color" :variant="button.variant"
          :ui="{ base: 'gap-1' }"
        />
      </div>

      <UDropdownMenu :items="selectedUsersActions">
        <UButton
          :label="$t('users.button.selected-users-actions')"
          color="warning" variant="subtle"
          :ui="{ base: 'gap-1' }"
          :disabled="selectedCount === 0"
        />
      </UDropdownMenu>
    </div>

    <div class="flex justify-between mb-4">
      <UInput
        v-model="searchTerm" :placeholder="$t('users.table.search-placeholder')"
        icon="i-lucide-search" :ui="{ base: 'w-sm', trailing: 'pe-1.5' }"
        @keydown.enter="() => updateQuery({ q: searchTerm, p: 1 })"
      >
        <template #trailing>
          <UButton
            variant="ghost" color="neutral"
            :ui="{ base: 'font-normal cursor-pointer p-1' }"
            @click="() => updateQuery({ q: searchTerm, p: 1 })"
          >
            <UKbd value="enter" />
          </UButton>
        </template>
      </UInput>
      <div class="flex justify-end items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm text-gray-600">{{ $t('table.page-size-label') }}</label>
          <USelect
            v-model="pageSize" :items="pageOptions"
            class="w-24"
            @update:model-value="() => updateQuery(
              { l: pageSize, p: Math.ceil(offset / pageSize!) },
            )"
          />
        </div>

        <UDropdownMenu
          :items="
            table?.tableApi
              ?.getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => ({
                label: columnNames[column.id as keyof typeof columnNames],
                type: 'checkbox' as const,
                checked: column.getIsVisible(),
                onUpdateChecked(checked: boolean) {
                  table?.tableApi?.getColumn(column.id)?.toggleVisibility(!!checked)
                },
                onSelect(e: Event) {
                  e.preventDefault()
                },
              }))
          "
          :content="{ align: 'end' }"
        >
          <UButton
            color="neutral" variant="outline"
            trailing-icon="i-lucide-chevron-down" :label="$t('table.display-columns-label')"
          />
        </UDropdownMenu>
      </div>
    </div>

    <UTable
      ref="table"
      v-model:column-visibility="columnVisibility"
      :data="result?.resources" :columns="columns"
    >
      <template #empty>
        <UEmpty
          :title="$t('users.table.no-users-title')"
          :description="$t('users.table.no-users-description')"
          :actions="emptyActions"
        />
      </template>
    </UTable>
  </dev>
</template>
