import DefaultTheme from 'vitepress/theme'
import CopyOrDownloadAsMarkdownButtons from 'vitepress-plugin-llms/vitepress-components/CopyOrDownloadAsMarkdownButtons.vue'
import './custom.css'
import Layout from './Layout.vue'
import NavigationBoxes from "../components/NavigationBoxes.vue";

// The generated LikeC4 bundle (public/likec4-webcomponent.js, gitignored, produced by
// `likec4:codegen`) is an IIFE meant to be loaded via a <script> tag — it registers the
// <likec4-view> custom element as a side effect. It must NOT be imported as an ES module:
// Rollup tree-shakes the unused dynamic import out of the production build. Instead we
// inject a classic <script> for the static asset, base-path aware, on the client only.
function loadLikeC4WebComponent() {
  if (import.meta.env.SSR || typeof document === 'undefined') return
  if (document.querySelector('script[data-likec4-webcomponent]')) return
  const script = document.createElement('script')
  script.src = `${import.meta.env.BASE_URL}likec4-webcomponent.js`
  script.setAttribute('data-likec4-webcomponent', '')
  document.head.appendChild(script)
}

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('CopyOrDownloadAsMarkdownButtons', CopyOrDownloadAsMarkdownButtons)
    app.component('NavigationBoxes', NavigationBoxes)
    loadLikeC4WebComponent()
  },
}