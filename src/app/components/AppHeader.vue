<!--
 Copyright (C) 2026 National Institute of Informatics.
-->

<script setup lang="ts">
const { setLocale } = useI18n()
const { currentLocale: locale, locales } = useAvailableLocales()
</script>

<template>
  <UHeader :toggle="false">
    <template #left>
      <AppLogo />
    </template>

    <template #right>
      <UColorModeButton />
      <ULocaleSelect
        v-model="locale" :locales="locales" class="h-8 w-30 my-auto"
        @update:model-value="setLocale($event as AvailableLocaleCode)"
      />
    </template>
  </UHeader>
</template>
