import * as z from 'zod'

import type { MaybeRefOrGetter } from 'vue'
import type { FormErrorEvent } from '@nuxt/ui'

export type FormMode = 'new' | 'edit' | 'view'

const useRepositoryForm = () => {
  const defaultData: Required<RepositoryDetail> = {
    id: '',
    serviceName: '',
    serviceUrl: '',
    entityIds: [''],
    spConnectorId: '',
    active: false,
    created: '',
    groupsCount: 0,
    usersCount: 0,
  }
  const { groupsCount, usersCount, ...defaultForm } = defaultData
  const state = reactive<RepositoryForm>({ ...defaultForm })

  return { defaultData, state }
}

const useRepositorySchema = (mode?: MaybeRefOrGetter<FormMode>) => {
  const { t: $t } = useI18n()

  const createSchema = computed(() => z.object({
    serviceName: z.string().min(1, $t('repository.validation.serviceName.required')),
    serviceUrl: z.string()
      .min(1, $t('repository.validation.serviceUrl.required'))
      .url($t('repository.validation.serviceUrl.invalid')),
    entityIds: z.array(z.string().min(1, $t('repository.validation.entityIds.required')))
      .nonempty($t('repository.validation.entityIds.at-least-one')),
    active: z.boolean(),
  }))

  const updateSchema = computed(() => z.object({
    id: z.string().min(1, $t('repository.validation.id.required')),
    serviceName: z.string().min(1, $t('repository.validation.serviceName.required')),
    serviceUrl: z.string()
      .min(1, $t('repository.validation.serviceUrl.required'))
      .url($t('repository.validation.serviceUrl.invalid')),
    entityIds: z.array(z.string().min(1, $t('repository.validation.entityIds.required')))
      .nonempty($t('repository.validation.entityIds.at-least-one')),
    active: z.boolean(),
  }))

  const getSchemaByMode = (m: FormMode) => {
    return m === 'new' ? createSchema.value : updateSchema.value
  }

  const schema = mode
    ? computed(() => {
        const currentMode = toValue(mode)
        return getSchemaByMode(currentMode)
      })
    : undefined

  return { schema }
}

const useFormError = () => {
  const { t: $t } = useI18n()
  const toast = useToast()

  const handleFormError = (event: FormErrorEvent) => {
    toast.add({
      title: $t('error.validation.title'),
      description: $t('error.validation.description'),
      color: 'error',
    })

    focusFirstError(event)
  }

  return {
    handleFormError,
  }
}

const focusFirstError = (event: FormErrorEvent) => {
  const errorId = event?.errors?.[0]?.id
  if (import.meta.client && errorId) {
    nextTick(() => {
      const id = CSS.escape(errorId)
      const element = document.querySelector(`#${id}`) as HTMLElement
      element?.focus()
      element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
}

export { useRepositoryForm, useRepositorySchema, useFormError }
