<script>
  import { onDestroy, setContext } from 'svelte';
  import { writable } from 'svelte/store';
  import { fetch, getOriginalComponent } from '@aihub/mods';
  import { guardContext, exportState } from './guard.js';

  export let chatId = '';
  export let onOpen = () => {};
  export let onClose = () => {};
  const Original = getOriginalComponent('src/lib/components/layout/Sidebar/ChatMenu.svelte');
  const policy = writable('checking');
  setContext(guardContext, policy);
  let pending;

  async function open() {
    pending?.abort();
    const controller = new AbortController();
    pending = controller;
    policy.set('checking');
    onOpen();
    try {
      const response = await fetch(`/api/v1/chats/${encodeURIComponent(chatId)}`, {
        headers: { Authorization: `Bearer ${localStorage.token}` }, signal: controller.signal
      });
      if (!response.ok) throw new Error(`Chat lookup failed: ${response.status}`);
      const chat = await response.json();
      if (!controller.signal.aborted) policy.set(exportState(chat));
    } catch (error) {
      if (controller.signal.aborted) return;
      console.warn('[AI Hub PDF export]', error);
      policy.set('allowed');
    }
  }

  function close() { pending?.abort(); onClose(); }
  onDestroy(() => pending?.abort());
</script>

<Original {...$$restProps} {chatId} onOpen={open} onClose={close}><slot /></Original>
