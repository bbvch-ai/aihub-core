// Shows text that its trigger truncates. The tooltip's own size is capped so an unbroken
// identifier of any length still fits the viewport, and autoHide is off so the pointer can
// move into the tooltip to scroll whatever exceeds that cap.
export const longTextTooltip = (text: string) => ({
  value: text,
  autoHide: false,
  pt: {
    root: { class: '!max-w-[min(32rem,90vw)]' },
    text: { class: 'max-h-[40vh] overflow-y-auto [overflow-wrap:anywhere]' },
  },
})
