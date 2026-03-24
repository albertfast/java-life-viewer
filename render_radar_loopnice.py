from math import cos, pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter


WIDTH = 900
HEIGHT = 900
FPS = 18  # Reduced from 24 for smaller file size
SECONDS = 6
FRAME_COUNT = FPS * SECONDS
TAU = pi * 2
GIF_COLORS = 220  # Reduced from 256 for better compression
PALETTE_SAMPLE_LIMIT = 48

# Scene palette
BG_TOP = (4, 10, 24)
BG_BOTTOM = (2, 6, 16)
SHELL_FILL = (10, 40, 74)
SHELL_EDGE = (64, 190, 255)
RADAR_CYAN = (70, 218, 236)
RADAR_BLUE = (64, 170, 255)
RADAR_RED = (255, 92, 92)
RADAR_HOT = (255, 154, 84)
WHITE = (218, 248, 255)

CX = WIDTH // 2
CY = HEIGHT // 2 + 24
SHELL_R = 248
PLANE_RX = 270
PLANE_RY = 102


def rgba(rgb, alpha):
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def ellipse_bbox(cx, cy, rx, ry):
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def build_particles():
    rng = Random(1337)
    particles = []
    for _ in range(96):
        particles.append(
            {
                "orbit": rng.random() * TAU,
                "radius": 0.10 + rng.random() * 0.94,
                "speed": 0.22 + rng.random() * 0.68,
                "phase": rng.random() * TAU,
                "danger": rng.random(),
                "height": -0.24 + rng.random() * 0.74,
                "size": 1.4 + rng.random() * 2.8,
            }
        )
    return particles


PARTICLES = build_particles()


def draw_background():
    base = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    d = ImageDraw.Draw(base)
    for y in range(HEIGHT):
        mix = y / max(1, HEIGHT - 1)
        d.line((0, y, WIDTH, y), fill=lerp_color(BG_TOP, BG_BOTTOM, mix))

    haze = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    hd.ellipse((-200, 80, 640, 820), fill=rgba((18, 118, 180), 34))
    hd.ellipse((420, -140, 1040, 450), fill=rgba((44, 204, 198), 30))
    hd.ellipse((300, 430, 980, 1080), fill=rgba((255, 108, 88), 24))
    haze = haze.filter(ImageFilter.GaussianBlur(62))
    return Image.alpha_composite(base, haze)


