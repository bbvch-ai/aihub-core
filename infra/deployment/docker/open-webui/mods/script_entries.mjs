export const scriptEntries = Object.freeze({
  bootstrap: Object.freeze({ prefix: 'bootstrap/', nativeRuntime: false, after: [], timeout: 15000 }),
  frontend: Object.freeze({ prefix: 'frontend/', nativeRuntime: true, after: ['bootstrap'] })
});
