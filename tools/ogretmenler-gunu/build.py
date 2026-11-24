#!/usr/bin/env python3
"""Build the GMA Öğretmenler Günü film: timing from narration → config → render → concat → mix."""
import json, subprocess, re, sys, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
FPS = 30
NARR_OFFSET = 1.0          # narration starts 1 s in
XF = 0.8                   # crossfade length

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stdout); print(r.stderr); raise SystemExit(f"failed: {' '.join(map(str, cmd))}")
    return r

def duration(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout.strip())

def silences(p, noise="-38dB", d=0.22):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    gaps = []
    for s in starts:
        e = next((e for e in ends if e > s), None)
        if e is not None: gaps.append((s, e))
    return gaps

def first_sound(p, noise="-38dB"):
    g = silences(p, noise, 0.05)
    if g and g[0][0] < 0.05: return g[0][1]
    return 0.0

def line_starts(narr, n_lines=9):
    """Pick the (n_lines-1) longest internal pauses as line boundaries; return list of line start times (narration-relative)."""
    dur = duration(narr)
    gaps = [(s, e) for s, e in silences(narr) if s > 0.3 and e < dur - 0.2]
    gaps_sorted = sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[: n_lines - 1]
    bounds = sorted(e for s, e in gaps_sorted)          # a line starts where its preceding pause ends
    starts = [first_sound(narr)] + bounds
    return starts, dur, sorted(gaps)

def ensure_logo():
    """assets/logo.png: the GMA logo cropped from the closing card of an existing ad film (repo videos/reklam)."""
    logo = ASSETS / "logo.png"
    if logo.exists(): return
    ASSETS.mkdir(exist_ok=True)
    src = None
    for cand in [ROOT.parent.parent / "videos/reklam/reklam-05-dort-yonlu-gelisim.mp4", Path.cwd() / "videos/reklam/reklam-05-dort-yonlu-gelisim.mp4"]:
        if cand.exists(): src = cand; break
    if src is None: raise SystemExit("assets/logo.png missing and reklam-05 film not found to extract it from")
    frame = ASSETS / "_card.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "37.0", "-i", str(src), "-frames:v", "1", str(frame)])
    from PIL import Image
    Image.open(frame).crop((355, 586, 726, 1042)).save(logo)
    frame.unlink()

