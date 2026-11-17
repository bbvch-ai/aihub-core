<script>
  import { getContext } from 'svelte';
  import { getOriginalComponent } from '@aihub/mods';
  import { guardContext } from './guard.js';

  const Original = getOriginalComponent('src/lib/components/common/DropdownSub.svelte');
  const policy = getContext(guardContext);
  const i18n = getContext('i18n');
  const messages = {
    en: { blocked: 'PDF export is unavailable for chats with several models side by side. Use plain text instead.', checking: 'Checking chat…' },
    de: { blocked: 'PDF-Export ist bei Antworten mehrerer Modelle nebeneinander nicht verfügbar. Verwenden Sie stattdessen Klartext.', checking: 'Chat wird geprüft…' },
    fr: { blocked: 'L’export PDF est indisponible pour les chats avec plusieurs modèles côte à côte. Utilisez le texte brut.', checking: 'Vérification du chat…' },
    it: { blocked: 'L’esportazione PDF non è disponibile per chat con più modelli affiancati. Usa il testo semplice.', checking: 'Verifica della chat…' }
  };
  $: labels = messages[$i18n.language?.split('-')[0]] ?? messages.en;

  function guard(node, labels) {
    const button = [...node.querySelectorAll('button')].find(button => /\.pdf\b/i.test(button.textContent));
    if (!button) return;
    let state;
    const render = () => {
      button.disabled = state !== 'allowed';
      button.setAttribute('aria-disabled', String(button.disabled));
      button.setAttribute('data-aihub-pdf-guard', state);
      button.title = labels[state] ?? '';
      button.style.opacity = button.disabled ? '0.5' : '';
      button.style.cursor = button.disabled ? 'not-allowed' : '';
    };
    const unsubscribe = policy.subscribe(value => { state = value; render(); });
    return {
      update(value) { labels = value; render(); },
      destroy: unsubscribe
    };
  }
</script>

<Original {...$$restProps}>
  <svelte:fragment slot="trigger"><slot name="trigger" /></svelte:fragment>
  {#if policy}
    <div style="display: contents" use:guard={labels}><slot /></div>
  {:else}
    <slot />
  {/if}
</Original>
