import { expect, test } from '@playwright/test'
import JSZip from 'jszip'

test('replacement boundaries preserve the native component contract and contain render failures', async ({ page, request }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const token = process.env.OPENWEBUI_MODS_CONTROL_TOKEN
  expect(token, 'Set OPENWEBUI_MODS_CONTROL_TOKEN for the disposable host').toBeTruthy()
  const source = new JSZip()
  source.file('mod.json', JSON.stringify({ format: 1, id: 'boundary-test', name: 'Boundary test', version: '1', frontend: 'main.js' }))
  source.file('main.js', "export { default as Child } from './Child.svelte'; export { default as Parent } from './Parent.svelte';")
  source.file('Child.svelte', `<script>
      import { getContext, createEventDispatcher, onDestroy } from 'svelte';
      export let value = 0;
      export let destroyed;
      const label = getContext('label');
      const crash = getContext('crash');
      const dispatch = createEventDispatcher();
      onDestroy(destroyed);
      export function read() { return value; }
      function explode() { throw new Error('Boundary fixture failed'); }
    </script>
    {#if $crash}{explode()}{/if}
    <button on:click={() => { value++; dispatch('change', value); }}>{label}:{value}</button>`)
  source.file('Parent.svelte', `<script>
      export let Child;
      export let destroyed;
      let value = 3;
      let child;
      const events = [];
      export function inspect() { return { value, method: child.read(), events }; }
    </script>
    <Child bind:value bind:this={child} {destroyed} on:change={event => events.push(event.detail)} />`)
  const response = await request.post('/_aihub/mods/control/compile', {
    headers: { Authorization: `Bearer ${token}` }, data: await source.generateAsync({ type: 'nodebuffer' }),
  })
  expect(response.status(), response.ok() ? '' : await response.text()).toBe(200)
  const archive = await JSZip.loadAsync(await response.body())
  const fixtures = {
    child: await archive.file('files/frontend/Child.svelte.mjs')!.async('string'),
    parent: await archive.file('files/frontend/Parent.svelte.mjs')!.async('string'),
  }
  await page.goto('/auth')
  const result = await page.evaluate(async (fixtures) => {
    const origin = location.origin
    const runtime = await import(/* @vite-ignore */ `${origin}/_aihub/mods/runtime.js`)
    const svelte = runtime.getModule('svelte')
    const store = runtime.getModule('svelte/store')
    async function load(code: string) {
      const url = URL.createObjectURL(new Blob([code], { type: 'text/javascript' }))
      try { return (await import(/* @vite-ignore */ url)).default }
      finally { URL.revokeObjectURL(url) }
    }
    const Child = await load(fixtures.child)
    const Parent = await load(fixtures.parent)
    let destroyed = 0
    const failures: string[] = []
    const crash = store.writable(false)
    const target = document.createElement('div')
    document.body.append(target)
    const options = {
      target,
      props: { Child: runtime.guardComponent(Child, (error: Error) => failures.push(error.message)), destroyed: () => destroyed++ },
      context: new Map<string, unknown>([['label', 'Native context'], ['crash', crash]]),
    }
    const instance = svelte.mount(Parent, options)
    svelte.flushSync()
    const before = { text: target.textContent?.trim(), method: instance.inspect().method }
    target.querySelector('button')!.click()
    svelte.flushSync()
    const after = { text: target.textContent?.trim(), ...instance.inspect() }
    crash.set(true)
    svelte.flushSync()
    await Promise.resolve()
    const failed = { text: target.textContent?.trim(), failures: [...failures], destroyed }
    await svelte.unmount(instance)
    const initiallyBroken = svelte.mount(Parent, options)
    svelte.flushSync()
    await Promise.resolve()
    await svelte.unmount(initiallyBroken)
    target.remove()
    return { before, after, failed, initialFailureCaught: failures.length === 2 }
  }, fixtures)
  expect(result.before).toEqual({ text: 'Native context:3', method: 3 })
  expect(result.after).toEqual({ text: 'Native context:4', method: 4, value: 4, events: [4] })
  expect(result.failed).toEqual({ text: '', failures: ['Boundary fixture failed'], destroyed: 1 })
  expect(result.initialFailureCaught).toBe(true)
  expect(errors).toEqual([])
})
