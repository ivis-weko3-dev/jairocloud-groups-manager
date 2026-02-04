<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const historyId = computed(() => route.params.id as string)

const currentStep = ref(2) // 0始まりなので2に変更

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
    description: 'インポート結果',
    icon: 'i-lucide-circle-check-big',
  },
]

const stepper = ref()

const { importResult, fetchUploadtResult, resetUpload } = useUserUpload()

onMounted(async () => {
  if (!historyId.value) {
    await router.push('/bulk')
    return
  }

  try {
    await fetchUploadtResult(historyId.value)
  }
  catch (error) {
    console.error('Failed to fetch import result:', error)
    useToast().add({
      title: 'エラー',
      description: 'インポート結果の取得に失敗しました',
      color: 'error',
      icon: 'i-lucide-circle-x',
    })
    await router.push('/bulk')
  }
})

async function handleRestart() {
  resetUpload()
  await router.push('/bulk')
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

    <BulkResultStep
      :history-id="historyId"
      @restart="handleRestart"
    />
  </div>
</template>
