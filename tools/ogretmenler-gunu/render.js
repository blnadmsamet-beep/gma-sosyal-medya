// Film a deterministic HTML page scene by scene with Playwright → ffmpeg (image2pipe).
// usage: node render.js config.json [segmentName ...]
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const cfgPath = path.resolve(process.argv[2]);
const only = process.argv.slice(3);
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const FPS = cfg.fps || 30;
const outDir = cfg.outDir;
fs.mkdirSync(outDir, { recursive: true });

function encodeSegment(name, t0, t1, page) {
  return new Promise(async (resolve, reject) => {
    const tmp = path.join(outDir, `${name}.tmp.mp4`);
    const fin = path.join(outDir, `${name}.mp4`);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(FPS), '-i', '-',
      '-vf', 'format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp]);
    let err = '';
    ff.stderr.on('data', d => err += d.toString());
    ff.on('close', code => {
      if (code === 0) { fs.renameSync(tmp, fin); resolve(fin); }
      else reject(new Error(`ffmpeg exit ${code} for ${name}: ${err}`));
    });
    const n0 = Math.round(t0 * FPS), n1 = Math.round(t1 * FPS);
    const started = Date.now();
    for (let n = n0; n < n1; n++) {
      const t = n / FPS;
      await page.evaluate((tt) => render(tt), t);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    console.log(`${name}: ${n1 - n0} frames in ${((Date.now() - started) / 1000).toFixed(1)}s`);
  });
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(cfg.page));
  await page.evaluate((c) => setup(c), cfg.pageConfig);
  // wait for images to load
  await page.evaluate(() => Promise.all([...document.images].map(im => im.complete ? 1 : new Promise(r => { im.onload = r; im.onerror = r; }))));
  await page.waitForTimeout(300);
  if (cfg.stills) {
    fs.mkdirSync(cfg.stillsDir, { recursive: true });
    for (const t of cfg.stills) {
      await page.evaluate((tt) => render(tt), t);
      await page.screenshot({ path: path.join(cfg.stillsDir, `still_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 90 });
    }
    console.log('stills done');
  }
  if (!cfg.stillsOnly) {
    for (const seg of cfg.segments) {
      if (only.length && !only.includes(seg.name)) continue;
      await encodeSegment(seg.name, seg.t0, seg.t1, page);
    }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
