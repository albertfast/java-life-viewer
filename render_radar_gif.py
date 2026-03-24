from math import cos, sin, pi
from pathlib import Path
from random import Random
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter


BASE_WIDTH = 430
BASE_HEIGHT = 430
RENDER_SCALE = 3
WIDTH = BASE_WIDTH * RENDER_SCALE
HEIGHT = BASE_HEIGHT * RENDER_SCALE
FPS = 15  # Reduced from 20 for smaller file size
SECONDS = 6
FRAME_COUNT = FPS * SECONDS
TAU = pi * 2
GIF_COLORS = 220  # Reduced from 256 for better compression
PALETTE_SAMPLE_LIMIT = 40

BG_TOP = (3, 13, 34)
BG_BOTTOM = (2, 8, 22)
SPHERE_FILL = (8, 34, 58)
SPHERE_GLOW = (25, 110, 170)
CYAN = (52, 188, 255)
TEAL = (83, 228, 223)
WHITE = (205, 248, 255)
RED = (255, 96, 96)
RED_HOT = (255, 126, 78)

CX = WIDTH // 2
CY = HEIGHT // 2 + 4 * RENDER_SCALE
SHELL_R = 108 * RENDER_SCALE
RADAR_RX = 122 * RENDER_SCALE
RADAR_RY = 30 * RENDER_SCALE


def rgba(rgb, alpha):
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def ellipse_bbox(cx, cy, rx, ry):
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def build_particles():
    rng = Random(21)
    items = []
    for _ in range(34):
        items.append(
            {
                "orbit": rng.random() * TAU,
                "radius": 0.16 + rng.random() * 0.8,
                "speed": 0.45 + rng.random() * 0.45,
                "size": 0.7 + rng.random() * 1.1,
                "phase": rng.random() * TAU,
                "threat": rng.random(),
            }
        )
    return items


PARTICLES = build_particles()


