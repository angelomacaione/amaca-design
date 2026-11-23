// The visual regression pass of the site's demos (v6.1.0). It runs in CI only, in the Playwright image pinned in
// .github/workflows/visual.yml: fonts draw differently between systems, so a snapshot taken on a Mac never matches.
// Two passes: the motion the reader gets, settled, and reduced motion. A snapshot changes only on purpose
// (Run workflow, update = true), never because a run happened to differ.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  snapshotPathTemplate: '{testDir}/__snapshots__/{projectName}/{arg}{ext}',
  fullyParallel: true,
  retries: 1,   // a real difference fails twice; one that does not repeat is timing, and is reported as flaky
  reporter: [['list']],
  timeout: 60000,
  expect: {
    timeout: 20000,   // a long section takes more than the default 5s to give two equal frames
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.001,   // 0.1%: a border one step lighter is 0.20%, a title one weight lighter 0.25% (measured 2026-11-22)
      threshold: 0,               // per pixel: the default 0.2 lets one ramp step through as 'the same colour'
      animations: 'disabled',     // finite animations land on their last frame, loops stop
      caret: 'hide',
      stylePath: './screenshot.css',
      scale: 'css',
    },
  },
  use: { viewport: { width: 1440, height: 1000 } },
  projects: [
    { name: 'motion', use: { reducedMotion: 'no-preference' } },
    { name: 'reduced', use: { reducedMotion: 'reduce' } },
  ],
});
