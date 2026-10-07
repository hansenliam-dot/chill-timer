"""Focus Timer: a tiny web app with no dependencies.
Run locally:  python app.py   then open http://localhost:8000
On Render:    Web Service, Start Command "python app.py"
"""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Focus Timer</title>
<style>
:root{--bg:#eef2f0;--card:#fff;--ink:#1d2b27;--mute:#6b7c76;--accent:#2f7d6d;--track:#dbe5e1;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121917;--card:#1b2623;--ink:#e8f0ed;--mute:#8fa39c;--accent:#5cc2ad;--track:#2b3a36}}
:root[data-theme="dark"]{--bg:#121917;--card:#1b2623;--ink:#e8f0ed;--mute:#8fa39c;--accent:#5cc2ad;--track:#2b3a36}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font-family:"Trebuchet MS",system-ui,sans-serif;display:flex;align-items:center;justify-content:center}
.app{background:var(--card);border-radius:28px;padding:28px;width:min(360px,92vw);text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.12)}
.modes{display:flex;gap:6px;background:var(--track);border-radius:999px;padding:4px;margin-bottom:24px}
.modes button{flex:1;border:0;background:none;color:var(--mute);padding:8px 4px;border-radius:999px;font:inherit;font-size:13px;cursor:pointer}
.modes button.on{background:var(--card);color:var(--ink);font-weight:bold}
.ring{position:relative;width:240px;height:240px;margin:0 auto 24px}
svg{width:100%;height:100%;transform:rotate(-90deg)}
circle{fill:none;stroke-width:10}
.bg{stroke:var(--track)}
.fg{stroke:var(--accent);stroke-linecap:round;transition:stroke-dashoffset .4s linear}
.time{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:56px;font-weight:bold;font-variant-numeric:tabular-nums}
.ctrl{display:flex;gap:10px}
.ctrl button{flex:1;border:0;border-radius:16px;padding:14px;font:inherit;font-size:16px;cursor:pointer}
#go{background:var(--accent);color:#fff;font-weight:bold}
#reset{background:var(--track);color:var(--ink)}
button:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.chill{display:none;align-items:center;justify-content:center;gap:16px;margin-bottom:16px;color:var(--mute);font-size:14px}
.chill button{width:36px;height:36px;border:0;border-radius:50%;background:var(--track);color:var(--ink);font-size:20px;cursor:pointer}
:root.chill-on{--bg:#1e1b2e;--card:#29253d;--ink:#ece9f7;--mute:#a49fc2;--accent:#b39ddb;--track:#3a3555}
:root.chill-on .chill{display:flex}
.msg{min-height:20px;margin:-6px 0 10px;font-size:14px;color:var(--accent)}
.count{margin-top:18px;color:var(--mute);font-size:14px}
</style>
</head>
<body>
<main class="app">
  <div class="modes" id="modes">
    <button data-m="25" class="on">Focus</button>
    <button data-m="5">Short break</button>
    <button data-m="15">Long break</button>
    <button data-m="10" data-chill="1">Chill</button>
  </div>
  <div class="ring">
    <svg viewBox="0 0 100 100"><circle class="bg" cx="50" cy="50" r="45"/><circle class="fg" id="fg" cx="50" cy="50" r="45"/></svg>
    <div class="time" id="time">25:00</div>
  </div>
  <div class="chill" id="chill"><button id="minus" aria-label="Less time">−</button><span id="mins">10 min</span><button id="plus" aria-label="More time">+</button></div>
  <div class="msg" id="msg" role="status"></div>
  <div class="ctrl"><button id="go">Start</button><button id="reset">Reset</button></div>
  <div class="count" id="count">Sessions finished: 0</div>
</main>
<script>
const C=2*Math.PI*45, fg=document.getElementById('fg'), timeEl=document.getElementById('time'),
go=document.getElementById('go'), count=document.getElementById('count');
fg.style.strokeDasharray=C;
let total=25*60, left=total, timer=null, done=0;
function draw(){
  const m=String(Math.floor(left/60)).padStart(2,'0'), s=String(left%60).padStart(2,'0');
  timeEl.textContent=m+':'+s; document.title=m+':'+s+' · Focus Timer';
  fg.style.strokeDashoffset=C*(1-left/total);
}
function stop(){clearInterval(timer);timer=null;go.textContent='Start'}
let chillOn=false;
function beep(){try{const a=new (window.AudioContext||window.webkitAudioContext)(),o=a.createOscillator(),g=a.createGain();
  o.connect(g);g.connect(a.destination);o.type=chillOn?'sine':'square';o.frequency.value=chillOn?330:660;
  g.gain.setValueAtTime(chillOn?.15:.1,a.currentTime);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+(chillOn?1.8:.4));
  o.start();o.stop(a.currentTime+(chillOn?1.8:.4))}catch(e){}}
function setChill(m){stop();total=left=m*60;document.getElementById('mins').textContent=m+' min';draw()}
// error.mid: [start s, length s, Hz]
const ERR=[[.5,1.25,43.65],[.75,1.25,77.78],[.75,1.25,130.81],[1.5,1.25,51.91]];
let errCtx=null,msgT=null;
function errorSound(){try{errCtx=errCtx||new (window.AudioContext||window.webkitAudioContext)();const a=errCtx,t0=a.currentTime;
  const f=a.createBiquadFilter();f.type='lowpass';f.frequency.value=900;f.connect(a.destination);
  ERR.forEach(([st,du,hz])=>{const o=a.createOscillator(),g=a.createGain();o.type='sawtooth';o.frequency.value=hz;
    g.gain.setValueAtTime(0,t0+st);g.gain.linearRampToValueAtTime(.12,t0+st+.03);g.gain.exponentialRampToValueAtTime(.001,t0+st+du);
    o.connect(g);g.connect(f);o.start(t0+st);o.stop(t0+st+du+.05)})}catch(e){}}
function showMsg(t){const m=document.getElementById('msg');m.textContent=t;clearTimeout(msgT);msgT=setTimeout(()=>m.textContent='',2800)}
document.getElementById('minus').onclick=()=>{
  if(total/60<=2){errorSound();showMsg("You can't make it shorter");return}
  setChill(total/60-1)};
document.getElementById('plus').onclick=()=>{const m=Math.min(120,total/60+1);setChill(m)};
go.onclick=()=>{
  if(timer){stop();return}
  go.textContent='Pause';
  timer=setInterval(()=>{
    left--; draw();
    if(left<=0){stop();beep();done++;count.textContent='Sessions finished: '+done}
  },1000);
};
document.getElementById('reset').onclick=()=>{stop();left=total;draw()};
document.querySelectorAll('#modes button').forEach(b=>b.onclick=()=>{
  document.querySelector('#modes .on').classList.remove('on');b.classList.add('on');
  chillOn=!!b.dataset.chill;document.documentElement.classList.toggle('chill-on',chillOn);
  if(chillOn){setChill(+document.getElementById('mins').textContent.split(' ')[0]||10)}
  else{stop();total=left=+b.dataset.m*60;draw()}
});
draw();
</script>
</body>
</html>
'''.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(PAGE)))
            self.end_headers()
            self.wfile.write(PAGE)
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Focus Timer running on port {port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
