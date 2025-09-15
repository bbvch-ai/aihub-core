import DefaultTheme from 'vitepress/theme'
import './custom.css'
import GradientBackground from '../components/GradientBackground.vue'
import { h } from 'vue'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      // Insert your component in the sidebar slot
      'sidebar-nav-before': () => h(GradientBackground),

      'home-hero-before': () => h('div', { class: 'home-gradient-wrapper' }, [
        h(GradientBackground)
      ])

    })
  }
}