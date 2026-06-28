// @ts-check
import { defineConfig } from 'astro/config';

import svelte from '@astrojs/svelte';

import tailwindcss from '@tailwindcss/vite';

import sentry from '@sentry/astro';


// https://astro.build/config
export default defineConfig({
  integrations: [svelte(), sentry()],

  vite: {
    plugins: [tailwindcss()]
  }
});