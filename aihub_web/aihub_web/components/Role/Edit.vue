<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-2">
      <FloatLabel variant="in">
        <InputText
          id="in_label_name"
          v-model="role.name"
          rows="5"
          cols="30"
          class="w-full"
        />
        <label for="in_label_name">
          {{ t('role.name') }}
        </label>
      </FloatLabel>
      <FloatLabel variant="in">
        <Textarea
          id="in_label_description"
          v-model="role.description"
          rows="5"
          cols="30"
          class="w-full"
        />
        <label for="in_label_description">
          {{ t('role.description') }}
        </label>
      </FloatLabel>
    </div>
    <DataTable
      :value="accessRules"
      data-key="id"
    >
      <Column
        field="accessRule"
        :header="t('role.access_rules')"
      >
        <template #body="{ data }">
          <Badge
            :value="data.accessRule"
            severity="secondary"
            class="border border-gray-400/30"
          />
        </template>
      </Column>
      <Column
        class="w-24 !text-end"
      >
        <template #body="{ data }">
          <Tag
            v-if="isNewAccessRule(data.accessRule)"
            :value="t('role.is_new')"
            severity="success"
          />
        </template>
      </Column>
      <Column
        class="w-12"
      >
        <template #body="{ data }">
          <Button
            icon="pi pi-times"
            severity="secondary"
            variant="text"
            rounded
            size="small"
            @click="removeAccessRule(data.accessRule)"
          />
        </template>
      </Column>
    </DataTable>
    <div class="flex gap-2">
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-lock-open" />
        </InputGroupAddon>
        <InputText
          v-model="newRule"
          :placeholder="t('role.add_access_role')"
          @click.enter="addRule"
        />
      </InputGroup>
      <div>
        <Button
          type="button"
          :label="t('role.add_button')"
          icon="pi pi-plus"
          :disabled="!newRule"
          @click="addRule"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { CreateRoleRequest, RoleResponse } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  modelValue: RoleResponse | CreateRoleRequest
}>()

const emit = defineEmits<{
  'update:modelValue': [RoleResponse | CreateRoleRequest]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const role = ref<RoleResponse | CreateRoleRequest>(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  role.value = newValue
}, { deep: true })

const accessRules = computed(() => {
  return role.value.access_rules?.map((accessRule: string) => {
    return {
      accessRule,
      id: accessRule,
    }
  }) || []
})

const newRule = ref<string>('')

watch(() => [role.value.name, role.value.description, JSON.stringify(role.value.access_rules)], () => {
  emit('update:modelValue', role.value)
})

const isNewAccessRule = (accessRule: string) => {
  return !initialAccessRules.value?.includes(accessRule)
}

const addRule = () => {
  if (!newRule.value) return
  if (!role.value.access_rules) {
    role.value.access_rules = []
  }
  role.value.access_rules.push(newRule.value)
  newRule.value = ''
}

const removeAccessRule = (accessRule: string) => {
  if (!role.value.access_rules) return
  role.value.access_rules = role.value.access_rules.filter(
    (rule: string) => rule !== accessRule,
  )
}
</script>

<style scoped>

</style>
