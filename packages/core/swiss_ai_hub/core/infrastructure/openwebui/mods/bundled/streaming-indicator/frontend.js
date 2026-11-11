import stylesheet from './style.css';

export async function activate({ signal, onDispose }) {
  const response = await fetch(stylesheet, { signal, credentials: 'same-origin' });
  if (!response.ok) throw new Error(`Cannot load the streaming indicator stylesheet: ${response.status}`);
  const style = document.createElement('style');
  style.textContent = await response.text();
  signal.throwIfAborted();
  document.head.append(style);
  onDispose(() => style.remove());
}
