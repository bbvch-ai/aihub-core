<script>
  import { getOriginalComponent } from '@aihub/mods';

  const Original = getOriginalComponent('src/lib/components/chat/MessageInput/TerminalMenu.svelte');
  export let show = false;
</script>

<Original {...$$restProps} bind:show canConfigureDirect={false} />
