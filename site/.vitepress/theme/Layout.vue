<script setup>
import DefaultTheme from 'vitepress/theme';
import { onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vitepress';
import Ribbon from './Ribbon.vue';

const { Layout } = DefaultTheme;
const route = useRoute();
let live = null, motion = null;
onMounted(async () => {
  live = await import('./live.js');
  live.start();
  motion = await import('./motion.js');
  motion.start();
});
watch(() => route.path, () => nextTick(() => { live?.routeChanged(); motion?.routeChanged(); }));
</script>

<template>
  <Layout>
    <template #layout-bottom>
      <Ribbon />
      <div class="lrows" aria-hidden="true"></div>
      <div class="lstat" role="status">
        <span class="msg">Ready</span>
      </div>
    </template>
  </Layout>
</template>
