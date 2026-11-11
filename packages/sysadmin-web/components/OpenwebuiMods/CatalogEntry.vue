<template>
  <section class="rounded-xl border border-surface-200 p-4 dark:border-surface-700">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0">
        <h3 class="break-words font-semibold">{{ manifest?.name ?? selection.mod_id }}</h3>
        <p class="text-sm text-surface-500">{{ manifest?.version }}<span v-if="entry?.builtin"> · {{ t('openwebui_mods.automatic_version') }}</span></p>
        <p v-if="manifest?.description" class="mt-1 text-sm">{{ manifest.description }}</p>
      </div>
      <ToggleSwitch v-model="selection.enabled" class="shrink-0" :disabled="!selection.enabled && ((!entry?.builtin && !selection.publication) || (requiresRestart && !globalScope))" :aria-label="t('openwebui_mods.enable', { name: manifest?.name ?? selection.mod_id })" />
    </div>
    <Message v-if="error" severity="warn" :closable="false" class="mt-3">{{ t('openwebui_mods.metadata_error') }}</Message>
    <p v-if="requiresRestart" class="mt-3 text-sm text-surface-500">{{ t(globalScope ? 'openwebui_mods.global.mod_restart' : 'openwebui_mods.global.global_only') }}</p>
    <p v-if="!entry?.builtin && !selection.publication" class="mt-3 text-sm text-surface-500">{{ t('openwebui_mods.select_before_enable') }}</p>
    <details class="mt-4">
      <summary class="cursor-pointer text-sm">{{ t('openwebui_mods.settings') }}</summary>
      <p :id="`${selection.mod_id}-help`" class="my-2 text-sm text-surface-500">{{ t(globalScope ? 'openwebui_mods.global.settings_help' : 'openwebui_mods.settings_help') }}</p>
      <Textarea v-model="settings" :aria-label="t('openwebui_mods.settings')" :aria-describedby="`${selection.mod_id}-help`" :invalid="invalid" rows="6" spellcheck="false" class="w-full font-mono text-sm" />
      <p v-if="invalid" role="alert" class="text-sm text-red-600">{{ t('openwebui_mods.settings_invalid') }}</p>
    </details>
    <Button v-if="!entry?.builtin" class="mt-3" :label="t('openwebui_mods.versions')" severity="secondary" text size="small" @click="emit('versions', source)" />
  </section>
</template>

<script setup lang="ts">
import { getOpenwebuiModPublication, getOpenwebuiModRevision, type OpenWebuiModSelection, type OpenWebuiModCatalogEntry, type OpenWebuiModRevisionResponse } from '~/sdk/client'

const selection = defineModel<OpenWebuiModSelection>({ required: true })
const settings = defineModel<string>('settings', { required: true })
const props = defineProps<{ entry?: OpenWebuiModCatalogEntry, invalid: boolean, globalScope?: boolean }>()
const emit = defineEmits<{ versions: [OpenWebuiModRevisionResponse | undefined] }>()
const { t } = useI18n()
const { data: source, error } = useQuery({
  key: () => ['openwebui-mod-source-for-publication', selection.value.publication ?? ''],
  enabled: () => !props.entry?.builtin && Boolean(selection.value.publication),
  query: async () => {
    const publication = await getOpenwebuiModPublication({ composable: '$fetch', path: { revision: selection.value.publication! } })
    return getOpenwebuiModRevision({ composable: '$fetch', path: { revision: publication.manifest.source_revision } })
  },
})
const manifest = computed(() => props.entry?.builtin ? props.entry.manifest : source.value?.manifest ?? props.entry?.manifest)
const requiresRestart = computed(() => manifest.value?.backend_restart_required || Boolean(manifest.value?.backend_overrides?.['open_webui.main:lifespan']))
</script>
