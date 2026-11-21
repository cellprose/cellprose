<script setup>
import { onMounted, ref } from 'vue';
import { makeViewer } from '../lib/viewer.js';
import { loadSample } from '../lib/samples.js';

const props = defineProps({ sample: String, focus: String, mode: { type: String, default: 'bands' }, tabs: Boolean, name: String });
const host = ref(null);
const error = ref('');
onMounted(async () => {
  const v = makeViewer(host.value, { mode: props.mode, tabs: props.tabs, focus: props.focus });
  try {
    const s = await loadSample(props.sample);
    v.load(s.text, s.csv, props.name || s.file);
  } catch (e) {
    error.value = e.message;
  }
});
</script>
<template>
  <div ref="host"></div>
  <p v-if="error" class="warnbox">{{ error }}</p>
</template>
