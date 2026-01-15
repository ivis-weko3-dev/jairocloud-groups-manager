<!-- eslint-disable unicorn/prevent-abbreviations -->
<script setup lang="ts">
import type { Collections } from '@nuxt/content'
import type { NavigationMenuItem } from '@nuxt/ui'

const route = useRoute()
const categories: (Exclude<keyof Collections, 'index'>)[] = ['detailed', 'api', 'db']
const categoryData = await Promise.all(
  categories.map(category =>
    useAsyncData(`links-${category}`, () => {
      return queryCollection(category).first()
    }),
  ),
)
const links = computed(() =>
  categoryData.map((result, index) => ({
    label: result.data.value!.title,
    icon: result.data.value?.icon,
    to: `/${categories[index]}`,
    active: route.path.startsWith(`/${categories[index]}`),
  } as NavigationMenuItem)),
)
</script>

<template>
  <UHeader>
    <template #left>
      <UNavigationMenu :items="links" />
    </template>
  </UHeader>
</template>
