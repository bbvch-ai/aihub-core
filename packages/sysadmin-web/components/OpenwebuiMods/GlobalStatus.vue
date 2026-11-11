<template>
  <div class="flex flex-col gap-3">
    <Message v-if="state.restart_required" severity="warn" :closable="false">{{ t('openwebui_mods.global.pending') }}</Message>
    <Message v-else :severity="ready ? 'success' : 'info'" :closable="false">{{ t(ready ? 'openwebui_mods.global.ready' : 'openwebui_mods.global.applying', { ready: readyWorkers, total: state.expected_workers }) }}</Message>
    <Message v-for="error in errors" :key="error" severity="error" :closable="false">{{ error }}</Message>
    <Message v-if="failure" severity="error" :closable="false">{{ failure }}</Message>
    <Button v-if="state.restart_required || restarting" :label="t(restarting ? 'openwebui_mods.global.restarting' : 'openwebui_mods.global.restart')" icon="pi pi-refresh" severity="warn" class="self-start" :loading="restarting" :disabled="restarting" @click="confirmRestart" />
  </div>
</template>

<script setup lang="ts">
import { restartOpenwebuiForMods, type OpenWebuiModGlobalState } from '~/sdk/client'
import { useTimeoutFn } from '@vueuse/core'

const props = defineProps<{ state: OpenWebuiModGlobalState }>()
const emit = defineEmits<{ refresh: [] }>()
const { t } = useI18n()
const confirm = useConfirm()
const errorMessage = useOpenwebuiModError()
const restarting = ref(false)
const failure = ref('')
const previousBoot = ref('')
const errors = computed(() => [...new Set(props.state.workers.map(worker => worker.error).filter((error): error is string => Boolean(error)))])
const readyWorkers = computed(() => props.state.workers.filter(worker => worker.ready && !worker.error && worker.version === props.state.active_version).length)
const ready = computed(() => readyWorkers.value >= props.state.expected_workers)
const { start: startTimeout, stop: stopTimeout } = useTimeoutFn(() => {
  restarting.value = false
  failure.value = t('openwebui_mods.global.restart_timeout')
}, 120000, { immediate: false })

watch(() => props.state, (state) => {
  if (previousBoot.value && state.boot_id !== previousBoot.value && ready.value && !state.restart_required) {
    restarting.value = false
    failure.value = ''
    stopTimeout()
  }
})

function confirmRestart() {
  const version = props.state.configuration.version ?? 0
  confirm.require({
    header: t('openwebui_mods.global.restart'),
    message: t('openwebui_mods.global.restart_confirm'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('tenant_admin.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('openwebui_mods.global.restart'), severity: 'warn' },
    accept: async () => {
      failure.value = ''
      previousBoot.value = props.state.boot_id
      restarting.value = true
      startTimeout()
      try {
        await restartOpenwebuiForMods({ composable: '$fetch', query: { version } })
        emit('refresh')
      }
      catch (error) {
        restarting.value = false
        stopTimeout()
        failure.value = errorMessage(error, t('openwebui_mods.global.restart_error'))
      }
    },
  })
}
</script>
