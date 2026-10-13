#!/usr/bin/env python3
# Renders the frame dumps with PPSSPPHeadless into out/<graphics>/<name>.png, in parallel.
#
#   python3 tools/render.py --headless ~/ppsspp/build/PPSSPPHeadless --graphics vulkan [--filter TEXT] [--out DIR]
#
# With --adb, renders them on an Android device instead, one at a time, into out/android-<graphics>/.
import argparse, os, shlex, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPSSPP = os.environ.get('PPSSPP', os.path.join(os.path.dirname(ROOT), 'ppsspp'))

def adb(serial, *cmd, check=True):
    r = subprocess.run(['adb'] + (['-s', serial] if serial else []) + list(cmd), capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit('adb %s failed:\n%s%s' % (' '.join(cmd), r.stdout, r.stderr))
    return r

def render_on_device(args, dumps, out):
    # One shell script for the whole set, so there's no adb round trip per dump.
    serial, dev = args.adb, args.device_dir
    q = shlex.quote
    print('Pushing %s, assets and dumps to %s (only what changed)...' % (args.device_headless, dev))
    adb(serial, 'shell', 'mkdir -p %s/shots' % q(dev))
    adb(serial, 'push', args.device_headless, dev + '/ppsspp_headless')
    adb(serial, 'shell', 'chmod 755 %s/ppsspp_headless' % q(dev))
    adb(serial, 'push', '--sync', os.path.join(PPSSPP, 'assets') + '/.', dev + '/assets')
    adb(serial, 'push', '--sync', os.path.join(ROOT, 'dumps') + '/.', dev + '/dumps')
    lines = ['cd %s || exit 1' % q(dev), 'rm -f shots/*.png']
    for name in dumps:
        lines.append('timeout 60 ./ppsspp_headless %s --graphics=%s --screenshot-save=%s %s > /dev/null 2>&1' % (
            q('dumps/%s.ppdmp' % name), q(args.graphics), q('shots/%s.png' % name), args.args))
    with tempfile.NamedTemporaryFile('w', suffix='.sh', delete=False) as f:
        f.write('\n'.join(lines) + '\n')
    adb(serial, 'push', f.name, dev + '/render.sh')
    os.unlink(f.name)
    print('Rendering %d dumps on the device...' % len(dumps))
    adb(serial, 'shell', 'sh %s/render.sh' % q(dev), check=False)
    adb(serial, 'pull', dev + '/shots/.', out)
    return [name for name in dumps if not os.path.exists(os.path.join(out, name + '.png'))]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--headless', default=os.environ.get('PPSSPP_HEADLESS'), help='PPSSPPHeadless binary (default: $PPSSPP_HEADLESS)')
    ap.add_argument('--graphics', default='software', help='software, vulkan, opengl, ... (default software)')
    ap.add_argument('--filter', default='', help='only dumps whose name contains this (case-insensitive)')
    ap.add_argument('--out', help='output directory (default out/<graphics>)')
    ap.add_argument('--args', default='', help='extra headless arguments')
    ap.add_argument('-j', type=int, default=os.cpu_count(), help='parallel runs')
    ap.add_argument('--adb', nargs='?', const='', default=None, metavar='SERIAL',
                    help='render on an Android device over adb (SERIAL picks one when several are connected)')
    ap.add_argument('--device-headless', default=os.path.join(PPSSPP, 'android/libs/arm64-v8a/ppsspp_headless'),
                    help='with --adb: the Android headless binary (default: $PPSSPP/android/libs/arm64-v8a/ppsspp_headless)')
    ap.add_argument('--device-dir', default='/data/local/tmp/ppsspp-framedumps', help='with --adb: where on the device everything goes')
    args = ap.parse_args()
    if args.adb is None and not args.headless:
        sys.exit('Pass --headless or set PPSSPP_HEADLESS')
    out = args.out or os.path.join(ROOT, 'out', ('android-' if args.adb is not None else '') + args.graphics)
    os.makedirs(out, exist_ok=True)
    dumps = sorted(f[:-6] for f in os.listdir(os.path.join(ROOT, 'dumps')) if f.endswith('.ppdmp') and args.filter.lower() in f.lower())

    if args.adb is not None:
        for name in dumps:
            try:
                os.unlink(os.path.join(out, name + '.png'))
            except OSError:
                pass
        failed = render_on_device(args, dumps, out)
        print('%d dumps rendered to %s, %d failed' % (len(dumps) - len(failed), out, len(failed)))
        for name in failed:
            print('  failed: ' + name)
        return

    def run(name):
        png = os.path.join(out, name + '.png')
        r = subprocess.run([args.headless, os.path.join(ROOT, 'dumps', name + '.ppdmp'), '--graphics=' + args.graphics,
                            '--screenshot-save=' + png, '--timeout-wall=60'] + args.args.split(), capture_output=True)
        return name, os.path.exists(png)

    failed = []
    with ThreadPoolExecutor(args.j) as ex:
        for name, ok in ex.map(run, dumps):
            if not ok:
                failed.append(name)
    print('%d dumps rendered to %s, %d failed' % (len(dumps) - len(failed), out, len(failed)))
    for name in failed:
        print('  failed: ' + name)

if __name__ == '__main__':
    main()
