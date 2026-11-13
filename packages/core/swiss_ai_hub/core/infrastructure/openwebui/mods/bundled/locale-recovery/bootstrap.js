import locales from './locales.json';

export function activate() {
  const saved = localStorage.getItem('locale');
  // Open WebUI provides its own fallback for French regional codes.
  if (saved && !locales.includes(saved) && !/^fr(-|$)/.test(saved)) localStorage.setItem('locale', 'en-US');
}
