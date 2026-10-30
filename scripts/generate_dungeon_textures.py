"""Procedural High-Fidelity Texture Generator for Dungeon Crawler & PBR Scenes.

Generates diffuse albedo and normal maps for:
- Stone flagstone floor
- Gothic ashlar brick walls
- Carved stone pillars
- Antique iron-banded dark oak chest
"""

from pathlib import Path
import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def height_to_normal(height: np.ndarray, strength: float = 2.5) -> np.ndarray:
    """Generate high-quality tangent-space normal map from single-channel heightmap using Sobel filter."""
    h, w = height.shape
    # Sobel kernels
    dx = np.zeros((h, w), dtype=np.float32)
    dy = np.zeros((h, w), dtype=np.float32)

    # Central difference with wrap-around
    dx[:, :] = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dy[:, :] = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5

    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones((h, w), dtype=np.float32)

    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length

    # Map from [-1, 1] to [0, 255]
    r = ((nx * 0.5 + 0.5) * 255.0).astype(np.uint8)
    g = ((ny * 0.5 + 0.5) * 255.0).astype(np.uint8)
    b = ((nz * 0.5 + 0.5) * 255.0).astype(np.uint8)
    a = np.full((h, w), 255, dtype=np.uint8)

    return np.stack([r, g, b, a], axis=-1)


