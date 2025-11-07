<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const { setLocale } = useI18n()
const { currentLocale: locale, locales } = useAvailableLocales()

const items: DropdownMenuItem[] = [
  { label: 'プロフィール', icon: 'i-lucide-user', to: '/profile' },
  { label: '設定', icon: 'i-lucide-settings', to: '/settings' },
  { label: 'ヘルプ', icon: 'i-lucide-help-circle', to: '/help' },
  { label: 'ログアウト', icon: 'i-lucide-log-out', to: '/logout', color: 'error' },
]

const isAouthenticated = true
</script>

<template>
  <UHeader :toggle="false">
    <template #left>
      <NuxtLinkLocale to="/">
        <AppLogo class="w-auto h-6" />
      </NuxtLinkLocale>
    </template>

    <HeaderSearch v-if="isAouthenticated" />

    <template #right>
      <UColorModeButton />

      <ULocaleSelect
        v-model="locale" :locales="locales" class="h-8 w-30 my-auto"
        @update:model-value="setLocale($event as AvailableLocaleCode)"
      />

      <UDropdownMenu :items="items" arrow :modal="false">
        <UButton
          v-if="isAouthenticated" label="大田 次郎"
          icon="i-lucide-user-circle" color="neutral" variant="subtle"
        />
      </UDropdownMenu>
    </template>
  </UHeader>
</template>
