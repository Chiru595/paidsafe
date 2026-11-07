"""Render the PaidSafe video: animated HTML scenes + real room footage + neural narration -> MP4.

Deterministic frame-by-frame capture in headless Chrome (no dropped frames), encoded with ffmpeg.

    python demo/video/tts.py   <work>             # narration clips + durations
    python demo/video/build.py <work> <footage>   # -> <work>/paidsafe.mp4
    python demo/video/build.py <work> <footage> --stills   # one still per scene, for review
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script import SCENES  # noqa: E402

WORK = Path(sys.argv[1])
FOOTAGE = Path(sys.argv[2])
STILLS = "--stills" in sys.argv
FPS = 30
LEAD, TAIL = 0.35, 0.55  # silence before / after each scene's narration
W, H = 1920, 1080
FF = imageio_ffmpeg.get_ffmpeg_exe()

CSS = """
:root{--bg:#0b1020;--panel:#121a33;--ink:#e8ecf8;--mute:#93a0c4;--acc:#34d399;--warn:#fbbf24;--bad:#f87171;--blue:#60a5fa}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI Variable Display","Segoe UI",system-ui,sans-serif}
.scene{position:absolute;inset:0;display:none;padding:110px 140px}
.bgglow{position:absolute;inset:0;background:radial-gradient(1200px 700px at 80% 10%,#1d2b5a55,transparent),
  radial-gradient(900px 600px at 10% 100%,#0f766e33,transparent)}
.a{opacity:0;transform:translateY(24px)}
.kicker{font-size:30px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc);font-weight:600}
h1{font-size:120px;font-weight:800;letter-spacing:-.02em}
h2{font-size:64px;font-weight:750;letter-spacing:-.01em;line-height:1.1}
.sub{font-size:40px;color:var(--mute);margin-top:22px;line-height:1.35;max-width:1500px}
.logo{display:inline-flex;align-items:center;gap:26px}
.shield{width:120px;height:140px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:34px;margin-top:60px}
.card{background:var(--panel);border:1px solid #23305c;border-radius:26px;padding:40px 40px 34px}
.big{font-size:104px;font-weight:800;line-height:1}
.card p{font-size:28px;color:var(--mute);margin-top:16px;line-height:1.35}
.src{font-size:20px;color:#6b7aa6;margin-top:18px}
.pill{display:inline-block;background:#1b2547;border:1px solid #2c3c72;color:var(--ink);border-radius:999px;
  padding:10px 22px;font-size:24px;margin:6px 8px 0 0}
.room{position:relative;height:760px;margin-top:20px}
.node{position:absolute;width:300px;padding:26px 24px;border-radius:24px;background:var(--panel);
  border:2px solid #2c3c72;text-align:center}
.node b{display:block;font-size:34px}.node span{display:block;font-size:22px;color:var(--mute);margin-top:6px}
.node.h{border-color:#3b82f6}.node.c{border-color:#34d399}.node.l{border-color:#a78bfa}
.hub{position:absolute;left:620px;top:300px;width:400px;height:170px;border-radius:30px;
  background:linear-gradient(135deg,#0f766e,#1d4ed8);display:flex;align-items:center;justify-content:center;
  flex-direction:column;box-shadow:0 30px 80px #0008}
.hub b{font-size:40px}.hub span{font-size:24px;opacity:.85}
svg.lines{position:absolute;inset:0}
.shotwrap{position:absolute;left:110px;top:150px;width:1700px;height:860px;border-radius:22px;overflow:hidden;
  box-shadow:0 40px 120px #000a;border:1px solid #2c3c72;background:#fff}
.shotwrap img{position:absolute;left:0;width:1700px}
.shotlabel{position:absolute;left:110px;top:62px;font-size:40px;font-weight:700}
.live{position:absolute;right:110px;top:66px;font-size:24px;color:var(--acc);border:1px solid #2f6f5a;
  padding:8px 18px;border-radius:999px;background:#0f2a24}
.live:before{content:"";display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--acc);
  margin-right:10px;vertical-align:1px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px 50px;margin-top:50px}
.chk{font-size:34px;display:flex;gap:18px;align-items:flex-start}
.chk i{font-style:normal;color:var(--acc);font-weight:800}
.chk small{display:block;color:var(--mute);font-size:24px;margin-top:4px}
.endurl{font-size:40px;color:var(--blue);margin-top:40px}
.foot{position:absolute;left:140px;bottom:56px;font-size:22px;color:#6b7aa6}
"""

SHIELD = """<svg class="shield" viewBox="0 0 120 140"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#34d399"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
<path d="M60 4 L112 24 V66 C112 102 88 126 60 136 C32 126 8 102 8 66 V24 Z" fill="url(#g)"/>
<path d="M36 72 L54 90 L86 54" stroke="#0b1020" stroke-width="12" fill="none" stroke-linecap="round"
 stroke-linejoin="round"/></svg>"""


def scene_html(sid: str, kind: str, extra: dict) -> str:
    if kind == "title":
        return f"""<div class="bgglow"></div>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 160px">
 <div class="logo a" data-in="0.1">{SHIELD}<h1>PaidSafe</h1></div>
 <div class="sub a" data-in="0.7" style="font-size:52px;color:var(--ink)">Get paid on time, without losing the client.</div>
 <div class="sub a" data-in="1.3">People and AI agents decide together in a <b style="color:var(--acc)">Switch</b> room.
 Every number proven. Every rupee approved by a verified human.</div>
 <div class="a" data-in="2.0" style="margin-top:40px"><span class="pill">Flip the Switch · Track 01 Business Workflow</span>
 <span class="pill">Mattermost × Switch</span></div></div>"""
    if kind == "problem":
        return """<div class="bgglow"></div><div class="kicker a" data-in="0">A real, ranked problem</div>
<h2 class="a" data-in="0.2" style="margin-top:14px">Small suppliers wait. Fraud moves into chat.</h2>
<div class="cards">
 <div class="card a" data-in="0.6"><div class="big" style="color:var(--warn)"><span data-count="82.8" data-dec="1">0</span></div>
  <p>Itch score: <i>"Why can't SMEs negotiate favorable payment terms with large buyers?"</i></p>
  <div class="src">Razorpay Fix My Itch · B2B</div></div>
 <div class="card a" data-in="5.0"><div class="big" style="color:var(--blue)"><span data-count="59">0</span>%</div>
  <p>of US small businesses have invoices overdue 30+ days, owed $17.7K on average</p>
  <div class="src">Intuit QuickBooks, 2026</div></div>
 <div class="card a" data-in="9.5"><div class="big" style="color:var(--bad)">$<span data-count="3.05" data-dec="2">0</span>B</div>
  <p>lost to business email compromise in 2025. A wire request was even deepfaked via Slack</p>
  <div class="src">FBI IC3 2025 · AFP 2026</div></div>
</div>
<div class="sub a" data-in="11" style="font-size:30px;margin-top:40px">India's MSMED Act already grants late-payment
 interest at 3× the RBI Bank Rate. Most suppliers never claim it, for fear of losing the client.</div>"""
    if kind == "room":
        nodes = [
            ("h", 0, 60, "Owner", "verified human"), ("h", 0, 560, "Accountant", "verified human"),
            ("l", 1340, 60, "Ledger", "code · no LLM"), ("l", 1340, 560, "Warden", "code · no LLM"),
            ("c", 670, 0, "Relationship", "Claude Opus 5.5"), ("c", 670, 620, "Cash", "Claude Sonnet 5.5"),
        ]
        nh = "".join(f'<div class="node {c} a" data-in="{0.6 + i * 0.5}" style="left:{x}px;top:{y}px">'
                     f'<b>{n}</b><span>{d}</span></div>' for i, (c, x, y, n, d) in enumerate(nodes))
        lines = "".join(f'<line x1="{x + 150}" y1="{y + 60}" x2="820" y2="385" stroke="#2c3c72" stroke-width="3" '
                        f'stroke-dasharray="900" class="draw" data-in="{0.6 + i * 0.5}"/>'
                        for i, (_, x, y, *_r) in enumerate(nodes))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">One room · two people · four agents</div>
<div class="room"><svg class="lines" width="1640" height="760">{lines}</svg>
<div class="hub a" data-in="0.2"><b>Switch room</b><span>#client-megamart</span></div>{nh}</div>"""
    if kind == "shot":
        return f"""<div class="shotlabel a" data-in="0">{extra['label']}</div><div class="live a" data-in="0.2">LIVE · real Switch room</div>
<div class="shotwrap a" data-in="0.1"><img src="footage/{extra['img']}" data-pan="{extra['from']},{extra['to']}"></div>"""
    if kind == "shot2":
        return f"""<div class="shotlabel a" data-in="0">{extra['label']}</div><div class="live a" data-in="0.2">LIVE · real Switch room</div>
<div class="shotwrap a" data-in="0.1"><img src="footage/{extra['img']}" data-pan="0.42,0.5" class="swap1">
<img src="footage/{extra['img2']}" data-pan="0.42,0.5" class="swap2" style="opacity:0"></div>"""
    if kind == "hood":
        items = [("Switch agent protocol", "Ledger + Warden: WebSocket in, HTTP out"),
                 ("Verified sender identity", "approvals bound to Switch sender ids"),
                 ("Addressing rules", "debaters answer only the owner and owner's agents"),
                 ("Room documents", "Warden-owned playbook = shared memory"),
                 ("Validated template", "debaters + room + docs in one import"),
                 ("Guardrails in code", "evidence-checked drafts · freeze in every tool"),
                 ("Scoped agents", "no shell, files or web · injection-resistant prompts"),
                 ("53 tests passing", "interest, fact-check, impostor, two-key, evidence")]
        rows = "".join(f'<div class="chk a" data-in="{0.4 + i * 0.75}"><i>✓</i><div>{a}<small>{b}</small></div></div>'
                       for i, (a, b) in enumerate(items))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">Under the hood</div>
<h2 class="a" data-in="0.15" style="margin-top:14px">Switch is the backbone, not a plug-in.</h2><div class="grid">{rows}</div>"""
    if kind == "end":
        return f"""<div class="bgglow"></div>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
 <div class="a" data-in="0.1">{SHIELD}</div><h1 class="a" data-in="0.3" style="margin-top:20px">PaidSafe</h1>
 <div class="sub a" data-in="0.8" style="color:var(--ink)">Every rupee, approved by a verified human.</div>
 <div class="endurl a" data-in="1.4">github.com/Chiru595/paidsafe</div>
 <div class="sub a" data-in="1.8" style="font-size:24px">Synthetic data · simulated sends · not legal or financial advice</div></div>"""
    raise ValueError(kind)


JS = """
const ease=t=>1-Math.pow(1-Math.min(Math.max(t,0),1),3);
function render(t){
  let acc=0, cur=null, lt=0;
  for(const s of window.PLAN){ if(t<acc+s.d||s===window.PLAN[window.PLAN.length-1]){cur=s;lt=t-acc;break;} acc+=s.d; }
  document.querySelectorAll('.scene').forEach(e=>e.style.display=(e.id===cur.id?'block':'none'));
  const root=document.getElementById(cur.id);
  // scene cross-fade in/out
  const fin=ease(lt/0.35), fout=ease((cur.d-lt)/0.35); root.style.opacity=Math.min(fin,fout);
  root.querySelectorAll('.a').forEach(e=>{const p=ease((lt-parseFloat(e.dataset.in||0))/0.6);
    e.style.opacity=p; e.style.transform=`translateY(${(1-p)*24}px)`;});
  root.querySelectorAll('[data-count]').forEach(e=>{const host=e.closest('.a');const st=parseFloat(host.dataset.in||0);
    const p=ease((lt-st)/1.6), v=parseFloat(e.dataset.count)*p; e.textContent=v.toFixed(parseInt(e.dataset.dec||0));});
  root.querySelectorAll('.draw').forEach(e=>{const p=ease((lt-parseFloat(e.dataset.in))/0.9);
    e.style.strokeDashoffset=900*(1-p); e.style.stroke=p>0.99?'#3b5bdb':'#2c3c72';});
  root.querySelectorAll('img[data-pan]').forEach(img=>{const [a,b]=img.dataset.pan.split(',').map(Number);
    const wrapH=860, ih=img.naturalHeight*1700/img.naturalWidth, travel=Math.max(0,ih-wrapH);
    const p=ease(lt/cur.d); const f=a+(b-a)*p; img.style.top=(-travel*f)+'px';
    const z=1+0.035*p; img.style.transform=`scale(${z})`; img.style.transformOrigin='50% '+(f*100)+'%';});
  const s1=root.querySelector('.swap1'), s2=root.querySelector('.swap2');
  if(s1&&s2){const p=ease((lt-cur.d*0.55)/0.5); s2.style.opacity=p; s1.style.opacity=1-p;}
}
"""


def main() -> None:
    durs = json.loads((WORK / "durations.json").read_text())
    plan = [{"id": sid, "d": round(LEAD + durs[sid] + TAIL, 3)} for sid, *_ in SCENES]
    plan[-1]["d"] += 1.5  # hold the end card
    total = sum(p["d"] for p in plan)
    print(f"video length {total:.1f}s")

    page_dir = WORK / "page"
    if page_dir.exists():
        shutil.rmtree(page_dir)
    page_dir.mkdir(parents=True)
    shutil.copytree(FOOTAGE, page_dir / "footage")
    scenes = "".join(f'<div class="scene" id="{sid}">{scene_html(sid, kind, extra)}</div>' for sid, kind, _, extra in SCENES)
    (page_dir / "index.html").write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{scenes}"
        f"<script>window.PLAN={json.dumps(plan)};{JS}</script></body></html>", encoding="utf-8")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto((page_dir / "index.html").as_uri())
        page.wait_for_function("Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)")
        page.wait_for_timeout(500)

        if STILLS:
            acc = 0.0
            (WORK / "stills").mkdir(exist_ok=True)
            for i, s in enumerate(plan):
                page.evaluate(f"render({acc + s['d'] * 0.7})")
                page.screenshot(path=str(WORK / "stills" / f"{i:02d}.jpg"), type="jpeg", quality=80)
                acc += s["d"]
            print("stills written")
            return

        # audio: each clip placed at its scene start + LEAD
        inputs, filters, t = [], [], 0.0
        for i, s in enumerate(plan):
            inputs += ["-i", str(WORK / "audio" / f"{s['id']}.mp3")]
            ms = int((t + LEAD) * 1000)
            filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
            t += s["d"]
        mix = "".join(f"[a{i}]" for i in range(len(plan)))
        filters.append(f"{mix}amix=inputs={len(plan)}:normalize=0,apad=whole_dur={total:.2f},"
                       f"afade=t=out:st={total - 1.2:.2f}:d=1.2[aout]")
        audio = WORK / "narration.m4a"
        subprocess.run([FF, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[aout]",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(audio)], check=True, capture_output=True)

        out = WORK / "paidsafe.mp4"
        enc = subprocess.Popen([FF, "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", "-i", str(audio),
                                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)],
                               stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        n = int(total * FPS)
        for f in range(n):
            page.evaluate(f"render({f / FPS})")
            enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            if f % 300 == 0:
                print(f"frame {f}/{n}", flush=True)
        enc.stdin.close()
        enc.wait()
        browser.close()
        print("wrote", out)


if __name__ == "__main__":
    main()
