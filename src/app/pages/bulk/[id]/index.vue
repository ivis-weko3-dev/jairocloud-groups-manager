<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const historyId = computed(() => route.params.id as string)

const currentStep = ref(2)

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

const stepper = ref()

const { fetchUploadtResult, resetUpload } = useUserUpload()

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
      title: $t('bulk.status.error'),
      description: $t('bulk.import.result_failed'),
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
