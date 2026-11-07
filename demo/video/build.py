"""Render the PaidSafe video: animated HTML scenes + real room footage + neural narration -> 1440p MP4.

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
LEAD, TAIL = 0.25, 0.45      # silence before / after each scene's narration
W, H, SCALE = 1920, 1080, 4 / 3  # CSS canvas 1920x1080 rendered at 2560x1440
FF = imageio_ffmpeg.get_ffmpeg_exe()

CSS = """
:root{--bg:#0b1020;--panel:#121a33;--ink:#e8ecf8;--mute:#93a0c4;--acc:#34d399;--warn:#fbbf24;--bad:#f87171;--blue:#60a5fa;--vio:#a78bfa}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI Variable Display","Segoe UI",system-ui,sans-serif}
.scene{position:absolute;inset:0;display:none;padding:100px 140px}
.bgglow{position:absolute;inset:0;background:radial-gradient(1200px 700px at 80% 10%,#1d2b5a66,transparent),
  radial-gradient(900px 600px at 10% 100%,#0f766e33,transparent)}
.a{opacity:0}
.kicker{font-size:30px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc);font-weight:600}
h1{font-size:120px;font-weight:800;letter-spacing:-.02em}
h2{font-size:62px;font-weight:750;letter-spacing:-.01em;line-height:1.12}
.sub{font-size:38px;color:var(--mute);margin-top:22px;line-height:1.35}
.logo{display:inline-flex;align-items:center;gap:26px}
.shield{width:120px;height:140px}
.panel{background:var(--panel);border:1px solid #23305c;border-radius:26px;padding:34px 38px}
.big{font-size:96px;font-weight:800;line-height:1}
.small{font-size:26px;color:var(--mute);margin-top:12px;line-height:1.35}
.src{font-size:19px;color:#6b7aa6;margin-top:14px}
.pill{display:inline-block;background:#1b2547;border:1px solid #2c3c72;border-radius:999px;padding:10px 22px;font-size:24px;margin-right:10px}
/* chat mock */
.chat{background:#0f1730;border:1px solid #26345f;border-radius:28px;padding:28px;box-shadow:0 40px 100px #0009}
.msg{display:flex;gap:16px;align-items:flex-start;margin:14px 0}
.av{width:56px;height:56px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:24px;flex:none}
.bub{background:#17213f;border:1px solid #26345f;border-radius:18px;padding:14px 20px;font-size:27px;line-height:1.35}
.bub b{display:block;font-size:20px;color:var(--mute);margin-bottom:4px;font-weight:600}
/* invoice */
.invoice{background:#f8fafc;color:#0f172a;border-radius:22px;padding:38px 44px;width:640px;position:relative;box-shadow:0 40px 100px #0009}
.invoice .row{display:flex;justify-content:space-between;font-size:26px;margin-top:10px;color:#334155}
.stamp{position:absolute;right:30px;top:40px;border:8px solid #dc2626;color:#dc2626;font-weight:900;font-size:64px;
  padding:4px 24px;border-radius:14px;opacity:0;letter-spacing:.06em}
.alert{position:absolute;border:4px solid var(--bad);border-radius:24px;background:#3b0d1688;color:#fecaca;font-size:30px;
  font-weight:700;padding:16px 26px}
/* pillars */
.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:40px;margin-top:70px}
.pillar{text-align:center;padding:46px 30px}
.pillar svg{width:190px;height:170px}
.pillar h3{font-size:46px;margin-top:18px}
.pillar p{font-size:27px;color:var(--mute);margin-top:12px;line-height:1.35}
/* room */
.room{position:relative;height:760px;margin-top:20px}
.node{position:absolute;width:300px;padding:26px 24px;border-radius:24px;background:var(--panel);border:2px solid #2c3c72;text-align:center}
.node b{display:block;font-size:34px}.node span{display:block;font-size:22px;color:var(--mute);margin-top:6px}
.node.h{border-color:#3b82f6}.node.c{border-color:#34d399}.node.l{border-color:#a78bfa}
.hub{position:absolute;left:620px;top:300px;width:400px;height:170px;border-radius:30px;background:linear-gradient(135deg,#0f766e,#1d4ed8);
  display:flex;align-items:center;justify-content:center;flex-direction:column;box-shadow:0 30px 80px #0008}
.hub b{font-size:40px}.hub span{font-size:24px;opacity:.85}
svg.lines{position:absolute;inset:0}
/* footage */
.shotwrap{position:absolute;left:110px;top:160px;width:1700px;height:850px;border-radius:22px;overflow:hidden;
  box-shadow:0 40px 120px #000a;border:1px solid #2c3c72;background:#fff}
.shotwrap img{position:absolute;left:0;width:1700px}
.shotlabel{position:absolute;left:110px;top:58px;font-size:40px;font-weight:700;display:flex;align-items:center;gap:20px}
.part{font-size:24px;letter-spacing:.14em;text-transform:uppercase;border-radius:999px;padding:8px 18px;border:2px solid}
.live{position:absolute;right:110px;top:66px;font-size:23px;color:var(--acc);border:1px solid #2f6f5a;padding:8px 18px;border-radius:999px;background:#0f2a24}
.live:before{content:"";display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--acc);margin-right:10px;vertical-align:1px}
/* hood / roadmap / end */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px 50px;margin-top:46px}
.chk{font-size:34px;display:flex;gap:18px;align-items:flex-start}
.chk i{font-style:normal;color:var(--acc);font-weight:800}
.chk small{display:block;color:var(--mute);font-size:24px;margin-top:4px}
.rm{display:grid;grid-template-columns:520px 120px 1fr;align-items:center;margin-top:110px}
.roomcard{background:var(--panel);border:2px solid #2c3c72;border-radius:22px;padding:24px 28px;font-size:28px}
.roomcard small{display:block;color:var(--mute);font-size:21px;margin-top:6px}
.rgrid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.endurl{font-size:40px;color:var(--blue);margin-top:36px}
"""

SHIELD_T = """<svg class="shield" viewBox="0 0 120 140"><defs><linearGradient id="GID" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#34d399"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
<path d="M60 4 L112 24 V66 C112 102 88 126 60 136 C32 126 8 102 8 66 V24 Z" fill="url(#GID)"/>
<path d="M36 72 L54 90 L86 54" stroke="#0b1020" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def shield(gid: str) -> str:
    return SHIELD_T.replace("GID", gid)


def msg(av, color, who, text, t):
    return (f'<div class="msg a" data-in="{t}"><div class="av" style="background:{color}">{av}</div>'
            f'<div class="bub"><b>{who}</b>{text}</div></div>')


def scene_html(sid: str, kind: str, extra: dict) -> str:
    if kind == "intro":
        chat = "".join([
            msg("O", "#ea580c", "Owner", "MegaMart is 32 days late. Chase or wait?", 1.2),
            msg("L", "#7c3aed", "Ledger · code", "F3: ₹7,130 statutory interest already owed", 2.4),
            msg("R", "#059669", "Relationship · AI", "Keep it friendly, they're 30% of revenue [F4]", 3.6),
            msg("C", "#2563eb", "Cash · AI", "Firm reminder: the law is on our side [F3]", 4.8),
            msg("W", "#0891b2", "Warden · code", "✅ Approved by the verified Owner and Accountant", 6.0)])
        return f"""<div class="bgglow"></div>
<div style="position:absolute;left:150px;top:250px;width:820px">
 <div class="logo a" data-in="0.1">{shield("g1")}<h1>PaidSafe</h1></div>
 <div class="sub a" data-in="0.6" style="font-size:50px;color:var(--ink)">Decide with proof.<br>Approve with certainty.</div>
 <div class="sub a" data-in="1.1">A team chat where a small business's people and AI agents make money decisions together.</div>
 <div class="a" data-in="1.6" style="margin-top:34px"><span class="pill">Built on Switch</span><span class="pill">Mattermost</span></div>
</div><div class="float" data-amp="8" style="position:absolute;right:120px;top:170px;width:820px"><div class="chat">{chat}</div></div>"""
    if kind == "pain_in":
        return """<div class="bgglow"></div><div class="kicker a" data-in="0">The problem · money in</div>
<h2 class="a" data-in="0.2" style="margin-top:12px">Big customers pay late. Small suppliers are stuck.</h2>
<div style="display:grid;grid-template-columns:700px 1fr;gap:70px;margin-top:56px;align-items:start">
 <div class="a" data-in="0.5"><div class="invoice"><div style="font-size:24px;letter-spacing:.2em;color:#64748b">INVOICE</div>
  <div style="font-size:52px;font-weight:800;margin-top:6px">₹4,80,000</div>
  <div class="row"><span>Customer</span><b>MegaMart Retail</b></div><div class="row"><span>Invoice</span><b>INV-1042</b></div>
  <div class="row"><span>Days overdue</span><b style="color:#dc2626;font-size:40px"><span data-count="32" data-start="1.0">0</span></b></div>
  <div class="stamp" data-in="2.6">LATE</div></div></div>
 <div>
  <div class="panel a" data-in="3.6" style="display:flex;gap:26px;align-items:center"><div style="font-size:60px">😬</div>
   <div><b style="font-size:32px">Push too hard</b><div class="small" style="margin-top:4px">and lose the customer</div></div></div>
  <div class="panel a" data-in="5.0" style="display:flex;gap:26px;align-items:center;margin-top:22px"><div style="font-size:60px">💸</div>
   <div><b style="font-size:32px">Wait too long</b><div class="small" style="margin-top:4px">and miss payroll</div></div></div>
  <div class="panel a" data-in="7.2" style="margin-top:22px;border-color:#7c5e10"><div class="big" style="color:var(--warn)"><span data-count="82.8" data-dec="1" data-start="7.2">0</span></div>
   <div class="small">Itch score: "Why can't SMEs negotiate favorable payment terms with large buyers?"</div>
   <div class="src">Razorpay Fix My Itch · also: 59% of US small businesses wait 30+ days (Intuit QuickBooks 2026)</div></div>
 </div></div>"""
    if kind == "pain_out":
        chat = (msg("A", "#db2777", "Accountant", "Approved ✅ Pay ₹4,80,000 to the new account now. Urgent!", 0.8))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0" style="color:var(--bad)">The problem · money out</div>
<h2 class="a" data-in="0.2" style="margin-top:12px">Fraud has moved into team chat.</h2>
<div style="display:grid;grid-template-columns:900px 1fr;gap:70px;margin-top:60px;align-items:start">
 <div style="position:relative"><div class="chat shake" data-in="2.6">{chat}
   {msg("O", "#ea580c", "Owner", "Okay, paying now…", 1.8)}</div>
  <div class="alert a" data-in="2.6" style="left:120px;top:250px">⚠ That wasn't the real accountant.</div></div>
 <div class="panel a" data-in="3.6"><div class="big" style="color:var(--bad)">$<span data-count="3.05" data-dec="2" data-start="3.6">0</span>B</div>
  <div class="small">lost to business email compromise in 2025. A wire request was even deepfaked over Slack.</div>
  <div class="src">FBI IC3 2025 report · AFP 2026</div></div></div>"""
    if kind == "pillars":
        scale = """<svg viewBox="0 0 190 170"><g class="tilt" data-ox="95" data-oy="40"><line x1="25" y1="40" x2="165" y2="40" stroke="#60a5fa" stroke-width="8" stroke-linecap="round"/>
<path d="M25 40 L5 95 H45 Z" fill="none" stroke="#60a5fa" stroke-width="6"/><path d="M165 40 L145 95 H185 Z" fill="none" stroke="#60a5fa" stroke-width="6"/></g>
<line x1="95" y1="20" x2="95" y2="150" stroke="#60a5fa" stroke-width="8"/><rect x="55" y="150" width="80" height="12" rx="6" fill="#60a5fa"/></svg>"""
        shieldsvg = """<svg viewBox="0 0 190 170"><g class="pulse" data-ox="95" data-oy="85"><path d="M95 10 L160 35 V85 C160 125 130 150 95 162 C60 150 30 125 30 85 V35 Z" fill="#f8717133" stroke="#f87171" stroke-width="6"/>
<path d="M65 88 L88 110 L128 66" stroke="#f87171" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g></svg>"""
        chart = """<svg viewBox="0 0 190 170"><line x1="20" y1="150" x2="175" y2="150" stroke="#475569" stroke-width="4"/>
<path class="draw" data-in="6.4" pathLength="1" d="M22 140 L60 115 L95 120 L130 70 L170 30" fill="none" stroke="#a78bfa" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="170" cy="30" r="10" fill="#a78bfa" class="a" data-in="7.2"/></svg>"""
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">What PaidSafe does</div>
<h2 class="a" data-in="0.2" style="margin-top:12px">One room. Three jobs.</h2>
<div class="pillars">
 <div class="panel pillar a" data-in="1.8">{scale}<h3 style="color:var(--blue)">Decide</h3><p>AI agents argue chase or wait, using only proven facts</p></div>
 <div class="panel pillar a" data-in="3.9">{shieldsvg}<h3 style="color:var(--bad)">Protect</h3><p>Only the real owner and accountant can approve</p></div>
 <div class="panel pillar a" data-in="6.0">{chart}<h3 style="color:var(--vio)">Learn</h3><p>Every outcome makes the next decision smarter</p></div>
</div>"""
    if kind == "room":
        nodes = [("h", 0, 60, "Owner", "verified human"), ("h", 0, 560, "Accountant", "verified human"),
                 ("l", 1340, 60, "Ledger", "code · no LLM"), ("l", 1340, 560, "Warden", "code · no LLM"),
                 ("c", 670, 0, "Relationship", "Claude Opus 5.5"), ("c", 670, 620, "Cash", "Claude Sonnet 5.5")]
        nh = "".join(f'<div class="node {c} a" data-in="{0.6 + i * 0.6}" style="left:{x}px;top:{y}px">'
                     f'<b>{n}</b><span>{d}</span></div>' for i, (c, x, y, n, d) in enumerate(nodes))
        lines = "".join(f'<line x1="{x + 150}" y1="{y + 60}" x2="820" y2="385" stroke="#3b5bdb" stroke-width="3" '
                        f'pathLength="1" class="draw" data-in="{0.6 + i * 0.6}"/>' for i, (_, x, y, *_r) in enumerate(nodes))
        dots = "".join(f'<circle r="7" fill="#34d399" class="dot" data-x1="{x + 150}" data-y1="{y + 60}" data-x2="820" '
                       f'data-y2="385" data-ph="{i * 0.17}" data-in="4.5"/>' for i, (_, x, y, *_r) in enumerate(nodes))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">One Switch room · two people · four agents</div>
<div class="room"><svg class="lines" width="1640" height="760">{lines}{dots}</svg>
<div class="hub a" data-in="0.2"><b>Switch room</b><span>#client-megamart</span></div>{nh}</div>"""
    if kind in ("shot", "shot2"):
        part, color = extra["part"]
        imgs = (f'<img src="footage/{extra["img"]}" data-pan="0.40,0.52" class="swap1">' +
                (f'<img src="footage/{extra["img2"]}" data-pan="0.40,0.52" class="swap2" style="opacity:0">'
                 if kind == "shot2" else ""))
        return f"""<div class="shotlabel a" data-in="0"><span class="part" style="color:{color};border-color:{color}">{part}</span>{extra['label']}</div>
<div class="live a" data-in="0.2">LIVE · real Switch room</div><div class="shotwrap a" data-in="0.1">{imgs}</div>"""
    if kind == "hood":
        items = [("Switch agent protocol", "Ledger + Warden connect over WebSocket"),
                 ("Verified sender identity", "approvals bound to Switch sender ids"),
                 ("Who-can-talk rules", "debaters answer only the owner and owner's agents"),
                 ("Room documents", "the Warden-owned playbook is the room's memory"),
                 ("One-click template", "agents + room + docs, validated by Switch"),
                 ("Guardrails in code", "evidence-checked drafts · freeze in every tool"),
                 ("Scoped agents", "no shell, files or web · injection-resistant"),
                 ("59 automated tests", "interest, fact-check, impostor, two-key, memory")]
        rows = "".join(f'<div class="chk a" data-in="{0.4 + i * 0.6}"><i>✓</i><div>{a}<small>{b}</small></div></div>'
                       for i, (a, b) in enumerate(items))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">Under the hood</div>
<h2 class="a" data-in="0.15" style="margin-top:12px">Switch is the backbone, not a plug-in.</h2><div class="grid">{rows}</div>"""
    if kind == "roadmap":
        nxt = [("#client-blueleaf", "a room per client"), ("#client-northbridge", "UK rules pack ready"),
               ("#supplier-shree-polymers", "payment-fraud checks"), ("#paidsafe-desk", "hub for every room"),
               ("+ more agents", "collections, supplier checker"), ("+ phone approvals", "Telegram bridge")]
        cards = "".join(f'<div class="roomcard a" data-in="{4.5 + i * 0.7}">{a}<small>{b}</small></div>' for i, (a, b) in enumerate(nxt))
        return f"""<div class="bgglow"></div><div class="kicker a" data-in="0">Today → next</div>
<h2 class="a" data-in="0.2" style="margin-top:12px">Small today. Built to scale.</h2>
<div class="rm"><div class="a" data-in="1.0" style="position:relative"><div class="small" style="position:absolute;top:-48px;left:0">TODAY</div>
 <div class="roomcard" style="border-color:var(--acc)">#client-megamart<small>1 mock client · 4 basic agents · 2 people</small></div></div>
 <svg width="120" height="60"><path class="draw" data-in="3.4" pathLength="1" d="M10 30 H100 M80 12 L100 30 L80 48" stroke="#34d399" stroke-width="6" fill="none" stroke-linecap="round"/></svg>
 <div style="position:relative"><div class="small a" data-in="4.2" style="position:absolute;top:-48px;left:0">NEXT, FROM THE SAME TEMPLATE</div><div class="rgrid">{cards}</div></div></div>"""
    if kind == "end":
        return f"""<div class="bgglow"></div>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
 <div class="a pulse" data-in="0.1" data-ox="0" data-oy="0">{shield("g2")}</div><h1 class="a" data-in="0.3" style="margin-top:20px">PaidSafe</h1>
 <div class="sub a" data-in="0.8" style="color:var(--ink)">Decide with proof. Approve with certainty. Learn from every outcome.</div>
 <div class="endurl a" data-in="1.4">github.com/Chiru595/paidsafe</div>
 <div class="sub a" data-in="1.8" style="font-size:24px">Built on Switch · synthetic data · simulated sends · not legal or financial advice</div></div>"""
    raise ValueError(kind)


JS = """
const ease=t=>1-Math.pow(1-Math.min(Math.max(t,0),1),3);
const back=t=>{t=Math.min(Math.max(t,0),1);const c=1.7;return 1+(c+1)*Math.pow(t-1,3)+c*Math.pow(t-1,2);};
function render(t){
  let acc=0, cur=null, lt=0;
  for(const s of window.PLAN){ if(t<acc+s.d||s===window.PLAN[window.PLAN.length-1]){cur=s;lt=t-acc;break;} acc+=s.d; }
  document.querySelectorAll('.scene').forEach(e=>e.style.display=(e.id===cur.id?'block':'none'));
  const root=document.getElementById(cur.id);
  root.style.opacity=Math.min(ease(lt/0.35), ease((cur.d-lt)/0.35));
  root.querySelectorAll('.a').forEach(e=>{const p=ease((lt-parseFloat(e.dataset.in||0))/0.6);
    e.style.opacity=p; if(!e.classList.contains('pulse')) e.style.transform=`translateY(${(1-p)*26}px)`;});
  root.querySelectorAll('[data-count]').forEach(e=>{const st=parseFloat(e.dataset.start||0);
    const p=ease((lt-st)/1.6); e.textContent=(parseFloat(e.dataset.count)*p).toFixed(parseInt(e.dataset.dec||0));});
  root.querySelectorAll('.draw').forEach(e=>{const p=ease((lt-parseFloat(e.dataset.in))/0.9);
    e.style.strokeDasharray=1; e.style.strokeDashoffset=1-p;});
  root.querySelectorAll('.dot').forEach(e=>{const st=parseFloat(e.dataset.in); const on=lt>st;
    const f=((lt*0.45)+parseFloat(e.dataset.ph))%1; const d=e.dataset;
    e.setAttribute('cx', +d.x1+(d.x2-d.x1)*f); e.setAttribute('cy', +d.y1+(d.y2-d.y1)*f);
    e.style.opacity=on?Math.sin(f*Math.PI):0;});
  root.querySelectorAll('.float').forEach(e=>{e.style.transform=`translateY(${Math.sin(lt*0.9)*(+e.dataset.amp)}px)`;});
  root.querySelectorAll('.tilt').forEach(e=>{const a=Math.sin(lt*1.4)*9;
    e.setAttribute('transform',`rotate(${a} ${e.dataset.ox} ${e.dataset.oy})`);});
  root.querySelectorAll('.pulse').forEach(e=>{const s=1+0.045*Math.sin(lt*3.2);
    if(e.tagName==='g') e.setAttribute('transform',`translate(${e.dataset.ox} ${e.dataset.oy}) scale(${s}) translate(${-e.dataset.ox} ${-e.dataset.oy})`);
    else e.style.transform=`scale(${s})`;});
  root.querySelectorAll('.stamp').forEach(e=>{const p=(lt-parseFloat(e.dataset.in))/0.45;
    e.style.opacity=p>0?1:0; const s=2.4-1.4*back(p); e.style.transform=`rotate(-14deg) scale(${p>0?s:2.4})`;});
  root.querySelectorAll('.shake').forEach(e=>{const p=(lt-parseFloat(e.dataset.in))/0.7;
    const x=(p>0&&p<1)?Math.sin(lt*70)*10*(1-p):0; e.style.transform=`translateX(${x}px)`;
    e.style.borderColor=p>0?'#f87171':'#26345f';});
  root.querySelectorAll('img[data-pan]').forEach(img=>{const [a,b]=img.dataset.pan.split(',').map(Number);
    const ih=img.naturalHeight*1700/img.naturalWidth, travel=Math.max(0,ih-850);
    const p=ease(lt/cur.d), f=a+(b-a)*p; img.style.top=(-travel*f)+'px';
    img.style.transform=`scale(${1+0.035*p})`; img.style.transformOrigin='50% '+(f*100)+'%';});
  const s1=root.querySelector('.swap1'), s2=root.querySelector('.swap2');
  if(s1&&s2){const p=ease((lt-cur.d*0.5)/0.6); s2.style.opacity=p; s1.style.opacity=1-p;}
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
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
        page.goto((page_dir / "index.html").as_uri())
        page.wait_for_function("Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)")
        page.wait_for_timeout(500)

        if STILLS:
            acc = 0.0
            (WORK / "stills").mkdir(exist_ok=True)
            for i, s in enumerate(plan):
                page.evaluate(f"render({acc + s['d'] * 0.75})")
                page.screenshot(path=str(WORK / "stills" / f"{i:02d}.jpg"), type="jpeg", quality=80)
                acc += s["d"]
            print("stills written")
            return

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
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(audio)],
                       check=True, capture_output=True)

        out = WORK / "paidsafe.mp4"
        enc = subprocess.Popen([FF, "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", "-i", str(audio),
                                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)],
                               stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        n = int(total * FPS)
        for f in range(n):
            page.evaluate(f"render({f / FPS})")
            enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            if f % 600 == 0:
                print(f"frame {f}/{n}", flush=True)
        enc.stdin.close()
        enc.wait()
        browser.close()
        print("wrote", out)


if __name__ == "__main__":
    main()
