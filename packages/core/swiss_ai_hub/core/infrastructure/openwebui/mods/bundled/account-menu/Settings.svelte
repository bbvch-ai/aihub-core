<script>
  import { user } from '@openwebui/stores';
  import { getOriginalComponent } from '@aihub/mods';

  const Original = getOriginalComponent('src/lib/components/chat/SettingsModal.svelte');
  const hiddenTabs = ['admin:authentication', 'admin:connections', 'admin:db'];
  export let show = false;

  function filterTabs(tabs) {
    return [
      ...tabs.filter(tab => tab.id.startsWith('admin:') && !hiddenTabs.includes(tab.id)),
      ...tabs.filter(tab => tab.id === 'about')
    ];
  }

  $: if ($user?.role !== 'admin') show = false;
</script>

{#if $user?.role === 'admin'}
  <Original bind:show {filterTabs} />
{/if}
