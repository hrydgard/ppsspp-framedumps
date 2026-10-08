#!/usr/bin/env python3
# Compares renders (tools/render.py output, or any directory of NAME.png) with the PSP references in ref/,
# using PPSSPP's Tools/image_compare.py, which ignores differences of a pixel or two that any two
# rasterizers have. Pass a second directory to compare two renders with each other instead.
#
#   python3 tools/compare.py out/vulkan [--sort] [--heatmaps DIR] [--ppsspp ~/ppsspp]
#   python3 tools/compare.py out/vulkan out/opengl
import argparse, concurrent.futures, itertools, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a', help='directory of NAME.png renders')
    ap.add_argument('b', nargs='?', help='second directory (default: the PSP references in ref/)')
    ap.add_argument('--ppsspp', default=os.environ.get('PPSSPP', os.path.join(os.path.dirname(ROOT), 'ppsspp')),
                    help='PPSSPP checkout, for Tools/image_compare.py (default: $PPSSPP or ../ppsspp)')
    ap.add_argument('--sort', action='store_true', help='most different first')
    ap.add_argument('--all', action='store_true', help='list matching dumps too')
    ap.add_argument('--heatmaps', metavar='DIR', help='write side-by-side images of the differences')
    args = ap.parse_args()

    sys.path.insert(0, os.path.join(args.ppsspp, 'Tools'))
    import image_compare as ic

    names = sorted(f[:-4] for f in os.listdir(args.a) if f.endswith('.png'))
    if args.b:
        pairs = [(n + '.png', os.path.join(args.a, n + '.png'), os.path.join(args.b, n + '.png')) for n in names]
    else:
        pairs = [(n + '.png', os.path.join(args.a, n + '.png'), os.path.join(ROOT, 'ref', n + '-psp.png')) for n in names]
    pairs = [p for p in pairs if os.path.exists(p[2])]

    opts = argparse.Namespace(tolerance=12, radius=1, min_neighbors=5, block=8, block_tolerance=8.0, crop=(480, 272), heatmaps=args.heatmaps)
    if args.heatmaps:
        os.makedirs(args.heatmaps, exist_ok=True)
    with concurrent.futures.ProcessPoolExecutor() as ex:
        results = [r for r in ex.map(ic.compare_pair, pairs, itertools.repeat(opts), chunksize=4) if r]
    if args.sort:
        results.sort(key=lambda r: (-r[1], -r[2]))
    differing = total = 0
    for name, area, blocks, nblocks, bias in results:
        total += area
        if area or blocks:
            differing += 1
        if area or blocks or args.all:
            print('%7d px %5d/%d blocks  %s' % (area, blocks, nblocks, name[:-4]))
    print('%d compared, %d differ, %d px in total' % (len(results), differing, total))

if __name__ == '__main__':
    main()
