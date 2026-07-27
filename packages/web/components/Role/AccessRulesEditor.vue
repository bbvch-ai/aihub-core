<template>
  <div class="flex flex-col gap-4">
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
              <li class="whitespace-nowrap"><Badge
                value="aihub.user.agent.>"
                severity="secondary"
                size="small"
              /> — {{ t('role.access_rules_help_all_agents') }}</li>
              <li class="whitespace-nowrap"><Badge
                value="aihub.user.agent.MyAgent.*"
                severity="secondary"
                size="small"
              /> — {{ t('role.access_rules_help_agent_instances') }}</li>
              <li class="whitespace-nowrap"><Badge
                value="aihub.user.service.knowledge"
                severity="secondary"
                size="small"
              /> — {{ t('role.access_rules_help_service') }}</li>
              <li class="whitespace-nowrap"><Badge
                value="aihub.admin.>"
                severity="secondary"
                size="small"
              /> — {{ t('role.access_rules_help_admin') }}</li>
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
        <Button
          type="button"
          icon="pi pi-th-large"
          :label="t('role.presets_button')"
          severity="secondary"
          outlined
          size="small"
          @click="(e: Event) => presetsPopover?.toggle(e)"
        />
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

      <Popover ref="presetsPopover">
        <div class="flex max-h-96 w-80 flex-col gap-3 overflow-y-auto">
          <span class="font-semibold">{{ t('role.presets_title') }}</span>
          <div
            v-for="group in presetGroups"
            :key="group.category"
            class="flex flex-col gap-1"
          >
            <span class="text-xs font-medium uppercase text-muted-color">{{ group.label }}</span>
            <button
              v-for="preset in group.presets"
              :key="preset.rule"
              type="button"
              class="flex flex-col items-start gap-1 rounded-md p-2 text-left hover:bg-surface-100 disabled:opacity-40 dark:hover:bg-surface-800"
              :disabled="rules.includes(preset.rule)"
              @click="addPreset(preset.rule)"
            >
              <span class="flex items-center gap-2 text-sm font-medium">
                {{ preset.name }}
                <i
                  v-if="rules.includes(preset.rule)"
                  class="pi pi-check text-green-500"
                />
              </span>
              <span class="text-xs text-muted-color">{{ preset.description }}</span>
              <Badge
                :value="preset.rule"
                severity="secondary"
                size="small"
              />
            </button>
          </div>
        </div>
      </Popover>
    </div>

    <AccessCapabilities
      :rules="rules"
      :restrict-to-tenant="restrictToTenant"
      @add="addPreset"
      @remove="remove"
    />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AccessCapabilities from './AccessCapabilities.vue'

import type { AccessPresetDto } from '@core/sdk/client'

import useAccessPresets from '@/composables/access/useAccessPresets'

const { t } = useI18n()

const accessRulesHelp = ref()
const presetsPopover = ref()
const rules = defineModel<string[]>('rules', { required: true })

const props = withDefaults(defineProps<{
  initialRules: string[]
  restrictToTenant?: boolean
}>(), {
  restrictToTenant: true,
})

const { presets } = useAccessPresets()

const presetGroups = computed<{ category: string, label: string, presets: AccessPresetDto[] }[]>(() => {
  const order = ['everything', 'agents', 'processes', 'models', 'knowledge']
  const byCategory = new Map<string, AccessPresetDto[]>()
  for (const preset of presets.value ?? []) {
    if (!byCategory.has(preset.category)) byCategory.set(preset.category, [])
    byCategory.get(preset.category)!.push(preset)
  }
  return [...byCategory.keys()]
    .sort((a, b) => order.indexOf(a) - order.indexOf(b))
    .map(category => ({ category, label: t(`role.preset_category_${category}`), presets: byCategory.get(category)! }))
})

const tableRows = computed(() =>
  rules.value.map(accessRule => ({ accessRule, id: accessRule })),
)

const newRule = ref('')

const isNew = (rule: string) => !props.initialRules.includes(rule)

const add = () => {
  if (!newRule.value) return
  if (!rules.value.includes(newRule.value)) rules.value.push(newRule.value)
  newRule.value = ''
}

const addPreset = (rule: string) => {
  if (!rules.value.includes(rule)) rules.value.push(rule)
}

const remove = (rule: string) => {
  rules.value = rules.value.filter(r => r !== rule)
}
</script>