def base_frame():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    gd = ImageDraw.Draw(image)

    # Vertical gradient close to the immersive radar panel look.
    for y in range(HEIGHT):
        mix = y / max(1, HEIGHT - 1)
        gd.line((0, y, WIDTH, y), fill=lerp_color(BG_TOP, BG_BOTTOM, mix))

    panel_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pgd = ImageDraw.Draw(panel_glow)
    pgd.ellipse((WIDTH * 0.62, -HEIGHT * 0.12, WIDTH * 1.08, HEIGHT * 0.34), fill=rgba((44, 202, 204), 36))
    pgd.ellipse((WIDTH * 0.08, HEIGHT * 0.18, WIDTH * 0.74, HEIGHT * 0.86), fill=rgba((18, 116, 184), 30))
    panel_glow = panel_glow.filter(ImageFilter.GaussianBlur(34 * RENDER_SCALE // 2))
    image = Image.alpha_composite(image, panel_glow)

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sgd = ImageDraw.Draw(glow)
    sgd.ellipse((70 * RENDER_SCALE, 70 * RENDER_SCALE, 340 * RENDER_SCALE, 340 * RENDER_SCALE), fill=rgba(SPHERE_GLOW, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(48 * RENDER_SCALE // 2))
    return Image.alpha_composite(image, glow)


def draw_sphere(image):
    shell = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shell)
    d.ellipse(ellipse_bbox(CX, CY, SHELL_R, SHELL_R), fill=rgba(SPHERE_FILL, 118))
    d.ellipse(ellipse_bbox(CX, CY, SHELL_R, SHELL_R), outline=rgba((110, 210, 255), 18), width=max(1, RENDER_SCALE))
    shell = shell.filter(ImageFilter.GaussianBlur(max(1, RENDER_SCALE)))
    return Image.alpha_composite(image, shell)


def draw_radar(image, t):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    d.ellipse(ellipse_bbox(CX, CY, RADAR_RX, RADAR_RY), fill=rgba((6, 18, 34), 136))
    d.ellipse(ellipse_bbox(CX, CY, RADAR_RX * 1.01, RADAR_RY * 1.18), fill=rgba((12, 40, 68), 34))

    for i in range(5):
        rx = RADAR_RX * (0.18 + i * 0.18)
        ry = RADAR_RY * (0.18 + i * 0.18)
        color = TEAL if i % 2 == 0 else CYAN
        alpha = 60 - i * 8
        d.ellipse(ellipse_bbox(CX, CY, rx, ry), outline=rgba(color, alpha), width=max(1, RENDER_SCALE))

    for i in range(3):
        orbit = Image.new("RGBA", image.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(orbit)
        rx = RADAR_RX * (0.34 + i * 0.16)
        ry = RADAR_RY * (0.42 + i * 0.16)
        od.ellipse(ellipse_bbox(CX, CY, rx, ry), outline=rgba(CYAN if i == 1 else TEAL, 40 - i * 6), width=max(1, RENDER_SCALE))
        orbit = orbit.rotate(
            sin(t * (0.7 + i * 0.16)) * (7 + i * 3),
            center=(CX, CY),
            resample=Image.Resampling.BICUBIC,
        )
        layer = Image.alpha_composite(layer, orbit)

    sweep = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sweep)
    sweep_angle = t
    arc = 0.48
    points = [(CX, CY)]
    for i in range(28):
        a = sweep_angle - arc / 2 + arc * i / 27
        points.append((CX + cos(a) * RADAR_RX * 0.96, CY + sin(a) * RADAR_RY * 0.96))
    sd.polygon(points, fill=rgba(TEAL, 90))
    tip = (CX + cos(sweep_angle) * RADAR_RX * 0.96, CY + sin(sweep_angle) * RADAR_RY * 0.96)
    sd.line((CX, CY, tip[0], tip[1]), fill=rgba(WHITE, 180), width=max(2, RENDER_SCALE * 2))
    sweep = sweep.filter(ImageFilter.GaussianBlur(4 * RENDER_SCALE // 2))
    layer = Image.alpha_composite(layer, sweep)

    particles = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(particles)
    for p in PARTICLES:
        a = p["orbit"] + t * p["speed"]
        x = CX + cos(a) * RADAR_RX * p["radius"] * 0.82
        y = CY + sin(a) * RADAR_RY * p["radius"] * 0.82 + sin(t * 2 + p["phase"]) * 0.8
        size = (p["size"] + (0.5 + 0.5 * sin(t * 2 + p["phase"])) * 0.3) * RENDER_SCALE
        threat_mix = 0.36 if p["threat"] > 0.72 else 0.0
        particle_color = lerp_color(TEAL, RED, threat_mix)
        alpha = 138 if p["radius"] < 0.5 else 96
        if p["threat"] > 0.86:
            particle_color = lerp_color(particle_color, RED_HOT, 0.42)
            alpha += 20
        pd.ellipse(ellipse_bbox(x, y, size, size), fill=rgba(particle_color, alpha))
    particles = particles.filter(ImageFilter.GaussianBlur(max(1, RENDER_SCALE // 2)))
    layer = Image.alpha_composite(layer, particles)

    center = Image.new("RGBA", image.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(center)
    cd.ellipse(
        ellipse_bbox(CX, CY, 12 * RENDER_SCALE // 2, 12 * RENDER_SCALE // 2),
        fill=rgba(TEAL, 24),
    )
    cd.ellipse(
        ellipse_bbox(CX, CY, 4 * RENDER_SCALE // 2, 4 * RENDER_SCALE // 2),
        fill=rgba(WHITE, 220),
    )
    center = center.filter(ImageFilter.GaussianBlur(max(1, RENDER_SCALE)))
    layer = Image.alpha_composite(layer, center)

    return Image.alpha_composite(image, layer)


def render_frame(progress):
    t = progress * TAU
    frame = base_frame()
    frame = draw_sphere(frame)
    frame = draw_radar(frame, t)
    return frame


def build_global_palette(frames):
    if not frames:
        raise ValueError("Cannot build palette from empty frame list")

    sample_step = max(1, len(frames) // PALETTE_SAMPLE_LIMIT)
    sampled = frames[::sample_step]
    strip = Image.new("RGB", (WIDTH * len(sampled), HEIGHT), (0, 0, 0))
    for idx, frame in enumerate(sampled):
        strip.paste(frame.convert("RGB"), (idx * WIDTH, 0))

    return strip.quantize(
        colors=GIF_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )


def save_frames(frames, frames_dir):
    for idx, frame in enumerate(frames):
        frame.convert("RGB").save(frames_dir / f"frame_{idx:04d}.png", format="PNG", optimize=True)


def run_ffmpeg_encode(frames_dir, output_path, codec_args):
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None:
        raise RuntimeError("ffmpeg is required to produce MP4/WEBM but was not found in PATH")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        *codec_args,
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def main():
    frames = []
    for i in range(FRAME_COUNT):
        frame = render_frame(i / FRAME_COUNT)
        frames.append(frame)

    global_palette = build_global_palette(frames)
    gif_frames = [
        frame.convert("RGB").quantize(palette=global_palette, dither=Image.Dither.FLOYDSTEINBERG)
        for frame in frames
    ]

    output = Path("/data/projects/java-life-viewer/radar_loop.gif")
    gif_frames[0].save(
        output,
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,  # Enable optimization for compression
        disposal=2,  # Use disposal method 2 for efficient frame replacement
    )

    with tempfile.TemporaryDirectory(prefix="radar_frames_") as tmpdir:
        frames_dir = Path(tmpdir)
        save_frames(frames, frames_dir)

        mp4_output = Path("/data/projects/java-life-viewer/radar_loop.mp4")
        run_ffmpeg_encode(
            frames_dir,
            mp4_output,
            [
                "-c:v",
                "libx264",
                "-preset",
                "veryslow",
                "-crf",
                "14",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
            ],
        )

        webm_output = Path("/data/projects/java-life-viewer/radar_loop.webm")
        run_ffmpeg_encode(
            frames_dir,
            webm_output,
            [
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                "18",
                "-deadline",
                "best",
                "-cpu-used",
                "0",
                "-row-mt",
                "1",
                "-pix_fmt",
                "yuv420p",
            ],
        )

    print(output)
    print(mp4_output)
    print(webm_output)


if __name__ == "__main__":
    main()
