function replaceOnce(source, changes, before, after, id) {
  const start = source.indexOf(before);
  if (start === -1 || source.indexOf(before, start + before.length) !== -1) {
    throw new Error(`Open WebUI ${id} changed; review its component adapter before upgrading`);
  }
  changes.overwrite(start, start + before.length, after);
}

export function adaptComponentProps(source, id, changes) {
  const replace = (before, after) => replaceOnce(source, changes, before, after, id);
  if (id === 'src/lib/components/chat/SettingsModal.svelte') {
    const show = 'export let show: boolean | string | SettingsModalRequest = false;';
    replace(show, `${show}\n\texport let filterTabs: (tabs: SettingsTab[]) => SettingsTab[] = tabs => tabs;`);
    replace('availableSettings = getAvailableSettings(allSettings, adminSettings);',
      'availableSettings = filterTabs(getAvailableSettings(allSettings, adminSettings));');
    const fallback = "!availableSettings.some((tab) => tab.id === selectedTab)\n\t) {\n\t\tselectedTab = 'general';";
    replace(fallback, fallback.replace("'general'", 'availableSettings[0].id'));
  } else if (id === 'src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte') {
    replace('export let canCompact = false;', 'export let canCompact = false;\n\texport let canSettings = true;');
    replace("...('settings'.startsWith(query.toLowerCase())", "...(canSettings && 'settings'.startsWith(query.toLowerCase())");
  } else if (id === 'src/lib/components/chat/MessageInput/TerminalMenu.svelte') {
    replace('export let disabled = false;', 'export let disabled = false;\n\texport let canConfigureDirect = true;');
    const action = "showSettings.set('tools');";
    const at = source.indexOf(action);
    const start = source.lastIndexOf('<Tooltip', at);
    const end = source.indexOf('</Tooltip>', at) + '</Tooltip>'.length;
    if (at === -1 || source.indexOf(action, at + action.length) !== -1 || start === -1 || end < at) {
      throw new Error(`Open WebUI ${id} changed; review its component adapter before upgrading`);
    }
    changes.prependLeft(start, '{#if canConfigureDirect}');
    changes.appendRight(end, '{/if}');
  }
}
