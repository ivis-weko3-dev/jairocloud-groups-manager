<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const { search = true, profile = true } = defineProps<{ search?: boolean, profile?: boolean }>()

const { setLocale } = useI18n()
const { currentLocale: locale, locales } = useAvailableLocales()

const { users } = useDataStore()
const user = computed(() => users[1])

const items = computed<DropdownMenuItem[][]>(() => {
  const localePath = useLocalePath()
  return [[
    { label: $t('profile'), icon: 'i-lucide-user', to: localePath(`/users/${user.value?.id}`) },
    { label: $t('help'), icon: 'i-lucide-help-circle', to: localePath('/help') },
  ], [
    { label: $t('logout'), icon: 'i-lucide-log-out', to: '/logout', color: 'error' }],
  ]
})

const isAouthenticated = true
</script>

<template>
  <UHeader :toggle="false">
    <template #left>
      <NuxtLinkLocale to="/">
        <AppLogo class="w-auto h-6" />
      </NuxtLinkLocale>
    </template>

    <HeaderSearch v-if="isAouthenticated && search" />

    <template #right>
      <UColorModeButton />

      <ULocaleSelect
        v-model="locale" :locales="locales" class="h-8 w-30 my-auto"
        @update:model-value="setLocale($event as AvailableLocaleCode)"
      />

      <UDropdownMenu v-if="isAouthenticated && profile" :items="items" arrow :modal="false">
        <UButton
          :label="user?.displayName"
          icon="i-lucide-user-circle" color="neutral" variant="subtle"
        />
      </UDropdownMenu>
      <!-- <UButton
        v-if="isAouthenticated"
        icon="i-lucide-log-out" color="neutral" variant="ghost" to="/logout"
        class="lg:hidden"
      />

      <UButton
        v-if="isAouthenticated"
        :label="$t('logout')" color="error" variant="outline" to="/logout"
        class="hidden lg:inline-flex"
      /> -->
    </template>
  </UHeader>
</template>