def main(images, narr, music, out_mp4, test=False):
    ensure_logo()
    starts, ndur, gaps = line_starts(narr)
    if len(starts) < 9:
        print("WARNING: only", len(starts), "line starts found:", starts)
    L = [s + NARR_OFFSET for s in starts]           # absolute times of L1..L9
    while len(L) < 9: L.append(L[-1] + 3.0)
    nend = ndur + NARR_OFFSET
    print("line starts:", [round(x, 2) for x in L], "narration end:", round(nend, 2))
    # internal pause inside L6 (between L6 start and L7 start) → split point for T3/T4
    l6_gaps = [(s + NARR_OFFSET, e + NARR_OFFSET) for s, e in gaps if L[5] - NARR_OFFSET + 0.8 < s and e < L[6] - NARR_OFFSET - 0.25]
    l6_split = max(l6_gaps, key=lambda g: g[1] - g[0])[1] - 0.15 if l6_gaps else (L[5] + L[6]) / 2
    if L[6] - l6_split < 1.2 or l6_split - L[5] < 1.2: l6_split = (L[5] + L[6]) / 2
    card_t0 = L[8] - 0.25
    card_t1 = nend + 3.6
    total = card_t1
    scenes = [
        {"img": 1, "t0": 0.0, "t1": L[2] - XF, "fadeIn": 1.6, "kb": {"s0": 1.0, "s1": 1.10, "x0": 0, "y0": 0, "x1": 0, "y1": -24}, "glow": {"a": 1.0, "x": 540, "y": 1100, "r": 540}},
        {"img": 2, "t0": L[2] - XF, "t1": L[4] - XF, "kb": {"s0": 1.07, "s1": 1.0, "x0": 0, "y0": -10, "x1": 0, "y1": 6}, "glow": {"a": 0.55, "x": 540, "y": 1180, "r": 480}},
        {"img": 3, "t0": L[4] - XF, "t1": L[5] - XF, "kb": {"s0": 1.0, "s1": 1.07, "x0": 0, "y0": 12, "x1": 0, "y1": -12}, "glow": {"a": 0.45, "x": 540, "y": 1800, "r": 640}},
        {"img": 4, "t0": L[5] - XF, "t1": L[6] - XF, "kb": {"s0": 1.08, "s1": 1.0, "x0": -22, "y0": 0, "x1": 18, "y1": 0}},
        {"img": 5, "t0": L[6] - XF, "t1": L[7] - XF, "kb": {"s0": 1.0, "s1": 1.08, "x0": 0, "y0": 24, "x1": 0, "y1": -22}},
        {"img": 1, "layer": "LF", "t0": L[7] - XF, "t1": card_t0 - XF, "dim": 0.42, "kb": {"s0": 1.12, "s1": 1.18, "x0": 0, "y0": 60, "x1": 0, "y1": 40}, "glow": {"a": 0.8, "x": 540, "y": 1160, "r": 560}},
    ]
    texts = {
        "T1": [0.9, L[2] - 1.0, 1.0, 0.6],
        "T2": [L[2] + 0.5, L[4] - 0.5, 0.8, 0.6],
        "T3": [L[5] + 0.1, l6_split - 0.05, 0.6, 0.4],
        "T4": [l6_split + 0.05, L[6] - 0.4, 0.6, 0.4],
        "T5": [L[6] + 0.4, L[7] - 0.5, 0.7, 0.6],
        "T6": [L[7] + 0.2, card_t0 - 0.9, 0.9, 0.7],
    }
    page_cfg = {
        "images": images, "logo": str(ASSETS / "logo.png"), "xfade": XF, "scenes": scenes,
        "shade": [[L[2] - 0.2, L[4] - 0.3], [L[5] - 0.2, L[6] - 0.2], [L[6] + 0.1, L[7] - 0.3]],
        "motes": [[0.6, L[2] + 0.5], [L[6] - 0.3, L[7] + 0.4], [L[7], card_t0 - 0.9]],
        "texts": texts, "card": {"t0": card_t0, "t1": card_t1, "fadeW": 1.2},
    }
    names = ["A_kandil", "B_ogretmen", "C_cocuklar", "D_sabah", "E_fenerler", "F_kutlama", "G_logo"]
    cuts = [0.0, L[2] + 0.3, L[4] + 0.3, L[5] + 0.3, L[6] + 0.3, L[7] + 0.3, card_t0 + 0.9, total]
    segments = [{"name": n, "t0": round(cuts[i], 3), "t1": round(cuts[i + 1], 3)} for i, n in enumerate(names)]
    stills = [0.6, 2.5, L[2] + 1.2, L[4] + 1.0, L[5] + 1.0, l6_split + 0.8, L[6] + 1.2, L[7] + 1.4, card_t0 + 2.5, total - 0.3]
    cfg = {"fps": FPS, "page": str(ROOT / "page.html"), "outDir": str(BUILD), "stillsDir": str(ROOT / "stills"),
           "stills": [round(s, 2) for s in stills], "stillsOnly": test, "pageConfig": page_cfg, "segments": segments}
    (ROOT / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
    print(json.dumps({"segments": segments, "texts": texts, "card": page_cfg["card"]}, ensure_ascii=False))
    if test:
        run(["node", str(ROOT / "render.js"), str(ROOT / "config.json")]); return
    if BUILD.exists(): shutil.rmtree(BUILD)
    BUILD.mkdir()
    run(["node", str(ROOT / "render.js"), str(ROOT / "config.json")])
    # concat
    lst = BUILD / "list.txt"
    lst.write_text("".join(f"file '{BUILD / (s['name'] + '.mp4')}'\n" for s in segments))
    silent = BUILD / "video_silent.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    # audio: narration delayed, music ducked under narration, fade out at the end
    mdur = duration(music)
    fade_start = total - 1.6
    afilter = (
        f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={int(NARR_OFFSET*1000)}|{int(NARR_OFFSET*1000)},apad=whole_dur={total}[nar];"
        f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,volume=0.42,afade=t=in:st=0:d=1.2,afade=t=out:st={fade_start}:d=1.6[mus];"
        f"[nar]asplit=2[nar1][nar2];"
        f"[mus][nar2]sidechaincompress=threshold=0.015:ratio=6:attack=80:release=900:makeup=1[musd];"
        f"[nar1][musd]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-15:TP=-1.2:LRA=9[a]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(narr), "-i", str(music), "-filter_complex", afilter,
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(out_mp4)])
    print("done:", out_mp4, duration(out_mp4))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", nargs=5, required=True)
    ap.add_argument("--narr", required=True)
    ap.add_argument("--music", required=True)
    ap.add_argument("--out", default=str(ROOT / "gma-ogretmenler-gunu.mp4"))
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    main(a.images, a.narr, a.music, a.out, a.test)
