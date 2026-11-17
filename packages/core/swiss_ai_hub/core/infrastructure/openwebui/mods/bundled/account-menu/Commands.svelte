<script>
  import { user } from '@openwebui/stores';
  import { getOriginalComponent } from '@aihub/mods';

  const Original = getOriginalComponent('src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte');
  let commands;
  export let filteredItems = [];
  export const selectUp = () => commands.selectUp();
  export const selectDown = () => commands.selectDown();
  export const select = () => commands.select();
</script>

<Original {...$$restProps} canSettings={$user?.role === 'admin'} bind:filteredItems bind:this={commands} />
