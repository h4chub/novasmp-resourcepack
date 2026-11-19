# NovaSMP resource pack

Optional resource pack for the NovaSMP Minecraft server (novasmp.pro).

- **Media rank icon**: the pink camera shown before Media players' names in chat, the TAB list and nametags.
  It is a bitmap font glyph on `U+2B24` in `minecraft:default` (Java pack format 88 for Minecraft 26.2, with
  `supported_formats` / `min_format` down to 34 for older clients joining through ViaVersion).
- Players who decline the pack see a plain white circle instead of the icon.
- Bedrock players (Geyser) get the same icon from the Bedrock pack (`font/glyph_2B.png`) installed in Geyser.

Releases contain `NovaSMP-resourcepack.zip` (Java) and `NovaSMP-bedrock.mcpack` (Bedrock) with their SHA-1/SHA-256.

## Build

`python3 tools/build_pack.py source/media-camera-original.jpg dist` rebuilds both packs from the original image
(only the outer white background is removed; the camera's own colours, white window and shadow are kept).
