<script setup lang="ts">
const currentStep = ref(0)

const items = [
  {
    title: 'ファイル選択',
    description: 'CSV,TSVまたはExcelファイル',
    icon: 'i-lucide-file-up',
  },
  {
    title: 'データ検証',
    description: '変更内容の確認',
    icon: 'i-lucide-shield-check',
  },
  {
    title: '完了',
    description: 'アップロード結果',
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
