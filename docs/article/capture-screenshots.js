// Run from the repository root with Playwright CLI and capture-screenshots.config.json.
// Only navigation, viewport changes, scrolling and native screenshots; no DOM/data edits.
async (page) => {
  const base = 'http://127.0.0.1:8765/examples/document-assistant/docs/workbench/index.html';
  await page.goto(base);
  await page.getByRole('tab', { name: '总览', exact: false }).waitFor();
  if (await page.evaluate(() => devicePixelRatio) !== 2) {
    throw new Error('Use capture-screenshots.config.json: deviceScaleFactor must be 2.');
  }
  await page.setViewportSize({ width: 1440, height: 1130 });
  await page.getByLabel('迭代范围').selectOption('');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.waitForTimeout(350);
  await page.screenshot({ path: 'docs/article/assets/screenshot-overview.png', scale: 'device' });

  await page.getByRole('tab', { name: '需求澄清与方案决策' }).click();
  await page.setViewportSize({ width: 390, height: 2200 });
  for (const [selector, expected, name] of [
    ['#question-Q-SHARE', 'open', 'question'],
    ['#proposal-PROP-SHARE', 'proposed', 'options'],
  ]) {
    const card = page.locator(selector);
    if (await card.getAttribute('data-canonical-status') !== expected) {
      throw new Error(`Demonstration state changed for ${selector}; review before capturing.`);
    }
    if (await page.locator('input[type=radio]:checked').count()) {
      throw new Error('The demonstration must retain unselected answers and proposals.');
    }
    await card.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await card.screenshot({ path: `docs/article/assets/screenshot-${name}.png`, scale: 'device' });
  }

  await page.getByRole('tab', { name: '上线版本管理' }).click();
  await page.setViewportSize({ width: 390, height: 3000 });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.waitForTimeout(350);
  const first = await page.locator('#release-records').boundingBox();
  const last = await page.locator('#gates').boundingBox();
  const clip = { x: first.x, y: first.y, width: first.width, height: last.y + last.height - first.y };
  if (clip.y + clip.height > 3000) throw new Error('Release content exceeds capture viewport; review framing.');
  await page.screenshot({ path: 'docs/article/assets/screenshot-release.png', clip, scale: 'device' });
  return { demonstration: 'Entirely fictional document-assistant example', checkedRadios: await page.locator('input[type=radio]:checked').count(), releaseClip: clip };
}
