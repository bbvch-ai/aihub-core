export const guardContext = Symbol('AI Hub PDF export guard');

export function exportState(chat) {
  return Object.values(chat?.chat?.history?.messages ?? {}).some(message => message.models?.length > 1)
    ? 'blocked' : 'allowed';
}
