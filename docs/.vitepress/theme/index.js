import DefaultTheme from 'vitepress/theme'
import CopyOrDownloadAsMarkdownButtons from 'vitepress-plugin-llms/vitepress-components/CopyOrDownloadAsMarkdownButtons.vue'
import './custom.css'
import Layout from './Layout.vue'
import NavigationBoxes from "../components/NavigationBoxes.vue";

// Side-effect import: registers <likec4-view> as a global custom element.
// Bundle is regenerated from docs/likec4/*.c4 by the `likec4:codegen` script.
if (!import.meta.env.SSR) {
  import('./likec4-webcomponent.js')
}

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('CopyOrDownloadAsMarkdownButtons', CopyOrDownloadAsMarkdownButtons)
    app.component('NavigationBoxes', NavigationBoxes)
  },
}