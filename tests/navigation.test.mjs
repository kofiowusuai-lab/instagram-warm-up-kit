import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import test from 'node:test';
const source = readFileSync(new URL('../scripts/ig-soft-warmup.mjs', import.meta.url), 'utf8');
const section = source.slice(source.indexOf('  const openSection = '), source.indexOf('  const checkNotifications = '));
for (const [href, url] of [['/', 'https://www.instagram.com/'], ['/direct/inbox/', 'https://www.instagram.com/direct/inbox/'], ['/reels/', 'https://www.instagram.com/reels/']]) {
  test(`section ${href} navigates without depending on a stalled UI click`, async () => {
    const destinations = [];
    let checked = false;
    const page = {
      locator: () => ({first: () => ({count: async () => 1, click: async () => {throw new Error('reproduced stalled click');}})}),
      goto: async (url, options) => { destinations.push(url); assert.equal(options.waitUntil, 'domcontentloaded'); }
    };
    const open = vm.runInNewContext(section + '\nopenSection', {
      page, wait: async () => {}, rnd: a => a, dismissPopups: async () => {}, checkInstagram: async () => {checked = true;}
    });
    await open(href, url);
    assert.deepEqual(destinations, [url]);
    assert.equal(checked, true, 'Instagram warning checks still run');
  });
}

const actions = source.slice(source.indexOf('  const doAction = '), source.indexOf('  // the topic\'s own results:'));
for (const visible of [true, false]) {
  test(`dialog author visit ignores hidden links; visible author ${visible}`, async () => {
    const targets = [];
    const anchor = (href, isVisible) => ({
      innerText: 'creator', getAttribute: () => href, setAttribute: () => {},
      getClientRects: () => isVisible ? [{}] : [],
      getBoundingClientRect: () => ({width: isVisible ? 40 : 0, height: isVisible ? 20 : 0})
    });
    const links = [anchor('/hidden/', false), ...(visible ? [anchor('/creator/', true)] : [])];
    const document = {querySelector: () => ({querySelectorAll: () => links})};
    const page = {
      evaluate: async callback => vm.runInNewContext('(' + callback.toString() + ')()', { document }),
      locator: () => ({click: async () => { throw new Error('hidden author click'); }}),
      goto: async url => {targets.push(url);}
    };
    const action = vm.runInNewContext(actions + '\ndoAction', {page, followsStopped:false, browseProfile: async () => 'visited', note: () => {}});
    await action('visit', true);
    assert.deepEqual(targets, visible ? ['https://www.instagram.com/creator/'] : []);
  });
}
