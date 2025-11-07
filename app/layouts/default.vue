<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const rute = useRoute()
const localePath = useLocalePath()

const items: NavigationMenuItem[] = [
  {
    label: $t('Management'), type: 'label',
  },
  {
    label: $t('Repositories'), icon: 'i-lucide-folder', to: localePath('/'),
    active: rute.path.startsWith('/repositories'),
  },
  {
    label: $t('Groups'),
    icon: 'i-lucide-users',
    to: localePath('/groups'),
    active: rute.path.startsWith('/groups'),
  },
  {
    label: $t('User'),
    icon: 'i-lucide-user',
    to: localePath('/users'),
    active: rute.path.startsWith('/users'),
  },
  {
    label: $t('Others'),
    type: 'label',
  },
  {
    label: $t('History'),
    icon: 'i-lucide-clock',
    to: localePath('/history'),
    active: rute.path.startsWith('/history'),
  },
]

const toaster = { position: 'top-center' } as const
</script>

<template>
  <UApp :toaster="toaster">
    <AppHeader />

    <UMain>
      <UContainer>
        <div class="flex gap-8 min-h-[calc(100vh-var(--ui-header-height))]">
          <aside
            :class="[
              'hidden', 'lg:block', 'lg:w-50', 'shrink-0', 'border-e', 'border-default',
              'self-start', 'sticky', 'top-[var(--ui-header-height)]',
              'max-h-[calc(100vh-var(--ui-header-height))]', 'overflow-y-auto',
            ]"
          >
            <div class="flex flex-col gap-4 py-8 pr-6">
              <UNavigationMenu
                :items="items"
                orientation="vertical"
              />
            </div>
          </aside>

          <div class="flex-1 flex flex-col min-w-0">
            <div class="flex-1 py-8">
              <slot />
            </div>

            <AppFooter />
          </div>
        </div>
      </UContainer>
    </UMain>
  </UApp>
</template>
