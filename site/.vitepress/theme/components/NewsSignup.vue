<script setup>
// Launch-news sign-up, kept by tablient.com (double opt-in: nothing is added until the emailed link is confirmed).
import { ref } from 'vue';
import { withBase } from 'vitepress';
import { NEWS_URL } from '../lib/beacon.js';

const props = defineProps({ source: { type: String, default: 'site' } });
const email = ref(''), msg = ref(''), busy = ref(false);
async function submit() {
  busy.value = true;
  try {
    const body = new FormData();
    body.set('email', email.value);
    body.set('source', props.source);
    const r = await fetch(NEWS_URL, { method: 'POST', body });
    const d = await r.json().catch(() => ({}));
    msg.value = typeof d.detail === 'string' ? d.detail : r.ok ? 'Check your inbox.' : 'Could not sign you up.';
    if (r.ok) email.value = '';
  } catch { msg.value = 'Could not sign you up. Try again later.'; }
  busy.value = false;
}
</script>

<template>
  <form class="news" @submit.prevent="submit">
    <label class="sr-only" :for="`news-${source}`">Email address</label>
    <input :id="`news-${source}`" v-model="email" type="email" autocomplete="email" required placeholder="you@company.com">
    <button class="btn" type="submit" :disabled="busy">Keep me posted</button>
  </form>
  <p class="muted small">A few emails a year: releases and benchmark results. You confirm by email first, and every email has a link to leave. <a :href="withBase('/privacy')">Privacy</a>.</p>
  <p v-if="msg" class="small" role="status">{{ msg }}</p>
</template>
