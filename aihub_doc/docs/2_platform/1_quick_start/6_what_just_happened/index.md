---
title: What Just Happened?
index: 6
---

# What Just Happened?

As you can see it is straight forward to get the Swiss AI-Hub Platform up and running. But we have only scratched the
surface of what is possible, hopefully the potential it has is clear. Your next steps are totally up to you. You can
start using the platform as is with no modification and come back once you see the need, or you can dive deeper into
other topics if you are interested. In any case as it stands now the platform is fully functional and ready for use.

If this short introduction was too quick, please just go back and revisit the parts that are still unclear. If not, then
welcome to the Swiss AI-Hub Platform. There is so much more to unpack which we will do in the following chapters.

## Where to go next?

Here are some options on where you can go next, depending on what you are interested in.

<script setup>
import NavigationBoxes from '../../../../.vitepress/components/NavigationBoxes.vue'

const navigationItems = [
  {
    title: 'Architecture',
    description: 'Dive deep into the architecture behind the platform and get to know its ins and outs.',
    href: '../../2_architecture/'
  },
  {
    title: 'Deployment',
    description: 'Learn how to deploy the platform for yourself and run it from wherever you want.',
    href: '../../3_deployment_guide/'
  },
  {
    title: 'Customization',
    description: 'Get straight into customizing the platform to meet your specific needs.',
    href: '../../4_customization/'
  }
]
</script>

<NavigationBoxes :items="navigationItems" />
