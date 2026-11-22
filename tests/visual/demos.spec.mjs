// One snapshot per component page of the site: the demos are the visual source of truth of the system, and
// verify-ds.py reads text, not pixels (DESIGN.md › Versioning, release checklist step 0). v6.1.0.
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PAGE = pathToFileURL(path.join(ROOT, 'index.html')).href;

// the component pages, read from the registry the site ships: a new component gets its snapshot with no edit here
const pages = JSON.parse(fs.readFileSync(path.join(ROOT, 'r', 'registry.json'), 'utf8')).items
  .map((it) => JSON.parse(fs.readFileSync(path.join(ROOT, 'r', `${it.name}.json`), 'utf8')))
  .map((it) => ({ name: it.name, id: String((it.meta && it.meta.amaca && it.meta.amaca.site) || '').split('#')[1] }))
  .filter((p) => p.id);

// what changes on every run and is not the system: the live chat demo (its anatomy is shot), the numbers that count
// up, the loader's mark (an SVG that animates inside its own file, where no animation setting reaches) and its label,
// which cycles
const MASK = ['.chat-demo', '[data-count-to]', '[data-pie-total]', 'img[src*="logo-loader"]', '.loader-label'];

for (const p of pages) {
  test(p.name, async ({ page }) => {
    // the date picker opens on today: a fixed day keeps its snapshot the same tomorrow
    await page.clock.setFixedTime(new Date('2026-11-22T10:00:00'));
    await page.goto(`${PAGE}#${p.id}`);
    await page.evaluate(() => document.fonts.ready);
    const section = page.locator(`section.section#${p.id}`);
    await expect(section).toHaveClass(/\bactive\b/);
    await page.waitForTimeout(1500);   // the page's own entrance and the charts' draw, settled
    // one snapshot per subsection, not per page: 0.1% of a whole page is a card's border on ten cards, so a page-sized
    // shot let a one-step border change pass; a subsection is the size the threshold was measured on (v6.1.0)
    const blocks = section.locator(':scope > .page-header, :scope > .subsection');
    const n = await blocks.count();
    expect(n).toBeGreaterThan(0);
    for (let i = 0; i < n; i++) {
      await expect(blocks.nth(i)).toHaveScreenshot(`${p.name}-${String(i + 1).padStart(2, '0')}.png`, { mask: MASK.map((m) => page.locator(m)) });
    }
  });
}
