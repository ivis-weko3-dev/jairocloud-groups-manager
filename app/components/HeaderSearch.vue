<script setup lang="ts">
const router = useRouter()

// CommandPalette の検索ワード
const searchTerm = ref('')

const dataStore = {
  repositories: [
    { id: 1, name: 'AAA大学リポジトリ', url: 'aaa.repo.nii.ac.jp' },
  ],
  users: [
    { id: 10, name: '大田 次郎', email: 'jiro@example.com' },
  ],
  groups: [
    { id: 99, name: 'AAA大学工学部', memberCount: 12 },
  ],
}

// dataStore = {} as typeof dataStore

// 検索結果
const { data: result, status, execute } = await useFetch('/api/search', {
  method: 'GET',
  query: () => ({ q: searchTerm.value }),
  transform: (data: {
    [resource: string]: {
      id: number
      name: string
      url?: string
      email?: string
      memberCount?: number
    }[]
  }) => {
    data = dataStore
    return {
      repos: data.repositories?.map(x => ({
        id: x.id,
        label: x.name,
        suffix: x.url,
        icon: 'i-lucide-folder',
        to: `/repo/${x.id}`,
      })) || [],
      users: data.users?.map(x => ({
        id: x.id,
        label: x.name,
        suffix: x.email,
        icon: 'i-lucide-user',
        to: `/user/${x.id}`,
      })) || [],
      groups: data.groups?.map(x => ({
        id: x.id,
        label: x.name,
        suffix: `${x.memberCount} members`,
        icon: 'i-lucide-users',
        to: `/group/${x.id}`,
      })) || [],
    }
  },
  lazy: true, // 手動で実行
})

// コマンドパレットの表示グループ
const groups = computed(() => [
  {
    id: 'repos',
    label: searchTerm.value ? `「${searchTerm.value}」に一致するリポジトリ` : 'リポジトリ',
    items: result.value?.repos || [],
    ignoreFilter: true,
  },
  {
    id: 'users',
    label: searchTerm.value ? `「${searchTerm.value}」に一致するユーザー` : 'ユーザー',
    items: result.value?.users || [],
    ignoreFilter: true,
  },
  {
    id: 'groups',
    label: searchTerm.value ? `「${searchTerm.value}」に一致するグループ` : 'グループ',
    items: result.value?.groups || [],
    ignoreFilter: true,
  },
])

// 改行 / Enterで検索実行
const onSubmit = async () => {
  if (!searchTerm.value) return
  await execute() // useFetch を手動実行
}

// アイテムが選択されたときの遷移
const onSelect = (item) => {
  if (item.to) router.push(item.to)
}

const isOpen = ref(false)
defineShortcuts({
  '/': () => isOpen.value = !isOpen.value,
})
</script>

<template>
  <UInput
    ref="input" color="neutral"
    icon="i-lucide-search" variant="outline"
    placeholder="検索..." class="w-50" @click="isOpen = true"
  >
    <template #trailing>
      <UKbd value="/" class="pointer-events-none" />
    </template>
  </UInput>

  <UModal v-model:open="isOpen">
    <template #content>
      <div class="relative">
        <UCommandPalette
          v-model:search-term="searchTerm"
          :loading="status === 'pending'"
          :groups="groups"
          placeholder="リポジトリ、ユーザー、グループを検索..."
          class="h-80"
          @submit="onSubmit"
          @select="onSelect"
        >
          <template #empty>
            <div v-if="searchTerm.length === 0">
              検索ワードを入力してください。
            </div>
            <div v-else>
              「{{ searchTerm }}」に一致する結果は見つかりませんでした。
            </div>
          </template>
        </UCommandPalette>
        <div class="absolute top-2.5 right-3 pointer-events-none">
          <UKbd value="enter" />
        </div>
      </div>
    </template>
  </UModal>
</template>