def draw_world_shell(image, t):
    shell = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shell)

    d.ellipse(ellipse_bbox(CX, CY, SHELL_R, SHELL_R), fill=rgba(SHELL_FILL, 118))
    d.ellipse(ellipse_bbox(CX, CY, SHELL_R, SHELL_R), outline=rgba(SHELL_EDGE, 42), width=2)

    # Latitude rings for stronger 3D sphere cue.
    latitudes = [-0.68, -0.42, -0.18, 0.12, 0.38, 0.62]
    for idx, lat in enumerate(latitudes):
        y = CY + lat * SHELL_R
        rx = SHELL_R * (1.0 - abs(lat) * 0.52)
        ry = rx * 0.26
        alpha = 24 + idx * 5
        d.ellipse(ellipse_bbox(CX, y, rx, ry), outline=rgba(lerp_color(RADAR_BLUE, RADAR_CYAN, idx / 5.0), alpha), width=2)

    # Rotating meridian arcs.
    for i in range(4):
        ring = Image.new("RGBA", image.size, (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rx = SHELL_R * (0.72 + i * 0.07)
        ry = SHELL_R * 0.96
        rd.ellipse(ellipse_bbox(CX, CY, rx, ry), outline=rgba((95, 206, 255), 18 + i * 4), width=1)
        ring = ring.rotate((t * 45 + i * 31) * (1 if i % 2 == 0 else -1), center=(CX, CY), resample=Image.Resampling.BICUBIC)
        shell = Image.alpha_composite(shell, ring)

    shell = shell.filter(ImageFilter.GaussianBlur(1.2))
    return Image.alpha_composite(image, shell)


def draw_radar_plane(image, t):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Base disk and inner glow.
    d.ellipse(ellipse_bbox(CX, CY, PLANE_RX, PLANE_RY), fill=rgba((6, 18, 36), 184))
    d.ellipse(ellipse_bbox(CX, CY, PLANE_RX * 0.88, PLANE_RY * 0.88), fill=rgba((5, 28, 50), 126))

    for i in range(7):
        ratio = 0.16 + i * 0.12
        rx = PLANE_RX * ratio
        ry = PLANE_RY * ratio
        col = RADAR_CYAN if i % 2 == 0 else RADAR_BLUE
        d.ellipse(ellipse_bbox(CX, CY, rx, ry), outline=rgba(col, 76 - i * 8), width=2)

    # Orbit ribbons with tilt.
    for i in range(4):
        orbit = Image.new("RGBA", image.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(orbit)
        rx = PLANE_RX * (0.34 + i * 0.13)
        ry = PLANE_RY * (0.36 + i * 0.12)
        od.ellipse(ellipse_bbox(CX, CY, rx, ry), outline=rgba(RADAR_CYAN if i != 1 else RADAR_BLUE, 58 - i * 10), width=2)
        orbit = orbit.rotate(sin(t * (0.8 + i * 0.21)) * (9 + i * 4), center=(CX, CY), resample=Image.Resampling.BICUBIC)
        layer = Image.alpha_composite(layer, orbit)

    # Main sweep + secondary echo sweep.
    for sweep_idx in range(2):
        sweep = Image.new("RGBA", image.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sweep)
        angle = t * (1.0 + sweep_idx * 0.22) + sweep_idx * 0.84
        arc = 0.42 - sweep_idx * 0.1
        points = [(CX, CY)]
        for seg in range(40):
            a = angle - arc / 2 + arc * seg / 39
            points.append((CX + cos(a) * PLANE_RX * 0.96, CY + sin(a) * PLANE_RY * 0.96))
        fill = (80, 225, 216) if sweep_idx == 0 else (70, 182, 255)
        sd.polygon(points, fill=rgba(fill, 104 - sweep_idx * 44))
        tip = (CX + cos(angle) * PLANE_RX * 0.96, CY + sin(angle) * PLANE_RY * 0.96)
        sd.line((CX, CY, tip[0], tip[1]), fill=rgba(WHITE, 200 - sweep_idx * 80), width=3)
        sweep = sweep.filter(ImageFilter.GaussianBlur(4 - sweep_idx))
        layer = Image.alpha_composite(layer, sweep)

    # Particle field with pseudo depth (height affects size/alpha/vertical lift).
    pfield = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(pfield)
    for p in PARTICLES:
        a = p["orbit"] + t * p["speed"]
        base_x = CX + cos(a) * PLANE_RX * p["radius"] * 0.88
        base_y = CY + sin(a) * PLANE_RY * p["radius"] * 0.88

        z = p["height"] + sin(t * 1.4 + p["phase"]) * 0.18
        y = base_y - z * 36
        x = base_x + sin(t * 1.2 + p["phase"]) * 1.8

        size = p["size"] * (0.65 + (z + 0.6))
        threat = 0.0
        if p["danger"] > 0.72:
            threat = 0.42
        color = lerp_color(RADAR_CYAN, RADAR_RED, threat)
        if p["danger"] > 0.9:
            color = lerp_color(color, RADAR_HOT, 0.45)

        alpha = int(86 + (z + 0.6) * 110)
        pd.ellipse((x - size, y - size, x + size, y + size), fill=rgba(color, alpha))

    pfield = pfield.filter(ImageFilter.GaussianBlur(0.9))
    layer = Image.alpha_composite(layer, pfield)

    # Bright center and pulse ring.
    core = Image.new("RGBA", image.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    pulse = 0.5 + 0.5 * sin(t * 2.7)
    core_r = 13 + pulse * 5
    cd.ellipse(ellipse_bbox(CX, CY, core_r * 2.1, core_r * 2.1), fill=rgba((92, 226, 236), 32 + pulse * 36))
    cd.ellipse(ellipse_bbox(CX, CY, core_r, core_r), fill=rgba((248, 252, 255), 230))
    core = core.filter(ImageFilter.GaussianBlur(2.0))
    layer = Image.alpha_composite(layer, core)

    return Image.alpha_composite(image, layer)


def render_frame(frame_idx):
    t = (frame_idx / FRAME_COUNT) * TAU
    frame = draw_background()
    frame = draw_world_shell(frame, t)
    frame = draw_radar_plane(frame, t)
    return frame


def build_global_palette(frames):
    sample_step = max(1, len(frames) // PALETTE_SAMPLE_LIMIT)
    sampled = frames[::sample_step]
    strip = Image.new("RGB", (WIDTH * len(sampled), HEIGHT), (0, 0, 0))
    for idx, fr in enumerate(sampled):
        strip.paste(fr.convert("RGB"), (idx * WIDTH, 0))
    return strip.quantize(
        colors=GIF_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )


def main():
    frames = [render_frame(i) for i in range(FRAME_COUNT)]

    palette = build_global_palette(frames)
    gif_frames = [
        fr.convert("RGB").quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        for fr in frames
    ]

    out = Path("/data/projects/java-life-viewer/radar_loopnice.gif")
    gif_frames[0].save(
        out,
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,  # Enable optimization for compression
        disposal=2,  # Use efficient frame disposal
    )
    print(out)


if __name__ == "__main__":
    main()
