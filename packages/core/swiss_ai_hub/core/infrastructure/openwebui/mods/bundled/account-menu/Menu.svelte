<script>
  import { getContext } from 'svelte';
  import { mobile, showSidebar } from '@openwebui/stores';
  import { getOriginalComponent } from '@aihub/mods';

  const i18n = getContext('i18n');
  const AdminIcon = getOriginalComponent('src/lib/components/layout/Sidebar/icons/User.svelte');

  export let role = '';

  $: expanded = $mobile || $showSidebar;

  function navigate(event) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if ($mobile) showSidebar.set(false);
  }
</script>

{#if role === 'admin'}
  <a
    href="/admin"
    class="group flex items-center transition text-gray-700 dark:text-gray-300 {expanded
      ? 'w-full space-x-2 rounded-xl px-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-900'
      : 'size-8 justify-center'}"
    aria-label={$i18n.t('Admin Panel')}
    title={$i18n.t('Admin Panel')}
    draggable="false"
    on:click={navigate}
    data-aihub-admin-link
  >
    <div
      class="self-center flex shrink-0 items-center justify-center {expanded
        ? 'size-4'
        : 'size-[calc(30px*var(--app-text-scale,1))] rounded-lg transition group-hover:bg-gray-100 dark:group-hover:bg-gray-900'}"
    >
      <AdminIcon className="size-4" strokeWidth="1.5" />
    </div>
    {#if expanded}
      <span class="self-center translate-y-[0.5px] text-[0.8125rem] leading-5">{$i18n.t('Admin Panel')}</span>
    {/if}
  </a>
{/if}

<style>
  a:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
</style>
