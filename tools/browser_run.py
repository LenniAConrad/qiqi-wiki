#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run the wiki's browser checks and layout captures in headless Firefox.

Uses Firefox's built-in Marionette remote protocol with the standard library
only; no WebDriver download is needed. A small throwaway profile in the system
temporary directory and a localhost static server are removed afterwards;
captures are written under .cache/. Examples:

  python3 tools/browser_run.py --check tools/features_browser_checks.html
  python3 tools/browser_run.py --capture features.html --out .cache/qa
  python3 tools/browser_run.py --offline features.html --keyboard features.html
"""

import argparse
import base64
import contextlib
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SIZES = {"desktop": (1440, 900), "tablet": (820, 1180), "mobile": (390, 844)}
PREFS = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.aboutwelcome.enabled": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "app.update.disabledForTesting": True,
    "browser.tabs.warnOnClose": False,
    "ui.prefersReducedMotion": 1,
}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Marionette:
    """Minimal client for the length-prefixed JSON Marionette protocol."""

    def __init__(self, port, timeout=60):
        deadline = time.monotonic() + timeout
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.2)
        self.buffer = b""
        self.next_id = 0
        self._read()  # protocol handshake
        self.command("WebDriver:NewSession", {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}}})

    def _read(self):
        while b":" not in self.buffer:
            self.buffer += self._recv()
        length, rest = self.buffer.split(b":", 1)
        length = int(length)
        while len(rest) < length:
            rest += self._recv()
        self.buffer = rest[length:]
        return json.loads(rest[:length])

    def _recv(self):
        chunk = self.sock.recv(1 << 20)
        if not chunk:
            raise ConnectionError("Marionette closed the connection")
        return chunk

    def command(self, name, params=None):
        self.next_id += 1
        payload = json.dumps([0, self.next_id, name, params or {}]).encode()
        self.sock.sendall(str(len(payload)).encode() + b":" + payload)
        while True:
            message = self._read()
            if message[0] == 1 and message[1] == self.next_id:
                if message[2]:
                    raise RuntimeError(f"{name}: {message[2].get('message', message[2])}")
                result = message[3]
                return result.get("value", result) if isinstance(result, dict) else result

    def script(self, source, *args):
        return self.command("WebDriver:ExecuteScript", {"script": source, "args": list(args)})

    def navigate(self, url):
        self.command("WebDriver:Navigate", {"url": url})

    def size(self, width, height):
        self.command("WebDriver:SetWindowRect", {"width": width, "height": height})

    def keys(self, *sequence):
        actions = []
        for key in sequence:
            actions += [{"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}]
        self.command("WebDriver:PerformActions", {"actions": [{"type": "key", "id": "keyboard", "actions": actions}]})
        self.command("WebDriver:ReleaseActions")

    def screenshot(self, path, full=True):
        data = self.command("WebDriver:TakeScreenshot", {"full": full, "hash": False})
        path.write_bytes(base64.b64decode(data))


@contextlib.contextmanager
def static_server():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextlib.contextmanager
def firefox():
    # A fresh profile on a busy spinning disk can delay Marionette for minutes,
    # so the few-megabyte profile stays in the (fast) system temporary folder.
    profile = Path(tempfile.mkdtemp(prefix="qiqi-wiki-firefox-"))
    port = free_port()
    prefs = dict(PREFS, **{"marionette.port": port})
    (profile / "user.js").write_text("".join(f"user_pref({json.dumps(k)}, {json.dumps(v)});\n" for k, v in prefs.items()))
    env = dict(os.environ, MOZ_HEADLESS="1")
    process = subprocess.Popen(["firefox", "--headless", "--marionette", "--no-remote", "--profile", str(profile),
                                "about:blank"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        client = Marionette(port)
        yield client
        with contextlib.suppress(Exception):
            client.command("Marionette:Quit")
    finally:
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        shutil.rmtree(profile, ignore_errors=True)


def run_check(client, base, harness, timeout=120):
    client.size(*SIZES["desktop"])
    client.navigate(f"{base}/{harness}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = client.script("const r = document.querySelector('#report');"
                              "const done = r?.dataset.done ||"
                              " ({passed:'pass', failed:'fail'}[r?.dataset.result] || '');"
                              "return r ? {done, text: r.textContent} : null;")
        if state and state["done"]:
            print(state["text"].rstrip())
            return state["done"] == "pass"
        time.sleep(0.25)
    raise TimeoutError(f"{harness} did not finish within {timeout} s; last report: {state}")


ELEMENT = "element-6066-11e4-a52e-4f735466cecf"
MIN_WINDOW_WIDTH = 500  # headless Firefox clamps narrower windows
MAX_CAPTURE_HEIGHT = 32000


def framed(client, url, width, height):
    """Load url in a same-size iframe, for viewports narrower than a window."""
    client.size(width + 200, height)
    wrapper = ("<!doctype html><body style='margin:0'><iframe id='frame' src='" + url +
               f"' style='display:block;border:0;width:{width}px;height:{height}px'></iframe>")
    client.navigate("data:text/html;charset=utf-8," + quote(wrapper))
    frame = client.command("WebDriver:FindElement", {"using": "css selector", "value": "#frame"})[ELEMENT]
    client.command("WebDriver:SwitchToFrame", {"element": frame})
    deadline = time.monotonic() + 30
    while client.script("return document.readyState;") != "complete" and time.monotonic() < deadline:
        time.sleep(0.1)
    return frame


def capture(client, base, page, out):
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(page).stem
    measure = ("return [document.documentElement.scrollWidth - document.documentElement.clientWidth,"
               " document.documentElement.clientWidth, document.documentElement.scrollHeight];")
    for name, (width, height) in SIZES.items():
        target = out / f"{stem}-{name}.png"
        if width < MIN_WINDOW_WIDTH:
            frame = framed(client, f"{base}/{page}", width, height)
            time.sleep(0.4)
            overflow, viewport, full = client.script(measure)
            tall = full > MAX_CAPTURE_HEIGHT
            if tall and client.script("return !!document.querySelector('.feature');"):
                client.command("WebDriver:SwitchToParentFrame")
                shot = client.command("WebDriver:TakeScreenshot", {"id": frame, "full": False, "hash": False})
                (out / f"{stem}-{name}.png").write_bytes(base64.b64decode(shot))
                client.command("WebDriver:SwitchToFrame", {"element": frame})
                client.script("document.querySelector('.feature').scrollIntoView();")
                time.sleep(0.2)
                target = out / f"{stem}-{name}-ledger.png"
            client.command("WebDriver:SwitchToParentFrame")
            if not tall:
                client.script(f"document.querySelector('#frame').style.height = '{full}px';")
            time.sleep(0.2)
            data = client.command("WebDriver:TakeScreenshot", {"id": frame, "full": False, "hash": False})
            target.write_bytes(base64.b64decode(data))
        else:
            client.size(width, height)
            client.navigate(f"{base}/{page}")
            time.sleep(0.4)
            overflow, viewport, full = client.script(measure)
            # Firefox refuses screenshots taller than 65,535 px: capture the
            # top viewport and the first ledger viewport of very long pages.
            client.screenshot(target, full=full <= MAX_CAPTURE_HEIGHT)
            if full > MAX_CAPTURE_HEIGHT and client.script("return !!document.querySelector('.feature');"):
                client.script("document.querySelector('.feature').scrollIntoView();")
                time.sleep(0.2)
                client.screenshot(out / f"{stem}-{name}-ledger.png", full=False)
        print(f"{target} ({viewport}px layout width, {full}px tall, horizontal overflow {overflow}px)")
        if overflow > 0:
            print(f"FAIL: {page} overflows horizontally by {overflow}px at {name} width")
            return False
    return True


def offline(client, page):
    """Open a page through file:// to prove it needs no server or network."""
    client.size(*SIZES["desktop"])
    client.navigate((ROOT / page).as_uri())
    time.sleep(0.4)
    state = client.script("return {title: document.title, styled: getComputedStyle(document.documentElement).backgroundColor,"
                          "scripted: (!document.querySelector('script[src=\"wiki-ui.js\"]') ||"
                          " document.querySelector('.site-menu')?.dataset.enhanced === 'true') &&"
                          " (!document.querySelector('#result-count, #controls-count, #search-status') ||"
                          " document.querySelector('#result-count, #controls-count, #search-status').textContent.length > 0)};")
    ok = bool(state["title"]) and state["styled"] not in ("", "rgba(0, 0, 0, 0)") and state["scripted"]
    print(f"{'PASS' if ok else 'FAIL'}: {page} over file:// — title {state['title']!r}, background "
          f"{state['styled']}, script ran {state['scripted']}")
    return ok


