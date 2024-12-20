import type { Meta } from '@storybook/vue3'
import type { StoryFn } from '@storybook/csf'
import Button from './Button.vue'

export default {
  title: 'Components/Button',
  component: Button,
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'primary', 'secondary', 'destructive', 'outline', 'ghost', 'link'],
    },
    size: {
      control: { type: 'select' },
      options: ['default', 'sm', 'lg'],
    },
    class: { control: 'text' },
    onClick: { action: 'clicked' },
  },
} as Meta<typeof Button>

const Template: StoryFn<typeof Button> = args => ({
  components: { Button },
  setup() {
    return { args }
  },
  template: '<Button v-bind="args">{{ args.label }}</Button>',
})

export const Default = Template.bind({})
Default.args = {
  variant: 'default',
  size: 'default',
  label: 'Default Button',
}

export const Primary = Template.bind({})
Primary.args = {
  variant: 'primary',
  size: 'default',
  label: 'Primary Button',
}

export const Secondary = Template.bind({})
Secondary.args = {
  variant: 'secondary',
  size: 'default',
  label: 'Secondary Button',
}

export const Destructive = Template.bind({})
Destructive.args = {
  variant: 'destructive',
  size: 'default',
  label: 'Destructive Button',
}

export const Outline = Template.bind({})
Outline.args = {
  variant: 'outline',
  size: 'default',
  label: 'Outline Button',
}

export const Ghost = Template.bind({})
Ghost.args = {
  variant: 'ghost',
  size: 'default',
  label: 'Ghost Button',
}

export const Link = Template.bind({})
Link.args = {
  variant: 'link',
  size: 'default',
  label: 'Link Button',
}

export const Small = Template.bind({})
Small.args = {
  variant: 'default',
  size: 'sm',
  label: 'Small Button',
}

export const Large = Template.bind({})
Large.args = {
  variant: 'default',
  size: 'lg',
  label: 'Large Button',
}
