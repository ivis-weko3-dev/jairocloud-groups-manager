<script setup lang="ts">
defineProps<{
  icon: string
  color?: string
  title?: string
  value?: string
  to?: string
}>()
</script>

<template>
  <UPageCard variant="outline" :to="to">
    <div class="flex items-center gap-4">
      <div :class="`p-3 rounded-lg bg-${color}/10`">
        <UIcon :name="icon" :class="`size-6 text-${color}`" />
      </div>
      <div>
        <p class="text-sm text-muted">
          {{ title }}
        </p>
        <p class="text-2xl font-bold text-highlighted">
          {{ value }}
        </p>
      </div>
    </div>
  </UPageCard>
</template>
