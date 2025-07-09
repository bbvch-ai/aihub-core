<template>
  <div class="content">
    <div class="w-full max-w-2xl">
      <FormKit
        id="form"
        v-model="data"
        type="form"
        :submit-attrs="{
          inputClass: 'p-button p-component',
        }"
        @submit="submitHandler"
      >
        <FormKitSchema
          :schema="schema"
          :data="data"
        />
      </FormKit>

      <div class="mt-4">
        <pre>{{ data }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const schema = reactive(
  [
    {
      $el: 'h1',
      children: 'Title 1',
    },
    {
      $el: 'h2',
      children: 'Title 2',
    },
    {
      $el: 'h3',
      children: ['Register ', '$email'],
    },
    {
      $formkit: 'primeInputText',
      name: 'user.email',
      label: 'Email',
      help: 'This will be used for your account.',
      validation: 'required|email',
    },
    {
      $formkit: 'primeTextarea',
      name: 'comment',
      label: 'Text',
      validation: '',
      rows: '3',
    },
    {
      $formkit: 'primeAutoComplete',
      id: 'basic',
      name: 'id',
      dropdown: true,
      label: 'Object AutoComplete - Use [t]om',
      options: [
        {
          id: '1',
          name: 'Tom',
          value: '123',
        },
        {
          id: '2',
          name: 'Tim',
          value: '124',
        },
      ],
      optionLabel: 'name',
    },
    {
      $formkit: 'primeCheckbox',
      id: 'basic',
      name: 'basic',
      label: 'Basic Checkbox',
    },
    {
      $formkit: 'primeColorPicker',
      label: 'Select Color',
      name: 'color',
    },
    {
      $formkit: 'primeEditor',
      name: 'myEditor',
      label: 'Editor',
      validation: 'required',
      class: 'test',
    },
    {
      $formkit: 'primeInputMask',
      name: 'phone',
      label: 'Phone',
      mask: '+41 123 45 67',
      placeholder: '+41 ## ### ## ##',
      validation: 'required',
      validationVisibility: 'live',
    },
    {
      $formkit: 'primeInputNumber',
      name: 'firstNumber',
      label: 'Input Number',
      value: 1234,
      validation: 'max:10000',
      useGrouping: true,
      minFractionDigits: 2,
    },
    {
      $formkit: 'primeInputOtp',
      name: 'firstInput',
      label: 'Input OTP',
      length: 6,
      integerOnly: true,
      mask: true,
      variant: 'outlined',
    },
    {
      $formkit: 'primeListbox',
      name: 'cookie_notice',
      label: 'Cookie notice',
      value: 'hourly',
      optionLabel: 'label',
      optionValue: 'value',
      options: [
        {
          label: 'Every page load',
          value: 'refresh',
        },
        {
          label: 'Every hour',
          value: 'hourly',
        },
        {
          label: 'Every day',
          value: 'daily',
        },
      ],
      help: 'Cookie notice frequency ?',
    },
    {
      $formkit: 'primeMultiSelect',
      name: 'cookie_notice',
      label: 'Cookie notice MultiSelect',
      optionLabel: 'label',
      optionValue: 'value',
      options: [
        {
          label: 'Every page load',
          value: 'refresh',
        },
        {
          label: 'Every hour',
          value: 'hourly',
        },
        {
          label: 'Every day',
          value: 'daily',
        },
      ],
      help: 'Cookie notice frequency ?',
    },
    {
      $formkit: 'primePassword',
      name: 'password_confirm',
      label: 'Confirm password',
      help: 'Enter your new password again.',
      validation: 'required|confirm',
      toggleMask: true,
      validationLabel: 'password confirmation',
    },
    {
      $formkit: 'primeRadioButton',
      id: 'basic',
      label: 'Select',
      name: 'basic',
      optionLabel: 'label',
      optionValue: 'value',
      options: [
        {
          label: 'Every page load',
          value: 'refresh',
        },
        {
          label: 'Every hour',
          value: 'hourly',
        },
        {
          label: 'Every day',
          value: 'daily',
        },
      ],
    },
    {
      $formkit: 'primeSelect',
      name: 'selectValue',
      label: 'Cookie notice Select',
      value: 'hourly',
      optionLabel: 'label',
      optionValue: 'value',
      options: [
        {
          label: 'Every page load',
          value: 'refresh',
        },
        {
          label: 'Every hour',
          value: 'hourly',
        },
        {
          label: 'Every day',
          value: 'daily',
        },
      ],
      help: 'Cookie notice frequency ?',
    },
    {
      $formkit: 'primeSelectButton',
      label: 'SelectButton',
      name: 'selectButton',
      options: [
        {
          label: 'yes',
          value: 'YES',
        },
        {
          label: 'no',
          value: 'NO',
        },
        {
          label: 'maybe',
          value: 'MAYBE',
        },
      ],
      optionLabel: 'label',
      optionValue: 'value',
      value: 'MAYBE',
      unselectable: false,
    },
    {
      $formkit: 'primeSlider',
      name: 'slider',
      label: 'Use Slider',
      class: 'mt-2 w-72',
      min: 5,
      max: 100,
      step: 5,
      value: 10,
      validation: 'min:20|max:80',
    },
    {
      $formkit: 'primeToggleButton',
      label: 'ToggleButton',
      name: 'toggleButton',
    },
    {
      $formkit: 'primeToggleSwitch',
      name: 'eu_citizen',
      id: 'eu',
      suffix: 'Are you a european citizen: ',
    },
    {
      $formkit: 'primeRating',
      label: 'Select Rating',
      name: 'rating',
    },
    {
      $formkit: 'primeDatePicker',
      id: 'basic',
      name: 'basic',
      label: 'Basic',
      placeholder: 'MM/DD/YYYY',
      validation: 'required',
    },
    {
      $formkit: 'primeCascadeSelect',
      name: 'city',
      label: 'Cascade Select',
      optionLabel: 'cname',
      optionGroupLabel: 'name',
      optionGroupChildren: [
        'states',
        'cities',
      ],
      options: [
        {
          name: 'Australia',
          code: 'AU',
          states: [
            {
              name: 'New South Wales',
              cities: [
                {
                  cname: 'Sydney',
                  code: 'A-SY',
                },
                {
                  cname: 'Newcastle',
                  code: 'A-NE',
                },
                {
                  cname: 'Wollongong',
                  code: 'A-WO',
                },
              ],
            },
            {
              name: 'Queensland',
              cities: [
                {
                  cname: 'Brisbane',
                  code: 'A-BR',
                },
                {
                  cname: 'Townsville',
                  code: 'A-TO',
                },
              ],
            },
          ],
        },
        {
          name: 'Canada',
          code: 'CA',
          states: [
            {
              name: 'Quebec',
              cities: [
                {
                  cname: 'Montreal',
                  code: 'C-MO',
                },
                {
                  cname: 'Quebec City',
                  code: 'C-QU',
                },
              ],
            },
            {
              name: 'Ontario',
              cities: [
                {
                  cname: 'Ottawa',
                  code: 'C-OT',
                },
                {
                  cname: 'Toronto',
                  code: 'C-TO',
                },
              ],
            },
          ],
        },
        {
          name: 'United States',
          code: 'US',
          states: [
            {
              name: 'California',
              cities: [
                {
                  cname: 'Los Angeles',
                  code: 'US-LA',
                },
                {
                  cname: 'San Diego',
                  code: 'US-SD',
                },
                {
                  cname: 'San Francisco',
                  code: 'US-SF',
                },
              ],
            },
            {
              name: 'Florida',
              cities: [
                {
                  cname: 'Jacksonville',
                  code: 'US-JA',
                },
                {
                  cname: 'Miami',
                  code: 'US-MI',
                },
                {
                  cname: 'Tampa',
                  code: 'US-TA',
                },
                {
                  cname: 'Orlando',
                  code: 'US-OR',
                },
              ],
            },
            {
              name: 'Texas',
              cities: [
                {
                  cname: 'Austin',
                  code: 'US-AU',
                },
                {
                  cname: 'Dallas',
                  code: 'US-DA',
                },
                {
                  cname: 'Houston',
                  code: 'US-HO',
                },
              ],
            },
          ],
        },
      ],
      placeholder: 'Select a City',
    },
  ],
)

const data = ref({ email: 'tom@sfxcode.com' })

async function submitHandler() {
  await new Promise(resolve => setTimeout(resolve, 1000))
  console.log(data.value)
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}
.content :deep(.formkit-outer){
  @apply pt-3 pb-1;
}
.content :deep(h1) {
  @apply pt-3 pb-1 text-xl font-bold;
}

.content :deep(h2) {
  @apply pt-3 pb-1 text-lg font-bold;
}

.content :deep(h3) {
  @apply pt-3 pb-1 text-base font-bold;
}

.content :deep(h4) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h5) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h6) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(p) {
  @apply pt-3 pb-1 ;
}

.content :deep(blockquote) {
  @apply px-4 py-3 my-4 italic border-s-4 dark:border-gray-500/20 dark:bg-gray-800/20;
}

.content :deep(ul) {
  @apply list-disc list-outside mt-2;
}

.content :deep(ol) {
  @apply list-decimal list-outside mt-2;
}

.content :deep(ul > li) {
  @apply ml-4 mt-2;
}

.content :deep(ol > li) {
  @apply ml-6 mt-2;
}

.content :deep(strong) {
  @apply font-bold;
}

.content :deep(p a) {
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}
.content :deep(ul a) {
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}
.content :deep(table) {
  @apply my-8;
}
.content :deep(th) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left font-bold bg-surface-100 dark:bg-surface-800;
}
.content :deep(td) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left;
}
</style>
