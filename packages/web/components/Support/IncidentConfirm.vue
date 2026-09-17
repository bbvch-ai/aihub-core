<template>
  <!--
    Its own group, and its own instance, because the app-wide ConfirmDialog in
    app.vue carries no width: a prose message stretches it across the viewport
    and renders as one unwrapped line. Constraining that dialog would reshape
    every confirmation in the app, so this one owns its size instead.

    Rendered once by the layout — the button that opens it appears both in the
    rail and in the settings popover, and the chat page raises it too.
  -->
  <ConfirmDialog
    group="incident"
    :draggable="false"
    :style="{ width: '30rem', maxWidth: '90vw' }"
  />
</template>
