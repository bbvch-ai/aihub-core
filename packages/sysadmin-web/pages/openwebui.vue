<template>
  <StructuralScreen>
    <template #top>
      <SysadminNavigation />
    </template>
    <StructuralColumn
      :title="t('openwebui_mods.global.title')"
      size="large"
    >
      <OpenwebuiModsCatalog
        tenant-id=""
        global-scope
      />
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'sysadmin' })
const { t } = useI18n()
</script>
