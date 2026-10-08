#!/usr/bin/env python3
# Renders the frame dumps with PPSSPPHeadless into out/<graphics>/<name>.png, in parallel.
#
#   python3 tools/render.py --headless ~/ppsspp/build/PPSSPPHeadless --graphics vulkan [--filter TEXT] [--out DIR]
import argparse, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--headless', default=os.environ.get('PPSSPP_HEADLESS'), help='PPSSPPHeadless binary (default: $PPSSPP_HEADLESS)')
    ap.add_argument('--graphics', default='software', help='software, vulkan, opengl, ... (default software)')
    ap.add_argument('--filter', default='', help='only dumps whose name contains this (case-insensitive)')
    ap.add_argument('--out', help='output directory (default out/<graphics>)')
    ap.add_argument('--args', default='', help='extra headless arguments')
    ap.add_argument('-j', type=int, default=os.cpu_count(), help='parallel runs')
    args = ap.parse_args()
    if not args.headless:
        sys.exit('Pass --headless or set PPSSPP_HEADLESS')
    out = args.out or os.path.join(ROOT, 'out', args.graphics)
    os.makedirs(out, exist_ok=True)
    dumps = sorted(f[:-6] for f in os.listdir(os.path.join(ROOT, 'dumps')) if f.endswith('.ppdmp') and args.filter.lower() in f.lower())

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
