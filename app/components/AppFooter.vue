<script setup lang="ts">
const localePath = useLocalePath()

const columns = [
  {
    label: $t('Management'),
    children: [
      { label: $t('Repositories'), to: localePath('/repositories') },
      { label: $t('Groups'), to: localePath('/groups') },
      { label: $t('User'), to: localePath('/users') },
    ],
  },
  {
    label: $t('Others'),
    children: [
      { label: $t('History'), to: '/history' },
    ],
  },
]
</script>

<template>
  <USeparator icon="i-simple-icons-nuxtdotjs" class="h-px" />

  <UFooter :ui="{ top: 'border-b border-default' }">
    <template #top>
      <UContainer>
        <UFooterColumns :columns="columns" />
      </UContainer>
    </template>

    <template #left>
      <p class="text-muted text-sm">
        &copy; {{ new Date().getFullYear() }} National Institute of Informatics
      </p>
    </template>

    <template #right>
      <UColorModeButton />
    </template>
  </UFooter>
</template>
