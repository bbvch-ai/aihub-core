import DefaultTheme from 'vitepress/theme'
import CopyOrDownloadAsMarkdownButtons from 'vitepress-plugin-llms/vitepress-components/CopyOrDownloadAsMarkdownButtons.vue'
import './custom.css'
import Layout from './Layout.vue'
import NavigationBoxes from "../components/NavigationBoxes.vue";

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('CopyOrDownloadAsMarkdownButtons', CopyOrDownloadAsMarkdownButtons)
    app.component('NavigationBoxes', NavigationBoxes)
  },
}