<script>
  import { onMount } from 'svelte';
  import { getOriginalComponent } from '@aihub/mods';
  import { recovery, locale, reset } from './state.js';

  const Original = getOriginalComponent('src/lib/components/chat/MessageInput/CallOverlay.svelte');
  export let files = [];
  export let eventTarget;
  const messages = {
    en: 'Voice reply unavailable. The answer is shown as text.',
    de: 'Sprachausgabe nicht verfügbar. Die Antwort wird als Text angezeigt.',
    fr: 'Réponse vocale indisponible. La réponse est affichée sous forme de texte.',
    it: 'Risposta vocale non disponibile. La risposta è visualizzata come testo.'
  };
  onMount(() => {
    reset();
    eventTarget.addEventListener('chat:start', reset);
    return () => {
      eventTarget.removeEventListener('chat:start', reset);
      reset();
    };
  });
</script>

<div class="voice-recovery">
  <Original {...$$restProps} {eventTarget} bind:files on:close />
  {#if $recovery.failed}
    <div class="voice-status" data-aihub-tts-status role="status">
      {messages[$locale.split('-')[0]] ?? messages.en}
    </div>
  {/if}
</div>

<style>
  .voice-recovery {
    position: relative;
    display: flex;
    justify-content: center;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .voice-status {
    position: absolute;
    top: 0.75rem;
    left: 1rem;
    right: 1rem;
    z-index: 20;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    background: #f3f4f6;
    color: #4b5563;
    font-size: 0.75rem;
    text-align: center;
  }

  :global(.dark) .voice-status {
    background: #1f2937;
    color: #d1d5db;
  }
</style>
