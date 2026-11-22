// One cookie-free visit count per page view, sent to tablient.com, which counts by day, page and referring site and
// stores nothing that identifies a visitor (see /privacy). Only on the real site, and never when the browser asks
// not to be tracked (Do Not Track, Global Privacy Control).
export const NEWS_URL = 'https://tablient.com/api/news';
const HIT_URL = 'https://tablient.com/api/hit';

export function countVisit(path, referrer = '') {
  try {
    if (location.hostname !== 'cellprose.com' || navigator.doNotTrack === '1' || navigator.globalPrivacyControl) return;
    navigator.sendBeacon?.(HIT_URL, JSON.stringify({ p: path, r: referrer }));
  } catch { /* counting is optional */ }
}
