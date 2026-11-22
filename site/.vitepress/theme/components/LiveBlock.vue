<script setup>
// A section of a page: a white sheet whose green tab shows its name and, once live.js has measured it, the cells it covers.
defineProps({ win: { type: String, required: true }, id: { type: String, default: undefined } });
</script>
<template>
  <section :id="id" class="block" :data-win="win"><slot /></section>
</template>
