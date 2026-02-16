<template>
  <div class="flex flex-col gap-2 rounded-lg border border-surface-200 p-4 dark:border-surface-700">
    <span class="flex items-center gap-1 font-semibold">
      {{ t('role.access_rules') }}
      <i
        class="pi pi-question-circle text-surface-400"
        @mouseenter="(e: Event) => accessRulesHelp?.show(e)"
        @mouseleave="() => accessRulesHelp?.hide()"
      />
      <Popover ref="accessRulesHelp">
        <div class="text-sm font-normal">
          <p class="mb-2">
            {{ t('role.access_rules_help_intro') }}
          </p>
          <ul class="flex flex-col gap-1">
            <li class="whitespace-nowrap"><Badge value="aihub.user.agent.>" severity="secondary" size="small" /> — {{ t('role.access_rules_help_all_agents') }}</li>
            <li class="whitespace-nowrap"><Badge value="aihub.user.agent.MyAgent.*" severity="secondary" size="small" /> — {{ t('role.access_rules_help_agent_instances') }}</li>
            <li class="whitespace-nowrap"><Badge value="aihub.user.service.knowledge" severity="secondary" size="small" /> — {{ t('role.access_rules_help_service') }}</li>
            <li class="whitespace-nowrap"><Badge value="aihub.admin.>" severity="secondary" size="small" /> — {{ t('role.access_rules_help_admin') }}</li>
          </ul>
        </div>
      </Popover>
    </span>
    <DataTable
      v-if="rules.length"
      :value="tableRows"
      data-key="id"
      size="small"
    >
      <Column field="accessRule">
        <template #body="{ data }">
          <Badge
            :value="data.accessRule"
            severity="secondary"
            class="border border-gray-400/30"
          />
        </template>
      </Column>
      <Column class="w-24 !text-end">
        <template #body="{ data }">
          <Tag
            v-if="isNew(data.accessRule)"
            :value="t('role.is_new')"
            severity="success"
          />
        </template>
      </Column>
      <Column class="w-12">
        <template #body="{ data }">
          <Button
            icon="pi pi-times"
            severity="secondary"
            variant="text"
            rounded
            size="small"
            @click="remove(data.accessRule)"
          />
        </template>
      </Column>
    </DataTable>
    <span
      v-else
      class="text-sm italic text-muted-color"
    >
      {{ t('role.no_access_rules') }}
    </span>
    <div class="flex items-center gap-2">
      <InputText
        v-model="newRule"
        :placeholder="t('role.add_access_role')"
        size="small"
        class="flex-1"
        @keyup.enter="add"
      />
      <Button
        type="button"
        icon="pi pi-plus"
        :label="t('role.add_button')"
        size="small"
        :disabled="!newRule"
        @click="add"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const accessRulesHelp = ref()
const rules = defineModel<string[]>('rules', { required: true })

const props = defineProps<{
  initialRules: string[]
}>()

const tableRows = computed(() =>
  rules.value.map(accessRule => ({ accessRule, id: accessRule })),
)

const newRule = ref('')

const isNew = (rule: string) => !props.initialRules.includes(rule)

const add = () => {
  if (!newRule.value) return
  rules.value.push(newRule.value)
  newRule.value = ''
}

const remove = (rule: string) => {
  rules.value = rules.value.filter(r => r !== rule)
}
</script>
