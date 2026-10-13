#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Measure initial static-page requests with a fresh Firefox profile and disabled HTTP cache."""
import argparse, contextlib, functools, hashlib, http.server, json, sys, threading, time
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--tools',type=Path,default=Path(__file__).resolve().parent,help='Directory containing browser_run.py')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--page',action='append')
parser.add_argument('--mode',action='append',choices=['desktop','mobile','mobile-constrained'],help='Only these profiles; default: all applicable profiles')
parser.add_argument('--startup-timeout',type=float,default=60,help='Firefox connection/command timeout in seconds; allow more on busy disks')
parser.add_argument('--require-complete',action='store_true',help='Save the sample and fail immediately if any response body size is unavailable')
parser.add_argument('--base',help='Use a deployed origin instead of a local server; no synthetic throttling')
args=parser.parse_args()
args.root=args.root.resolve()
args.tools=args.tools.resolve()
args.out.parent.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(args.tools))
import browser_run as b
from loading_metrics import body_totals
b.ROOT=args.root
b.PREFS.update({'browser.cache.disk.enable':False,'browser.cache.memory.enable':False,'network.http.use-cache':False})
runner_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),args.tools/'browser_run.py',args.tools/'loading_metrics.py')}

class Bandwidth:
    def __init__(self,bps=0):
        self.bps=bps;self.next=0;self.lock=threading.Lock()
    def wait(self,count):
        if not self.bps:return
        with self.lock:
            self.next=max(self.next,time.monotonic())+count/self.bps;end=self.next
        time.sleep(max(0,end-time.monotonic()))

@contextlib.contextmanager
def server(bps,latency):
    throttle=Bandwidth(bps)
    class Handler(b.QuietHandler):
        def do_GET(self):
            if latency:time.sleep(latency/1000)
            try:super().do_GET()
            except (BrokenPipeError,ConnectionResetError):pass
        def copyfile(self,source,target):
            while data:=source.read(8192):
                throttle.wait(len(data));target.write(data)
    s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(args.root)))
    thread=threading.Thread(target=s.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{s.server_address[1]}'
    finally:s.shutdown();s.server_close()

rows=[]
for mode,width,height,bps,latency in [('desktop',1440,900,0,0),('mobile',390,844,0,0),('mobile-constrained',390,844,200_000,150)]:
    if args.mode and mode not in args.mode:continue
    if args.base and bps:continue
    source=contextlib.nullcontext(args.base.rstrip('/')) if args.base else server(bps,latency)
    with source as base:
        for page in (args.page or ['index.html','animals.html','guide-crafting.html','islands.html']):
            # Fresh profile PER PAGE: Firefox also has a stylesheet cache that
            # can survive navigation when the ordinary HTTP cache is disabled.
            with b.firefox(startup_timeout=args.startup_timeout) as c:
                start=time.monotonic()
                harness={}
                if width<500:b.framed(c,base+'/'+page,width,height,parent_url=base+'/wiki.css',setup_receipt=harness,load_timeout=args.startup_timeout)
                else:c.size(width,height);c.navigate(base+'/'+page)
                media_selector = c.script("return document.querySelector('#grid') ? '#grid' : document.querySelector('.mob-model') ? '.mob-model' : document.querySelector('.guide-figure') ? '.guide-figure' : null;")
                for phase in (['initial', 'first-media-row'] if media_selector else ['initial']):
                    if phase=='first-media-row':c.script("document.querySelector(arguments[0]).scrollIntoView({behavior:'instant',block:'start',inline:'nearest'});", media_selector)
                    previous=None;stable=0
                    for _ in range(160):
                        counts=c.script("return [performance.getEntriesByType('resource').length,[...document.images].filter(i=>i.getClientRects().length&&i.getBoundingClientRect().top<innerHeight&&i.getBoundingClientRect().bottom>0&&i.getBoundingClientRect().left<innerWidth&&i.getBoundingClientRect().right>0&&!i.complete).length];")
                        stable=stable+1 if counts==previous and counts[1]==0 else 0;previous=counts
                        if stable>=3:break
                        time.sleep(.25)
                    if stable<3:raise RuntimeError('Visible images did not settle: '+page+' '+phase)
                    data=c.script("""return {url:document.URL,navigation:performance.getEntriesByType('navigation').map(e=>({url:e.name,encoded:e.encodedBodySize,transfer:e.transferSize,loadMs:e.loadEventEnd,domMs:e.domContentLoadedEventEnd})),resources:performance.getEntriesByType('resource').map(e=>({url:e.name,kind:e.initiatorType,encoded:e.encodedBodySize,transfer:e.transferSize,durationMs:e.duration})),images:[...document.images].map(i=>({src:i.currentSrc,width:i.clientWidth,height:i.clientHeight,naturalWidth:i.naturalWidth,complete:i.complete,loading:i.loading})),viewport:[innerWidth,innerHeight],pixelRatio:devicePixelRatio,userAgent:navigator.userAgent};""")
                    assert data['url']==base+'/'+page,data['url']
                    if width<500:assert data['viewport']==[width,height],data['viewport']
                    if harness:
                        harness['resources']=c.script("return parent.performance.getEntriesByType('resource').filter(e=>e.initiatorType!=='iframe').map(e=>({url:e.name,encoded:e.encodedBodySize,transfer:e.transferSize}));")
                        harness.update(body_totals(harness['navigation'],harness['resources']))
                    row={'page':page,'mode':mode,'phase':phase,'requestedViewport':[width,height],'harness':harness.copy(),'network':{'bytesPerSecond':bps,'addedResponseLatencyMs':latency,'cache':'fresh profile per page, disabled HTTP cache','origin':base},**body_totals(data['navigation'],data['resources']),'settledSeconds':round(time.monotonic()-start,3),**data}
                    rows.append(row);print(page,mode,phase,row['requests'],row['encodedBytes'],row['settledSeconds'],flush=True)
                    args.out.write_text(json.dumps({'schemaVersion':2,'runnerHashes':runner_hashes,'method':'Firefox headless; fresh profile PER PAGE, cache disabled. Initial viewport, then first gallery/reference/guide image. Mobile replaces a same-origin wiki.css text document with a sized iframe; its setup/navigation and other parent requests are recorded separately in harness. This warms the origin connection even with disabled HTTP cache. settledSeconds includes this setup; iframe fully inside the parent viewport; visible images intersect both viewport axes. Wait for visible images and three stable 250ms request-count samples. Constrained local profile shares 200000 bytes/s across responses and adds150 ms response latency. Null encodedBytes/transferBytes means at least one response size is unavailable; reportedEncodedBytes/reportedTransferBytes are only the exposed sums. unmeasuredBodies lists any missing URLs. Totals include only document/resource timing entries at the checkpoint; transferBytes is a browser estimate including headers, not a packet capture. Not a real phone or LCP benchmark.','measuredAt':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'root':str(args.root),'rows':rows},indent=2)+'\n')
                    if args.require_complete and row['unmeasuredBodies']:
                        raise RuntimeError('Incomplete response sizes saved to '+str(args.out)+': '+', '.join(row['unmeasuredBodies']))
