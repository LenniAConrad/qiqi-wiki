#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Headless theme, keyboard, storage and file:// acceptance; captures stay private."""
import base64
import json
from pathlib import Path
import browser_run as browser

OUT = browser.ROOT / '.cache' / 'theme-review'
DARK = 'rgb(24, 35, 29)'
LIGHT = 'rgb(246, 243, 233)'


def state(client):
    return client.script('''return {
      background: getComputedStyle(document.documentElement).backgroundColor,
      choice: document.querySelector('#theme-choice').value,
      visible: !document.querySelector('.theme-choice').hidden,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      imageFilter: getComputedStyle(document.querySelector('.brand-logo')).filter,
      ink: getComputedStyle(document.documentElement).color,
      muted: getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(),
      accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
    };''')



def luminance(colour):
    if colour.startswith('#'):
        values = [int(colour[i:i+2], 16) for i in (1, 3, 5)]
    else:
        values = [int(v) for v in colour.removeprefix('rgb(').removesuffix(')').split(',')]
    linear = [v / 255 / 12.92 if v / 255 <= .04045 else ((v / 255 + .055) / 1.055) ** 2.4 for v in values]
    return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(first, second):
    a, b = sorted((luminance(first), luminance(second)))
    return (b + .05) / (a + .05)


def choose(client, choice):
    client.script('''const s = document.querySelector('#theme-choice');
      s.value = arguments[0]; s.dispatchEvent(new Event('change', {bubbles: true}));''', choice)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with browser.static_server() as base:
        browser.PREFS['ui.systemUsesDarkTheme'] = 1
        with browser.firefox() as client:
            client.navigate(base + '/index.html')
            assert state(client)['background'] == DARK
            assert state(client)['choice'] == 'system'
            # Real Tab reaches the native select from the preceding Search link.
            client.script("document.querySelector('.header-search').focus();")
            client.keys('\ue004')
            assert client.script('return document.activeElement.id;') == 'theme-choice'
            client.keys('\ue011', '\ue015', '\ue007')  # Home, Down, Enter: Light.
            assert state(client)['background'] == LIGHT, state(client)
            client.navigate(base + '/guide-controls.html')
            assert state(client)['background'] == LIGHT and state(client)['choice'] == 'light'
            choose(client, 'system')
            assert state(client)['background'] == DARK
            assert client.script("return localStorage.getItem('qiqi-theme');") is None
            print('PASS: keyboard and remembered/system choices', flush=True)
            results.append('system dark, keyboard Light, remembered navigation, return to system: PASS')
            for theme, expected in [('dark', DARK), ('light', LIGHT)]:
                client.navigate(base + '/index.html')
                choose(client, theme)
                for page in ['index.html', 'guide-controls.html', 'features.html', 'atlas.html']:
                    for label, width, height in [('desktop', 1440, 900), ('mobile', 390, 844)]:
                        frame = browser.framed(client, base + '/' + page, width, height,
                                       parent_url=base + '/index.html')
                        measured = state(client)
                        assert measured['background'] == expected, measured
                        for colour in ('ink', 'muted', 'accent'):
                            assert contrast(measured[colour], measured['background']) >= 4.5, measured
                        assert measured['overflow'] == 0 and measured['imageFilter'] == 'none', measured
                        client.command('WebDriver:SwitchToFrame', {'element': None})
                        shot = client.command('WebDriver:TakeScreenshot', {'id': frame, 'full': False, 'hash': False})
                        (OUT / f'{Path(page).stem}-{label}-{theme}.png').write_bytes(base64.b64decode(shot))
                        print(page, label, theme, 'PASS', flush=True)
                        results.append({'page': page, 'size': label, 'theme': theme, **measured})
            assert browser.keyboard(client, base, 'index.html')
            assert browser.mobile_menu(client, base, 'guide-controls.html')
            assert browser.offline(client, 'index.html')
            assert browser.offline(client, 'guide-controls.html')
            choose(client, 'dark')
            assert state(client)['background'] == DARK
            client.screenshot(OUT / 'offline-dark.png', full=False)
            results.append('keyboard search, mobile menu, static file URLs: PASS')
        for preference, expected in [(0, LIGHT), (1, DARK)]:
            browser.PREFS['ui.systemUsesDarkTheme'] = preference
            browser.PREFS['javascript.enabled'] = False
            with browser.firefox() as client:
                client.navigate(base + '/index.html')
                measured = state(client)
                assert measured['background'] == expected and not measured['visible'], measured
                results.append({'no_javascript_system': preference, **measured})
        browser.PREFS['javascript.enabled'] = True
        browser.PREFS['dom.storage.enabled'] = False
        with browser.firefox() as client:
            client.navigate(base + '/index.html')
            assert state(client)['visible']
            choose(client, 'light')
            assert state(client)['background'] == LIGHT
            choose(client, 'dark')
            assert state(client)['background'] == DARK
            results.append('storage denied: both explicit choices still work: PASS')
    (OUT / 'receipt.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'PASS: {len(results)} theme checks; captures in {OUT}')


if __name__ == '__main__':
    main()
