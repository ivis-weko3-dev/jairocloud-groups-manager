<script setup lang="ts">
import { FetchError } from 'ofetch'

const { currentUser } = useAuth()

if (!currentUser.value?.isSystemAdmin) {
  showError({
    status: 403,
    statusText: $t('repository.error.forbidden'),
  })
}

const defaultData: Required<RepositoryCreateForm> = {
  serviceName: '',
  serviceUrl: '',
  entityIds: [''],
  active: true,
}

const state = ref<RepositoryCreateForm>({ ...defaultData })

const onSubmit = async (data: RepositoryCreateForm) => {
  const toast = useToast()
  try {
    await $fetch('/api/repositories', {
      method: 'POST',
      body: data,
    })

    toast.add({
      title: $t('success.creation.title'),
      description: $t('success.repository.created-description'),
      color: 'success',
    })
    await navigateTo('/repositories')
  }
  catch (error) {
    if (error instanceof FetchError) {
      if (error.status === 400) {
        toast.add({
          title: $t('error.validation.title'),
          description: error?.data?.message ?? $t('error.validation.description'),
          color: 'error',
        })
      }
      else if (error.status === 409) {
        toast.add({
          title: $t('repository.error.conflict-title'),
          description: $t('repository.error.conflict-description'),
          color: 'error',
        })
      }
      else {
        toast.add({
          title: $t('error.server.title'),
          description: $t('error.server.description'),
          color: 'error',
        })
      }
    }
    else {
      toast.add({
        title: $t('error.unexpected.title'),
        description: $t('error.unexpected.description'),
        color: 'error',
      })
    }
  }
}
</script>

<template>
  <UPageHeader
    :title="$t('repository.new-title')"
    :description="$t('repositories.new-description')"
    :ui="{ root: 'py-2 mb-6', description: 'mt-4' }"
  />

  <div class="max-w-200 m-auto">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="text-2xl font-semibold">
            {{ $t('repository.details-title') }}
          </h2>
          <div />
        </div>
      </template>

      <RepositoryForm
        v-model="state"
        mode="new"
        @submit="onSubmit"
        @cancel="() => navigateTo('/repositories')"
      />
    </UCard>
  </div>
</template>