def keyboard(client, base, page):
    """Real key presses: '/' focuses search, typing filters, Escape clears.

    Works on the wiki home, feature ledger and controls reference."""
    client.size(*SIZES["desktop"])
    client.navigate(f"{base}/{page}")
    time.sleep(0.3)
    client.script("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0);")
    client.keys("/")
    focused = client.script("return document.activeElement && document.activeElement.id;")
    client.keys(*"sailing")
    if focused == "wiki-search":
        count = client.script("return document.querySelectorAll('#search-results a').length;")
        client.keys("\ue007")  # Enter focuses the first result.
        result_focused = client.script("return document.activeElement === document.querySelector('#search-results a');")
        client.keys("/")
        client.keys("\ue00c")  # Escape clears the search.
        cleared = client.script("return document.querySelector('#wiki-search').value === '' &&"
                                " document.querySelector('#search-results').hidden;")
        client.keys("\ue004")  # Tab reaches the first category article.
        tabbed = client.script("return document.activeElement.getAttribute('href');")
        ok = count > 0 and result_focused and cleared and tabbed == "guide-getting-started.html"
        print(f"{'PASS' if ok else 'FAIL'}: keyboard on {page} — search results {count}, "
              f"Enter focused result {result_focused}, Escape cleared {cleared}, Tab reached {tabbed!r}")
        return ok
    rows = ".feature:not([hidden]), .control-row:not([hidden])"
    field = "document.querySelector('#search, #controls-search')"
    filtered = client.script(f"return [{field}.value, document.querySelectorAll('{rows}').length,"
                             " document.querySelectorAll('.feature, .control-row').length];")
    client.keys("\ue00c")  # Escape
    cleared = client.script(f"return [{field}.value, document.querySelectorAll('{rows}').length];")
    client.keys("\ue004")  # Tab moves from search to the first status filter (ledger only)
    tabbed = client.script("const a = document.activeElement; return a && a.closest('#filters') ? a.textContent : null;")
    has_filters = client.script("return !!document.querySelector('#filters');")
    ok = (focused in ("search", "controls-search") and filtered[0] == "sailing" and 0 < filtered[1] < filtered[2]
          and cleared == ["", filtered[2]] and (tabbed == "All" or not has_filters))
    print(f"{'PASS' if ok else 'FAIL'}: keyboard on {page} — '/' focused {focused!r}; 'sailing' shows "
          f"{filtered[1]} of {filtered[2]}; Escape restores {cleared[1]}; Tab reaches {tabbed!r}")
    return ok


