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
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20viewBox=%270%200%2064%2064%27%3E%3Crect%20width=%2764%27%20height=%2764%27%20rx=%2716%27%20fill=%27%232f7d6d%27/%3E%3Ccircle%20cx=%2732%27%20cy=%2735%27%20r=%2716%27%20fill=%27none%27%20stroke=%27white%27%20stroke-width=%275%27/%3E%3Cpath%20d=%27M32%2035V25M32%2035l7%204%27%20stroke=%27white%27%20stroke-width=%274%27%20stroke-linecap=%27round%27%20fill=%27none%27/%3E%3Crect%20x=%2727%27%20y=%279%27%20width=%2710%27%20height=%275%27%20rx=%272%27%20fill=%27white%27/%3E%3C/svg%3E">
<meta name="theme-color" content="#2f7d6d">
<title>Focus Timer</title>
<style>
:root{--bg:#eef2f0;--card:#fff;--ink:#1d2b27;--mute:#6b7c76;--accent:#2f7d6d;--track:#dbe5e1;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121917;--card:#1b2623;--ink:#e8f0ed;--mute:#8fa39c;--accent:#5cc2ad;--track:#2b3a36}}
:root[data-theme="dark"]{--bg:#121917;--card:#1b2623;--ink:#e8f0ed;--mute:#8fa39c;--accent:#5cc2ad;--track:#2b3a36}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font-family:"Trebuchet MS",system-ui,sans-serif;display:flex;align-items:center;justify-content:center}
.app{background:var(--card);border-radius:28px;padding:28px;width:min(360px,92vw);text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.12)}
.modes{position:relative;display:flex;gap:6px;background:var(--track);border-radius:999px;padding:4px;margin-bottom:24px}
.modes button{position:relative;z-index:1;flex:1;transition:color .3s;border:0;background:none;color:var(--mute);padding:8px 4px;border-radius:999px;font:inherit;font-size:13px;cursor:pointer}
.modes button.on{color:var(--ink);font-weight:bold}
.pill{position:absolute;top:4px;bottom:4px;left:0;width:0;background:var(--card);border-radius:999px;box-shadow:0 1px 4px rgba(0,0,0,.15);transition:transform .35s cubic-bezier(.4,0,.2,1),width .35s cubic-bezier(.4,0,.2,1)}
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
.chill,.custom{display:flex;align-items:center;justify-content:center;gap:16px;max-height:0;opacity:0;overflow:hidden;margin-bottom:0;transform:translateY(-12px);transition:max-height .35s ease,opacity .3s ease,margin .35s ease,transform .35s ease;color:var(--mute);font-size:14px}
.chill button{width:36px;height:36px;border:0;border-radius:50%;background:var(--track);color:var(--ink);font-size:20px;cursor:pointer}
:root.chill-on{--bg:#1e1b2e;--card:#29253d;--ink:#ece9f7;--mute:#a49fc2;--accent:#b39ddb;--track:#3a3555}
:root.chill-on .chill,:root.timer-on .custom{max-height:44px;opacity:1;margin-bottom:16px;transform:none}
.custom input{width:56px;padding:8px 4px;border:0;border-radius:12px;background:var(--track);color:var(--ink);font:inherit;font-size:16px;text-align:center}
.msg{min-height:20px;margin:-6px 0 10px;font-size:14px;color:var(--accent)}
.count{margin-top:18px;color:var(--mute);font-size:14px}
</style>
</head>
<body>
<main class="app">
  <div class="modes" id="modes"><span class="pill" id="pill"></span>
    <button data-m="25" class="on">Focus</button>
    <button data-m="5">Short</button>
    <button data-m="15">Long</button>
    <button data-m="10" data-chill="1">Chill</button>
    <button data-m="5" data-timer="1">Timer</button>
  </div>
  <div class="ring">
    <svg viewBox="0 0 100 100"><circle class="bg" cx="50" cy="50" r="45"/><circle class="fg" id="fg" cx="50" cy="50" r="45"/></svg>
    <div class="time" id="time">25:00</div>
  </div>
  <div class="chill" id="chill"><button id="minus" aria-label="Less time">−</button><span id="mins">10 min</span><button id="plus" aria-label="More time">+</button></div>
  <div class="custom" id="custom"><input id="h" type="number" min="0" max="99" value="0" aria-label="Hours">h<input id="m" type="number" min="0" max="59" value="5" aria-label="Minutes">m<input id="s" type="number" min="0" max="59" value="0" aria-label="Seconds">s</div>
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
  const h=Math.floor(left/3600),mm=String(Math.floor(left%3600/60)).padStart(2,'0');
  timeEl.textContent=h?h+':'+mm+':'+s:m+':'+s;timeEl.style.fontSize=h?'42px':''; document.title=m+':'+s+' · Focus Timer';
  fg.style.strokeDashoffset=C*(1-(total?left/total:0));
}
function stop(){clearInterval(timer);timer=null;go.textContent='Start'}
let chillOn=false;
function beep(){try{const a=new (window.AudioContext||window.webkitAudioContext)(),o=a.createOscillator(),g=a.createGain();
  o.connect(g);g.connect(a.destination);o.type=chillOn?'sine':'square';o.frequency.value=chillOn?330:660;
  g.gain.setValueAtTime(chillOn?.15:.1,a.currentTime);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+(chillOn?1.8:.4));
  o.start();o.stop(a.currentTime+(chillOn?1.8:.4))}catch(e){}}
function setCustom(){stop();const v=id=>Math.max(0,Math.min(id=='h'?99:59,parseInt(document.getElementById(id).value)||0));
  total=left=v('h')*3600+v('m')*60+v('s');draw()}
['h','m','s'].forEach(i=>document.getElementById(i).addEventListener('input',setCustom));
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
  if(left<=0){showMsg('Set a time first');return}
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
  document.documentElement.classList.toggle('timer-on',!!b.dataset.timer);
  if(b.dataset.timer){setCustom()}
  else if(chillOn){setChill(+document.getElementById('mins').textContent.split(' ')[0]||10)}
  else{stop();total=left=+b.dataset.m*60;draw()}
});
function movePill(){const b=document.querySelector('#modes .on'),p=document.getElementById('pill');
  p.style.width=b.offsetWidth+'px';p.style.transform='translateX('+b.offsetLeft+'px)'}
document.querySelectorAll('#modes button').forEach(b=>b.addEventListener('click',movePill));
addEventListener('resize',movePill);movePill();
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
