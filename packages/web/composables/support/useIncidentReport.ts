// Opening the report dialog. Shared state rather than a prop, because it is raised from three
// places — the app rail, the settings popover, and a per-message action inside the chat iframe —
// while the dialog itself is mounted once by the layout.
export const useIncidentReport = () => {
  const isOpen = useState<boolean>('incident-dialog-open', () => false)

  const open = (): void => {
    isOpen.value = true
  }

  const close = (): void => {
    isOpen.value = false
  }

  return { isOpen, open, close }
}
