// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'
import unicorn from 'eslint-plugin-unicorn'
import { globalIgnores } from 'eslint/config'

export default withNuxt([
  // Your custom configs here
  unicorn.configs.recommended,
  globalIgnores(['htmlcov/', '.tox/']),
  {
    name: 'stylistic',
    rules: {
      'camelcase': ['error', { properties: 'always' }],
      'no-console': 'error',
      'vue/first-attribute-linebreak': ['error', { singleline: 'beside', multiline: 'below' }],
      'vue/max-attributes-per-line': [
        'warn', { singleline: { max: 4 }, multiline: { max: 4 } },
      ],
      '@stylistic/function-call-spacing': ['error', 'never'],
      '@stylistic/max-len': ['error', { code: 100 }],
    },
  },
  {
    files: ['**/app/**/*.vue'],
    rules: {
      'unicorn/filename-case': [
        'error', { case: 'pascalCase', ignore: ['app.vue'] },
      ],
      'vue/no-multiple-template-root': 'off',
    },
  },
  {
    files: ['**/*.{ts,js'],
    rules: {
      'unicorn/filename-case': ['error', { case: 'camelCase' }],
    },
  },
  {
    files: ['**/app/{pages,layouts}/**/*.vue'],
    rules: {
      'unicorn/filename-case': ['error', { case: 'kebabCase' }],
    },
  },
])
