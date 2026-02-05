<script setup lang="ts">
const currentStep = ref(0)

const { t: $t } = useI18n()
const items = [
  {
    title: $t('bulk.step.select_file'),
    description: $t('bulk.step.select_file_description'),
    icon: 'i-lucide-file-up',
  },
  {
    title: $t('bulk.step.validate'),
    description: $t('bulk.step.validate_description'),
    icon: 'i-lucide-shield-check',
  },
  {
    title: $t('bulk.step.complete'),
    description: $t('bulk.step.complete_description'),
    icon: 'i-lucide-circle-check-big',
  },
]

function onUploadComplete() {
  currentStep.value = 1
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function onImportComplete(uploadHistoryId: string) {
  await navigateTo(`/bulk/${uploadHistoryId}`)
}

function goBackToUpload() {
  currentStep.value = 0
}
</script>

<template>
  <div>
    <UPageHeader
      :title="$t('bulk.title')"
      :description="$t('bulk.description')"
      :ui="{ root: 'py-2', description: 'mt-2' }"
    />

    <UStepper
      ref="stepper"
      v-model="currentStep"
      :items="items"
      disabled
      orientation="horizontal"
      class="my-8"
    />

    <BulkUploadStep
      v-if="currentStep === 0"
      @next="onUploadComplete"
    />

    <BulkValidationStep
      v-else-if="currentStep === 1"
      @next="onImportComplete"
      @prev="goBackToUpload"
    />
  </div>
</template>
