<script>
  import { setContext } from 'svelte';
  import { writable } from 'svelte/store';
  import { getOriginalComponent } from '@aihub/mods';
  import { guardContext, exportState } from './guard.js';

  export let chat;
  const Original = getOriginalComponent('src/lib/components/layout/Navbar/Menu.svelte');
  const policy = writable('checking');
  setContext(guardContext, policy);
  $: policy.set(exportState(chat));
</script>

<Original {...$$restProps} {chat}><slot /></Original>
