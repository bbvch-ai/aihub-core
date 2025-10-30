---
title: Was ist gerade passiert?
source_sha: 75cd585f0450f02fed97ef04383552ad8fd0fc8f487d4de5632c25eb1f0e1753
---

@SkypeForBusiness [WIP]

# Was ist gerade passiert?

Wenn diese kurze Einführung zu schnell war, gehen Sie bitte zurück und sehen Sie sich die Teile noch einmal an, die noch
unklar sind. Wenn nicht, dann willkommen zur Swiss AI-Hub Plattform. Es gibt noch so viel mehr zu entdecken, was wir in
den nächsten Kapiteln tun werden.

## Wohin als Nächstes?

Es gibt tatsächlich drei Optionen, wohin Sie als Nächstes gehen können.

<script setup>
import NavigationBoxes from '../../../../.vitepress/components/NavigationBoxes.vue'

const navigationItems = [
  {
    title: 'Tiefer Einblick',
    description: 'Tauchen Sie tief in die Architektur hinter der Plattform ein und lernen Sie deren Aufbau und Funktionsweise kennen.',
    href: '/de/docs/2_architecture/'
  },
  {
    title: 'Bereitstellung',
    description: 'Erfahren Sie, wie Sie die Plattform selbst bereitstellen und von überall aus betreiben können.',
    href: '/de/docs/3_deployment_guide/'
  },
  {
    title: 'Anpassung',
    description: 'Beginnen Sie direkt mit der Anpassung der Plattform an Ihre spezifischen Anforderungen.',
    href: '/de/docs/4_customization/'
  }
]
</script>

<NavigationBoxes :items="navigationItems" />
