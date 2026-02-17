/*
 * Copyright (C) 2026 National Institute of Informatics.
 */

/**
 * Nuxt plugin to intercept fetch requests for authentication handling
 */
export default defineNuxtPlugin(() => {
  const { baseURL } = useAppConfig()

  globalThis.$fetch = $fetch.create({
    baseURL,
    credentials: 'include',
    onResponseError: ({ response }) => {
      const { handleFetchError } = useErrorHandling()
      handleFetchError({ response })
    },
  })
})
