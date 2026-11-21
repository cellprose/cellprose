// The Live Sheet theme: VitePress's default theme, drawn as a spreadsheet. The page has a name box and formula bar,
// column letters and row numbers (live.js).
import DefaultTheme from 'vitepress/theme';
import { inBrowser } from 'vitepress';
import { countVisit } from './lib/beacon.js';
import Layout from './Layout.vue';
import LiveBlock from './components/LiveBlock.vue';
import HomeStats from './components/HomeStats.vue';
import SheetViewer from './components/SheetViewer.vue';
import HowItWorks from './components/HowItWorks.vue';
import OverrideGame from './components/OverrideGame.vue';
import ReplayRace from './components/ReplayRace.vue';
import RunChart from './components/RunChart.vue';
import ScoreCost from './components/ScoreCost.vue';
import BenchPage from './components/BenchPage.vue';
import InstallTabs from './components/InstallTabs.vue';
import GitDiff from './components/GitDiff.vue';
import Playground from './components/Playground.vue';
import NewsSignup from './components/NewsSignup.vue';
import './style.css';
import './ribbon.css';

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app, router }) {
    for (const [name, c] of Object.entries({ LiveBlock, HomeStats, SheetViewer, HowItWorks, OverrideGame, ReplayRace, RunChart, ScoreCost, BenchPage, InstallTabs, Playground, GitDiff, NewsSignup })) {
      app.component(name, c);
    }
    if (inBrowser) {
      // VitePress calls onAfterRouteChange for the initial load too, so do not also count it directly.
      // The referrer belongs to the landing only; later in-site navigations send none.
      let first = true;
      router.onAfterRouteChange = (to) => {
        countVisit(new URL(to, location.href).pathname, first ? document.referrer : '');
        first = false;
      };
    }
  },
};
