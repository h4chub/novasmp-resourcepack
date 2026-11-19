"""Build the NovaSMP Media icon packs from the exact source icon (no redrawing, no recolouring).

  python3 build_pack.py <icon.png> <outdir>

Java  : NovaSMP-resourcepack.zip  - bitmap font glyph for U+2B24 in minecraft:default (chat, TAB list, nametags)
Bedrock: NovaSMP-bedrock.mcpack   - glyph sheet font/glyph_2B.png (cell 0x24) for Geyser
The glyph code point is U+2B24. Players without the Java pack see the vanilla character (a plain white circle)
instead of a broken box.
"""
import sys, os, json, uuid, zipfile, hashlib, io
from PIL import Image

CP = 0x2B24
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
def white_to_alpha(img):
    """The supplied icon is a JPEG on a white background. Remove ONLY the outer white background (white connected to the
    image border). White INSIDE the icon (the camera's window) stays opaque white. Edge pixels between the background
    and the icon get alpha from how far they are from white and their original colour is recovered (white un-mixed), so
    the pink, the dark shadow and the outline keep their colours and shape. JPEG noise in the background is removed."""
    from collections import deque
    rgb = img.convert('RGB'); W, H = rgb.size; px = rgb.load()
    light = lambda x, y: min(px[x, y]) > 200
    bg = [[False] * W for _ in range(H)]; q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if light(x, y) and not bg[y][x]: bg[y][x] = True; q.append((x, y))
    for y in range(H):
        for x in (0, W - 1):
            if light(x, y) and not bg[y][x]: bg[y][x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not bg[ny][nx] and light(nx, ny): bg[ny][nx] = True; q.append((nx, ny))
    near = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if bg[y][x]:
                for dy in (-2, -1, 0, 1, 2):
                    for dx in (-2, -1, 0, 1, 2):
                        if 0 <= x + dx < W and 0 <= y + dy < H: near[y + dy][x + dx] = True
    out = Image.new('RGBA', (W, H)); dst = out.load()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if not near[y][x]: dst[x, y] = (r, g, b, 255); continue          # inside the icon: untouched, opaque
            a = min(1.0, (255 - min(r, g, b)) / 245.0)
            if a < 0.10: dst[x, y] = (0, 0, 0, 0); continue
            un = lambda c: max(0, min(255, round(255 - (255 - c) / a)))
            dst[x, y] = (un(r), un(g), un(b), round(a * 255))
    return out

raw = Image.open(src)
im = raw.convert('RGBA') if raw.mode in ('RGBA', 'LA', 'P') and 'A' in raw.convert('RGBA').getbands() and raw.convert('RGBA').getchannel('A').getextrema()[0] < 255 else white_to_alpha(raw)
bbox = im.getchannel('A').getbbox()              # trim only empty margins (shape/proportions unchanged)
icon = im.crop(bbox) if bbox else im
icon.save(os.path.join(out, 'icon-cutout-full-size.png'))
w, h = icon.size
print('source', im.size, '-> trimmed', icon.size)

def fit(img, size):
    """Scale to height `size` keeping the aspect ratio; resampled with premultiplied alpha so edges keep their colour."""
    iw, ih = img.size; nh = size; nw = max(1, round(iw * nh / ih))
    return img.convert('RGBa').resize((nw, nh), Image.LANCZOS).convert('RGBA')

# ---------------- Java pack
tex = fit(icon, 32) if h > 32 else icon          # 32 px source texture rendered at 8 px text height: sharp at every GUI scale
jbuf = io.BytesIO()
with zipfile.ZipFile(jbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('pack.mcmeta', json.dumps({"pack": {"pack_format": 88, "supported_formats": [34, 88], "min_format": 34, "max_format": 88,
                                                    "description": "NovaSMP: Media rank icon"}}, indent=2))
    b = io.BytesIO(); tex.save(b, 'PNG'); z.writestr('assets/novasmp/textures/font/media_camera.png', b.getvalue())
    z.writestr('assets/minecraft/font/default.json', json.dumps({"providers": [
        {"type": "bitmap", "file": "novasmp:font/media_camera.png", "ascent": 7, "height": 8, "chars": [chr(CP)]}]}, ensure_ascii=False, indent=2))
    ic = fit(icon, 64) if h > 64 else icon; canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); canvas.paste(ic, ((64 - ic.size[0]) // 2, (64 - ic.size[1]) // 2), ic)
    b = io.BytesIO(); canvas.save(b, 'PNG'); z.writestr('pack.png', b.getvalue())
jpath = os.path.join(out, 'NovaSMP-resourcepack.zip'); open(jpath, 'wb').write(jbuf.getvalue())
print('java', jpath, 'sha1', hashlib.sha1(jbuf.getvalue()).hexdigest(), 'sha256', hashlib.sha256(jbuf.getvalue()).hexdigest())

# ---------------- Bedrock pack (Geyser)
CELL = 32
sheet = Image.new('RGBA', (CELL * 16, CELL * 16), (0, 0, 0, 0))
# Fit INSIDE one 32x32 cell (width is the limiting side for this wide camera) so nothing spills into the neighbouring
# cell (U+2B25) and the camera's right edge is not clipped. Aspect ratio unchanged.
iw, ih = icon.size; bw = CELL; bh = CELL - 4
sc = min(bw / iw, bh / ih); g = icon.convert('RGBa').resize((max(1, round(iw * sc)), max(1, round(ih * sc))), Image.LANCZOS).convert('RGBA')
row, col = (CP & 0xFF) >> 4, CP & 0x0F
sheet.paste(g, (col * CELL + (CELL - g.size[0]) // 2, row * CELL + (CELL - g.size[1]) // 2 + 1), g)
manifest = {"format_version": 2, "header": {"name": "NovaSMP Media icon", "description": "NovaSMP rank icons", "uuid": str(uuid.uuid5(uuid.NAMESPACE_DNS, 'novasmp.pro/bedrock-pack/header')),
            "version": [1, 0, 1], "min_engine_version": [1, 20, 0]},
            "modules": [{"type": "resources", "uuid": str(uuid.uuid5(uuid.NAMESPACE_DNS, 'novasmp.pro/bedrock-pack/module')), "version": [1, 0, 1]}]}
bbuf = io.BytesIO()
with zipfile.ZipFile(bbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('manifest.json', json.dumps(manifest, indent=2))
    b = io.BytesIO(); sheet.save(b, 'PNG'); z.writestr('font/glyph_2B.png', b.getvalue())
    b = io.BytesIO(); canvas.save(b, 'PNG'); z.writestr('pack_icon.png', b.getvalue())
bpath = os.path.join(out, 'NovaSMP-bedrock.mcpack'); open(bpath, 'wb').write(bbuf.getvalue())
print('bedrock', bpath, 'sha256', hashlib.sha256(bbuf.getvalue()).hexdigest())
tex.save(os.path.join(out, 'glyph-preview-32px.png'))
