<template>
  <div class="flex flex-col gap-4">
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
      <div
        v-for="position in POSITIONS"
        :key="position.key"
      >
        <label
          :for="`cron-${position.key}`"
          class="mb-1 block text-sm font-medium"
        >
          {{ t(`lib.cron.${position.key}.label`) }}
        </label>
        <InputText
          :id="`cron-${position.key}`"
          :model-value="schedule[position.key]"
          :aria-label="t(`lib.cron.${position.key}.label`)"
          class="w-full font-mono"
          @update:model-value="(value) => updatePosition(position.key, value ?? '')"
        />
        <small class="mt-1 block text-surface-500">{{ position.range }}</small>
      </div>
    </div>

    <div>
      <label
        for="cron-timezone"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('lib.cron.timezone.label') }}
      </label>
      <Select
        v-model="timezone"
        input-id="cron-timezone"
        :options="timezoneOptions"
        :placeholder="timezonePlaceholder ?? t('lib.cron.timezone.placeholder')"
        :filter="filter"
        class="w-full"
      />
      <small class="mt-1 block text-surface-500">{{ t('lib.cron.timezone.help') }}</small>
    </div>

    <small class="text-surface-500">
      {{ t('lib.cron.expression') }} <code class="font-mono">{{ expression }}</code>
    </small>
  </div>
</template>

<script setup lang="ts">
/**
 * Editor for a backend `AgentSchedule`: the five cron positions plus an IANA timezone.
 *
 * The emitted value is the schedule object in the backend's own field names, so it round-trips through
 * `config_data` untouched — the scheduler reads those keys directly. Positions are kept separate rather than
 * joined into one "0 12 * * *" string because that is how `AgentSchedule` stores them, and flattening here would
 * make every consumer parse it back apart.
 *
 * Deliberately has no presets and no plain-language summary — that is #1581, which extends this component rather
 * than replacing it.
 */

interface CronSchedule {
  minute: string
  hour: string
  day_of_month: string
  month: string
  day_of_week: string
  timezone: string
}

type CronPosition = Exclude<keyof CronSchedule, 'timezone'>

interface CronInputProps {
  context: {
    node: {
      input: (value: CronSchedule) => void
    }
    value?: CronSchedule | null
    attrs: Record<string, unknown>
    timezonePlaceholder?: string
    filter?: boolean
  }
}

const props = defineProps<CronInputProps>()
const { t } = useI18n()

const POSITIONS: { key: CronPosition, range: string }[] = [
  { key: 'minute', range: '0-59' },
  { key: 'hour', range: '0-23' },
  { key: 'day_of_month', range: '1-31' },
  { key: 'month', range: '1-12' },
  { key: 'day_of_week', range: '0-6' },
]

// Shown in the inputs the moment the field is enabled, never applied behind the user's back. `AgentSchedule`
// requires all five positions and has no defaults, so leaving them blank would save a schedule the scheduler then
// skips with only a log line to say why. Hourly is the least surprising visible starting point — `* * * * *` would
// commit an admin to a run every minute for merely ticking the enable box.
const HOURLY: CronSchedule = {
  minute: '0',
  hour: '*',
  day_of_month: '*',
  month: '*',
  day_of_week: '*',
  timezone: resolveBrowserTimezone(),
}

const timezonePlaceholder = computed(() => props.context.timezonePlaceholder)
const filter = computed(() => props.context.filter ?? true)

const schedule = computed<CronSchedule>(() => props.context.value ?? HOURLY)

const expression = computed(() =>
  POSITIONS.map(position => schedule.value[position.key] || '?').join(' '),
)

const timezone = computed({
  get: () => schedule.value.timezone,
  set: (value: string) => emitValue({ ...schedule.value, timezone: value }),
})

const timezoneOptions = computed<string[]>(() => {
  // Not every engine implements supportedValuesOf; without it the admin can still keep the resolved zone.
  const supported = (Intl as { supportedValuesOf?: (key: string) => string[] }).supportedValuesOf
  return supported ? supported('timeZone') : [schedule.value.timezone, 'UTC']
})

function resolveBrowserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  }
  catch {
    return 'UTC'
  }
}

function updatePosition(position: CronPosition, value: string) {
  emitValue({ ...schedule.value, [position]: value.trim() })
}

// Always emits every key: a partial schedule passes the generated submission schema (which cannot carry
// AgentSchedule's croniter and timezone validators) and is then skipped at tick time with nothing but a log line.
function emitValue(value: CronSchedule) {
  props.context.node.input({ ...value })
}

// Seed the stored value so enabling the field yields a complete, valid schedule even if the admin saves without
// touching an input — what the inputs show and what gets saved must not diverge.
onMounted(() => {
  if (!props.context.value) emitValue(HOURLY)
})
</script>
