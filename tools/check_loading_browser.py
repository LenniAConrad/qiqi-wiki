#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check Firefox's desktop/mobile byte accounting against actual gzip responses.

Run explicitly (not in the static gate):
  python3 tools/check_loading_browser.py --out /path/to/private/receipt.json
Set TMPDIR to an owned scratch directory for the disposable browser profiles.
"""
import argparse
from collections import Counter
import gzip
import http.server
import json
from pathlib import Path
import threading
import time

import browser_run as browser
from loading_metrics import body_totals


HTML = ("<!doctype html><meta name='viewport' content='width=device-width'>"
        "<link rel='stylesheet' href='style.css'><title>Loading check</title>"
        "<img src='picture.svg' width='100' height='60' alt='Test rectangle'>"
        + "<p>Compressible document body.</p>" * 200).encode()
CSS = b"body { margin: 0; color: #123; }\n" * 20
SVG = b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='60'><path fill='#abc' d='M0 0h100v60H0z'/></svg>"
RESPONSES = {
    '/index.html': (gzip.compress(HTML, mtime=0), 'text/html', True),
    '/style.css': (gzip.compress(CSS, mtime=0), 'text/css', True),
    '/picture.svg': (SVG, 'image/svg+xml', False),
    '/favicon.ico': (SVG, 'image/svg+xml', False),
    '/wrapper.css': (gzip.compress(CSS, mtime=0), 'text/css', True),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--startup-timeout', type=float, default=60)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    served = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in RESPONSES:
                self.send_error(404)
                return
            body, mime, compressed = RESPONSES[self.path]
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
            self.end_headers()
            self.wfile.write(body)
            served.append({'path': self.path, 'encodedBytes': len(body)})

        def log_message(self, *args):
            pass

    browser.PREFS.update({'browser.cache.disk.enable': False,
                          'browser.cache.memory.enable': False,
                          'network.http.use-cache': False})
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    rows = []
    try:
        for mode, width, height in [('desktop', 1440, 900), ('mobile', 390, 844)]:
            served.clear()
            with browser.firefox(startup_timeout=args.startup_timeout) as client:
                setup_receipt = {}
                if mode == 'mobile':
                    browser.framed(client, base + '/index.html', width, height,
                                   parent_url=base + '/wrapper.css', setup_receipt=setup_receipt)
                else:
                    client.size(width, height)
                    client.navigate(base + '/index.html')
                deadline = time.monotonic() + 30
                previous = None
                stable = 0
                while True:
                    data = client.script("""return {
                        url: document.URL, viewport: [innerWidth, innerHeight],
                        loaded: document.readyState === 'complete' && [...document.images].every(i => i.complete && i.naturalWidth > 0),
                        navigation: performance.getEntriesByType('navigation').map(e => ({url: e.name, encoded: e.encodedBodySize, transfer: e.transferSize, decoded: e.decodedBodySize})),
                        resources: performance.getEntriesByType('resource').map(e => ({url: e.name, encoded: e.encodedBodySize, transfer: e.transferSize}))
                    };""")
                    counts = (len(data['resources']), len(served))
                    stable = stable + 1 if data['loaded'] and counts == previous else 0
                    previous = counts
                    if stable >= 3:
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError('Fixture did not finish loading')
                    time.sleep(.25)
                total = body_totals(data['navigation'], data['resources'])
                if setup_receipt:
                    setup_receipt['resources'] = client.script("""return parent.performance.getEntriesByType('resource')
                        .filter(e => e.initiatorType !== 'iframe')
                        .map(e => ({url: e.name, encoded: e.encodedBodySize, transfer: e.transferSize}));""")
                setup_entries = setup_receipt.get('navigation', []) + setup_receipt.get('resources', [])
                row = {'mode': mode, 'responses': served[:], 'harness': setup_receipt, **data, **total}
                rows.append(row)
                args.out.write_text(json.dumps({'rows': rows}, indent=2) + '\n')
                assert data['url'] == base + '/index.html', data['url']
                if mode == 'mobile':
                    assert data['viewport'] == [390, 844], data['viewport']
                entries = data['navigation'] + data['resources']
                expected = Counter((base + r['path'], r['encodedBytes']) for r in served)
                measured = Counter((r['url'], r['encoded']) for r in entries + setup_entries)
                assert measured == expected, (measured, expected)
                assert {'/index.html', '/style.css', '/picture.svg'} <= {r['path'] for r in served}, served
                assert len(data['navigation']) == 1, data['navigation']
                assert data['navigation'][0]['encoded'] == len(RESPONSES['/index.html'][0]), row
                assert data['navigation'][0]['decoded'] == len(HTML), row
                assert len(setup_receipt.get('navigation', [])) == (1 if mode == 'mobile' else 0), setup_receipt
                assert total['requests'] + len(setup_entries) == len(served), row
                assert total['encodedBytes'] + sum(r['encoded'] for r in setup_entries) == sum(r['encodedBytes'] for r in served), row
                assert total['unmeasuredBodies'] == [], row
                assert total['transferBytes'] >= total['encodedBytes'], row
                print(f"PASS {mode}: {total['requests']} responses, {total['encodedBytes']} encoded bytes including compressed HTML", flush=True)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
