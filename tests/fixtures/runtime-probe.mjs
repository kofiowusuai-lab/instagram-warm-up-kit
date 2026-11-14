import { readFileSync } from 'node:fs';
export default async function ({ page, log }) {
  if (typeof readFileSync !== 'function') throw new Error('Node filesystem import unavailable');
  const probe = await page.context().newPage();
  try {
    await probe.goto('about:blank');
    log('PASS: Node filesystem import and isolated session tab supported');
  } finally {
    await probe.close();
  }
}
