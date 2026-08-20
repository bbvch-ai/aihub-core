<template>
  <Select
    v-model="selectedTenant"
    :options="tenants ?? []"
    option-label="name"
    option-value="id"
    :aria-label="placeholder ?? t('common.selectTenant')"
    :placeholder="placeholder ?? t('common.selectTenant')"
    :filter="filter"
    :loading="isLoading"
    class="w-full"
  >
    <template #option="{ option }">
      <div class="flex items-center gap-2">
        <Icon
          name="mage:building-a"
          size="1.2em"
        />
        <span>{{ option.name }}</span>
      </div>
    </template>
  </Select>
</template>

<script setup lang="ts">
interface TenantSelectProps {
  context: {
    node: { input: (value: string | null) => void }
    value?: string | null
    placeholder?: string
    filter?: boolean
  }
}

const props = defineProps<TenantSelectProps>()
const { t } = useI18n()

const { tenants, tenantsAreLoading } = useTenantMemberships()
const { tenantId } = useTenant()

const placeholder = computed(() => props.context.placeholder)
const filter = computed(() => props.context.filter ?? true)
const isLoading = computed(() => tenantsAreLoading.value)

const selectedTenant = computed({
  get: () => props.context.value ?? null,
  set: (value: string | null) => {
    props.context.node.input(value)
  },
})

// Pre-select the user's active tenant on a fresh field, while leaving an
// already-configured value (editing an existing instance) untouched.
// `preSelected` makes this idempotent: a commit re-renders the form, and re-emitting the same
// value from a re-created input would commit again, driving the input/commit loop that froze
// the configuration tab.
let preSelected: string | null = null

watch(
  [tenantId, () => props.context.value],
  ([active, current]) => {
    if (current || !active || preSelected === active) return
    preSelected = active
    props.context.node.input(active)
  },
  { immediate: true },
)
</script>