def mobile_menu(client, base, page):
    """Exercise the native disclosure with real keys in a narrow iframe."""
    framed(client, f'{base}/{page}', *SIZES['mobile'])
    client.script("document.querySelector('.site-menu summary').focus();")
    initially_closed = client.script("return !document.querySelector('.site-menu').open;")
    client.keys('\ue007')  # Enter opens the disclosure.
    client.keys('\ue004')  # Tab enters its navigation.
    entered = client.script("return document.querySelector('.site-menu').open &&"
                            " document.activeElement === document.querySelector('.wiki-nav a');")
    client.keys('\ue00c')
    closed = client.script("return !document.querySelector('.site-menu').open &&"
                           " document.activeElement === document.querySelector('.site-menu summary');")
    client.keys('\ue004')
    skipped = client.script("return !document.activeElement.closest('.site-menu');")
    client.command('WebDriver:SwitchToParentFrame')
    ok = initially_closed and entered and closed and skipped
    print(f"{'PASS' if ok else 'FAIL'}: mobile keyboard on {page} — starts closed {initially_closed}, "
          f"Enter/Tab enters {entered}, Escape returns focus {closed}, closed menu skipped {skipped}")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="append", default=[], help="in-browser check harness (repo path)")
    parser.add_argument("--capture", action="append", default=[], help="page to capture at three widths")
    parser.add_argument("--offline", action="append", default=[], help="page that must work over file://")
    parser.add_argument("--keyboard", action="append", default=[], help="ledger page for real key presses")
    parser.add_argument("--mobile-menu", action="append", default=[], help="page for mobile menu keyboard checks")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "browser-qa")
    args = parser.parse_args()
    ok = True
    with static_server() as base, firefox() as client:
        for harness in args.check:
            ok &= run_check(client, base, harness)
        for page in args.keyboard:
            ok &= keyboard(client, base, page)
        for page in args.mobile_menu:
            ok &= mobile_menu(client, base, page)
        for page in args.offline:
            ok &= offline(client, page)
        for page in args.capture:
            ok &= capture(client, base, page, args.out)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