def generate_flagstone_floor(size: int = 512):
    """Generate ancient weathered crypt flagstones with deep mortar grooves."""
    rng = np.random.RandomState(42)
    h_map = np.zeros((size, size), dtype=np.float32)
    color_map = np.zeros((size, size, 4), dtype=np.uint8)

    # Base stone texture with fine multi-octave noise
    noise1 = rng.uniform(0.0, 1.0, (size // 8, size // 8)).astype(np.float32)
    noise2 = rng.uniform(0.0, 1.0, (size // 2, size // 2)).astype(np.float32)

    img_n1 = Image.fromarray((noise1 * 255).astype(np.uint8)).resize((size, size), Image.Resampling.BICUBIC)
    img_n2 = Image.fromarray((noise2 * 255).astype(np.uint8)).resize((size, size), Image.Resampling.BILINEAR)

    n1_arr = np.array(img_n1, dtype=np.float32) / 255.0
    n2_arr = np.array(img_n2, dtype=np.float32) / 255.0
    fine_noise = n1_arr * 0.7 + n2_arr * 0.3

    # Tile layout: 4x4 large flagstones with irregular jitter
    num_tiles = 4
    tile_w = size // num_tiles
    mortar_width = 10

    tile_heights = rng.uniform(0.65, 0.95, (num_tiles, num_tiles))
    tile_colors = [
        (85, 90, 96),   # Cold slate
        (92, 88, 82),   # Ancient weathered stone
        (76, 80, 85),   # Dark charcoal flagstone
        (100, 98, 92),  # Mossy limestone
    ]

    for ty in range(num_tiles):
        for tx in range(num_tiles):
            x0 = tx * tile_w
            x1 = (tx + 1) * tile_w
            y0 = ty * tile_w
            y1 = (ty + 1) * tile_w

            # Base tile height and color
            th = tile_heights[ty, tx]
            tcol = tile_colors[(tx + ty * 3) % len(tile_colors)]

            # Inner tile area
            inner_x0 = x0 + mortar_width // 2
            inner_x1 = x1 - mortar_width // 2
            inner_y0 = y0 + mortar_width // 2
            inner_y1 = y1 - mortar_width // 2

            h_map[y0:y1, x0:x1] = 0.25 # Mortar depth

            # Beveled tile interior
            sub_y, sub_x = np.ogrid[0:(inner_y1 - inner_y0), 0:(inner_x1 - inner_x0)]
            dist_to_edge = np.minimum(
                np.minimum(sub_x, (inner_x1 - inner_x0) - 1 - sub_x),
                np.minimum(sub_y, (inner_y1 - inner_y0) - 1 - sub_y),
            )
            bevel = np.clip(dist_to_edge / 12.0, 0.0, 1.0)
            tile_h = (th * 0.8 + fine_noise[inner_y0:inner_y1, inner_x0:inner_x1] * 0.2) * bevel

            h_map[inner_y0:inner_y1, inner_x0:inner_x1] = tile_h

            # Tile color
            for c in range(3):
                c_val = tcol[c] * (0.8 + fine_noise[inner_y0:inner_y1, inner_x0:inner_x1] * 0.4) * (0.6 + bevel * 0.4)
                color_map[inner_y0:inner_y1, inner_x0:inner_x1, c] = np.clip(c_val, 0, 255).astype(np.uint8)

    # Mortar dark coloring
    mortar_mask = (h_map <= 0.3)
    color_map[mortar_mask, 0] = np.clip(38 + fine_noise[mortar_mask] * 15, 0, 255).astype(np.uint8)
    color_map[mortar_mask, 1] = np.clip(36 + fine_noise[mortar_mask] * 15, 0, 255).astype(np.uint8)
    color_map[mortar_mask, 2] = np.clip(42 + fine_noise[mortar_mask] * 18, 0, 255).astype(np.uint8)
    color_map[:, :, 3] = 255

    # Export
    diffuse_img = Image.fromarray(color_map, "RGBA")
    diffuse_img.save(OUT_DIR / "dungeon_stone_floor.png")

    normal_arr = height_to_normal(h_map, strength=4.0)
    normal_img = Image.fromarray(normal_arr, "RGBA")
    normal_img.save(OUT_DIR / "dungeon_stone_floor_normal.png")
    print("[Textures] Generated dungeon_stone_floor.png and dungeon_stone_floor_normal.png")


def generate_ashlar_walls(size: int = 512):
    """Generate dark medieval ashlar brick masonry walls with recessed mortar."""
    rng = np.random.RandomState(88)
    h_map = np.zeros((size, size), dtype=np.float32)
    color_map = np.zeros((size, size, 4), dtype=np.uint8)

    rows = 8
    row_h = size // rows
    brick_w = size // 4
    mortar = 6

    # Base noise
    noise_low = rng.uniform(0.0, 1.0, (size // 8, size // 8)).astype(np.float32)
    noise_img = Image.fromarray((noise_low * 255).astype(np.uint8)).resize((size, size), Image.Resampling.BICUBIC)
    noise = np.array(noise_img, dtype=np.float32) / 255.0

    h_map[:, :] = 0.2 # Deep mortar

    for r in range(rows):
        y0 = r * row_h
        y1 = (r + 1) * row_h
        offset = (brick_w // 2) if (r % 2 == 1) else 0

        num_bricks = (size // brick_w) + 2
        for b in range(-1, num_bricks):
            x0 = b * brick_w + offset
            x1 = x0 + brick_w

            # Clip to [0, size]
            clip_x0 = max(0, x0 + mortar // 2)
            clip_x1 = min(size, x1 - mortar // 2)
            clip_y0 = max(0, y0 + mortar // 2)
            clip_y1 = min(size, y1 - mortar // 2)

            if clip_x1 <= clip_x0 or clip_y1 <= clip_y0:
                continue

            bh = rng.uniform(0.7, 0.95)
            # Brick color: somber weathered gothic stone (cool charcoal/slate)
            base_grey = rng.uniform(85.0, 115.0)

            sub_y, sub_x = np.ogrid[0:(clip_y1 - clip_y0), 0:(clip_x1 - clip_x0)]
            edge_dist = np.minimum(
                np.minimum(sub_x, (clip_x1 - clip_x0) - 1 - sub_x),
                np.minimum(sub_y, (clip_y1 - clip_y0) - 1 - sub_y),
            )
            bevel = np.clip(edge_dist / 6.0, 0.0, 1.0)

            brick_h = (bh * 0.85 + noise[clip_y0:clip_y1, clip_x0:clip_x1] * 0.15) * bevel
            h_map[clip_y0:clip_y1, clip_x0:clip_x1] = brick_h

            for c in range(3):
                col_factor = 1.0 if c == 0 else (0.96 if c == 1 else 1.04) # Slight blue-slate tint
                c_val = base_grey * col_factor * (0.85 + noise[clip_y0:clip_y1, clip_x0:clip_x1] * 0.3) * (0.7 + bevel * 0.3)
                color_map[clip_y0:clip_y1, clip_x0:clip_x1, c] = np.clip(c_val, 0, 255).astype(np.uint8)

    # Mortar coloration
    mortar_mask = (h_map <= 0.25)
    color_map[mortar_mask, 0] = np.clip(45 + noise[mortar_mask] * 12, 0, 255).astype(np.uint8)
    color_map[mortar_mask, 1] = np.clip(42 + noise[mortar_mask] * 12, 0, 255).astype(np.uint8)
    color_map[mortar_mask, 2] = np.clip(48 + noise[mortar_mask] * 14, 0, 255).astype(np.uint8)
    color_map[:, :, 3] = 255

    diffuse_img = Image.fromarray(color_map, "RGBA")
    diffuse_img.save(OUT_DIR / "dungeon_stone_wall.png")

    normal_arr = height_to_normal(h_map, strength=4.5)
    normal_img = Image.fromarray(normal_arr, "RGBA")
    normal_img.save(OUT_DIR / "dungeon_stone_wall_normal.png")
    print("[Textures] Generated dungeon_stone_wall.png and dungeon_stone_wall_normal.png")


def generate_chest_texture(size: int = 512):
    """Generate antique iron-banded dark oak wood planks with gilded brass lock plate."""
    rng = np.random.RandomState(99)
    color_map = np.zeros((size, size, 4), dtype=np.uint8)
    h_map = np.zeros((size, size), dtype=np.float32)

    # Wood grain noise: stretched vertically
    grain_noise = rng.uniform(0.0, 1.0, (size // 2, size // 32)).astype(np.float32)
    grain_img = Image.fromarray((grain_noise * 255).astype(np.uint8)).resize((size, size), Image.Resampling.BICUBIC)
    grain = np.array(grain_img, dtype=np.float32) / 255.0

    # 1. Base dark oak wood planks
    num_planks = 6
    plank_h = size // num_planks
    for p in range(num_planks):
        y0 = p * plank_h
        y1 = (p + 1) * plank_h
        plank_var = rng.uniform(0.85, 1.15)
        for y in range(y0, y1):
            for x in range(size):
                # Seam at plank border
                edge_dist = min(y - y0, y1 - 1 - y)
                seam = np.clip(edge_dist / 3.0, 0.0, 1.0)
                g_val = grain[y, x] * 0.35 + 0.65
                r = 95.0 * plank_var * g_val * seam
                g = 55.0 * plank_var * g_val * seam
                b = 32.0 * plank_var * g_val * seam
                color_map[y, x] = [int(np.clip(r, 0, 255)), int(np.clip(g, 0, 255)), int(np.clip(b, 0, 255)), 255]
                h_map[y, x] = 0.5 * seam + grain[y, x] * 0.1

    # 2. Horizontal Iron Bands (Top band around y=80..130, Bottom band around y=380..430)
    band_regions = [(70, 120), (390, 440)]
    for by0, by1 in band_regions:
        for y in range(by0, by1):
            edge_y = min(y - by0, by1 - 1 - y)
            bevel = np.clip(edge_y / 4.0, 0.0, 1.0)
            h_map[by0:by1, :] = 0.75 + bevel * 0.15
            for x in range(size):
                # Studs / Rivets every 64 pixels
                dx_stud = abs((x % 64) - 32)
                dy_stud = abs(y - ((by0 + by1) // 2))
                dist_stud = np.sqrt(dx_stud * dx_stud + dy_stud * dy_stud)
                if dist_stud < 9.0:
                    # Rivet highlight
                    stud_h = np.sqrt(max(0.0, 81.0 - dist_stud * dist_stud)) / 9.0
                    h_map[y, x] = 0.9 + stud_h * 0.25
                    color_map[y, x] = [210, 185, 95, 255] # Brass stud
                else:
                    # Dark wrought iron
                    iron_shade = int(48.0 * (0.8 + bevel * 0.4 + grain[y, x] * 0.15))
                    color_map[y, x] = [iron_shade + 6, iron_shade + 8, iron_shade + 12, 255]

    # 3. Center Gilded Brass Keyhole Plate (x: 216..296, y: 216..296)
    lx0, lx1 = 216, 296
    ly0, ly1 = 216, 296
    for y in range(ly0, ly1):
        for x in range(lx0, lx1):
            cx = x - 256
            cy = y - 256
            d = np.sqrt(cx * cx + cy * cy)
            if d < 38.0:
                # Keyhole slot
                if abs(cx) < 4 and cy > -12 and cy < 16:
                    color_map[y, x] = [15, 12, 10, 255]
                    h_map[y, x] = 0.1
                elif np.sqrt(cx * cx + (cy + 10) * (cy + 10)) < 7.0:
                    color_map[y, x] = [15, 12, 10, 255]
                    h_map[y, x] = 0.1
                else:
                    # Gilded brass plate
                    plate_bevel = np.clip((38.0 - d) / 3.0, 0.0, 1.0)
                    h_map[y, x] = 0.85 + plate_bevel * 0.15
                    color_map[y, x] = [int(225 * plate_bevel), int(185 * plate_bevel), int(60 * plate_bevel), 255]

    diffuse_img = Image.fromarray(color_map, "RGBA")
    diffuse_img.save(OUT_DIR / "dungeon_chest.png")

    normal_arr = height_to_normal(h_map, strength=4.0)
    normal_img = Image.fromarray(normal_arr, "RGBA")
    normal_img.save(OUT_DIR / "dungeon_chest_normal.png")
    print("[Textures] Generated dungeon_chest.png and dungeon_chest_normal.png")


if __name__ == "__main__":
    generate_flagstone_floor(512)
    generate_ashlar_walls(512)
    generate_chest_texture(512)
    print("[Textures] All dungeon textures generated successfully in assets/textures/")
