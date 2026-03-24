from math import cos, pi, sin
from pathlib import Path
from random import Random
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter


FPS = 24
SECONDS = 6
FRAME_COUNT = FPS * SECONDS
TAU = pi * 2
GIF_COLORS = 256

OUTPUT_DIR = Path("/data/projects/java-life-viewer")


def rgba(rgb, alpha):
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def build_palette(frames, width, height):
    sample_step = max(1, len(frames) // 32)
    sampled = frames[::sample_step]
    strip = Image.new("RGB", (width * len(sampled), height), (0, 0, 0))
    for i, frame in enumerate(sampled):
        strip.paste(frame.convert("RGB"), (i * width, 0))
    return strip.quantize(
        colors=GIF_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )


def write_gif_mp4_webm(base_name, frames, width, height):
    gif_palette = build_palette(frames, width, height)
    gif_frames = [
        frame.convert("RGB").quantize(palette=gif_palette, dither=Image.Dither.FLOYDSTEINBERG)
        for frame in frames
    ]

    gif_path = OUTPUT_DIR / f"{base_name}.gif"
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=False,
        disposal=2,
    )

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None:
        raise RuntimeError("ffmpeg not found in PATH")

    with tempfile.TemporaryDirectory(prefix=f"{base_name}_") as tmp:
        tmp_dir = Path(tmp)
        for idx, frame in enumerate(frames):
            frame.convert("RGB").save(tmp_dir / f"frame_{idx:04d}.png", format="PNG", optimize=True)

        mp4_path = OUTPUT_DIR / f"{base_name}.mp4"
        mp4_cmd = [
            ffmpeg_bin,
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(tmp_dir / "frame_%04d.png"),
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
            str(mp4_path),
        ]
        subprocess.run(mp4_cmd, check=True)

        webm_path = OUTPUT_DIR / f"{base_name}.webm"
        webm_cmd = [
            ffmpeg_bin,
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(tmp_dir / "frame_%04d.png"),
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
            str(webm_path),
        ]
        subprocess.run(webm_cmd, check=True)

    return gif_path, mp4_path, webm_path


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def create_radar_panel_frames(width=1080, height=720):
    cx = width // 2
    cy = int(height * 0.58)
    core_r = int(height * 0.26)

    rng = Random(202)
    particles = []
    for _ in range(88):
        particles.append(
            {
                "orbit": rng.random() * TAU,
                "radius": 0.14 + rng.random() * 0.90,
                "speed": 0.24 + rng.random() * 0.66,
                "size": 1.0 + rng.random() * 2.6,
                "phase": rng.random() * TAU,
                "danger": rng.random(),
            }
        )

    frames = []
    panel_mask = rounded_mask((width, height), radius=38)

    for i in range(FRAME_COUNT):
        p = i / FRAME_COUNT
        t = p * TAU

        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bg)
        for y in range(height):
            mix = y / max(1, height - 1)
            bd.line((0, y, width, y), fill=lerp_color((4, 10, 16), (8, 7, 12), mix))

        # Holographic corner washes in amber and cyan to differentiate from previous style.
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((-220, -120, width * 0.55, height * 0.65), fill=rgba((0, 170, 190), 56))
        gd.ellipse((width * 0.44, height * 0.34, width * 1.16, height * 1.14), fill=rgba((255, 140, 56), 48))
        glow = glow.filter(ImageFilter.GaussianBlur(52))
        bg = Image.alpha_composite(bg, glow)

        grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        g2d = ImageDraw.Draw(grid)
        horizon = int(height * 0.63)
        for gx in range(-width // 2, width + width // 2, 36):
            lean = int((gx - cx) * 0.16)
            g2d.line((gx, height, cx + lean, horizon), fill=rgba((58, 212, 205), 26), width=1)
        for gy in range(horizon, height, 24):
            spread = int((gy - horizon) * 1.6)
            g2d.line((cx - spread, gy, cx + spread, gy), fill=rgba((62, 198, 232), 24), width=1)
        grid = grid.filter(ImageFilter.GaussianBlur(0.4))
        bg = Image.alpha_composite(bg, grid)

        radar = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rd = ImageDraw.Draw(radar)
        rd.ellipse((cx - core_r * 1.16, cy - core_r * 1.16, cx + core_r * 1.16, cy + core_r * 1.16), fill=rgba((8, 18, 28), 160))
        rd.ellipse((cx - core_r * 0.98, cy - core_r * 0.98, cx + core_r * 0.98, cy + core_r * 0.98), fill=rgba((2, 10, 18), 182))

        for ring_i in range(7):
            ratio = 0.18 + ring_i * 0.12
            r = core_r * ratio
            color = (245, 172, 62) if ring_i % 2 == 0 else (62, 214, 226)
            rd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(color, 80 - ring_i * 8), width=2)

        # Rotating hex contour gives a technical visual language unlike previous ellipse-heavy look.
        contour = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cd = ImageDraw.Draw(contour)
        for layer in range(3):
            angle_off = t * (0.4 + layer * 0.22) + layer * 0.8
            rad = core_r * (0.52 + layer * 0.18)
            pts = []
            for k in range(6):
                a = angle_off + (TAU * k / 6)
                pts.append((cx + cos(a) * rad, cy + sin(a) * rad))
            pts.append(pts[0])
            cd.line(pts, fill=rgba((90, 220, 220), 66 - layer * 14), width=2)
        contour = contour.filter(ImageFilter.GaussianBlur(0.6))
        radar = Image.alpha_composite(radar, contour)

        sweep = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sweep)
        sweep_arc = 0.32
        points = [(cx, cy)]
        for seg in range(48):
            a = t * 1.35 - sweep_arc / 2 + sweep_arc * seg / 47
            points.append((cx + cos(a) * core_r * 0.95, cy + sin(a) * core_r * 0.95))
        sd.polygon(points, fill=rgba((255, 186, 88), 116))
        tip = (cx + cos(t * 1.35) * core_r * 0.95, cy + sin(t * 1.35) * core_r * 0.95)
        sd.line((cx, cy, tip[0], tip[1]), fill=rgba((255, 242, 188), 192), width=3)
        sweep = sweep.filter(ImageFilter.GaussianBlur(4))
        radar = Image.alpha_composite(radar, sweep)

        field = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        fd = ImageDraw.Draw(field)
        for pitem in particles:
            a = pitem["orbit"] + t * pitem["speed"]
            x = cx + cos(a) * core_r * pitem["radius"] * 0.88
            y = cy + sin(a) * core_r * pitem["radius"] * 0.88 + sin(t * 1.5 + pitem["phase"]) * 5
            size = pitem["size"] + (0.5 + 0.5 * sin(t * 2.4 + pitem["phase"])) * 1.0
            base_col = (68, 222, 220)
            if pitem["danger"] > 0.72:
                base_col = lerp_color((255, 82, 82), (255, 156, 92), min(1.0, pitem["danger"]))
            fd.ellipse((x - size, y - size, x + size, y + size), fill=rgba(base_col, 150))
        field = field.filter(ImageFilter.GaussianBlur(0.8))
        radar = Image.alpha_composite(radar, field)

        core = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cod = ImageDraw.Draw(core)
        pulse = 0.5 + 0.5 * sin(t * 2.8)
        cod.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=rgba((255, 182, 92), int(46 + pulse * 40)))
        cod.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=rgba((255, 248, 224), 220))
        core = core.filter(ImageFilter.GaussianBlur(1.6))
        radar = Image.alpha_composite(radar, core)

        combined = Image.alpha_composite(bg, radar)
        clipped = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        clipped.paste(combined, (0, 0), panel_mask)
        frames.append(clipped)

    return frames


def create_premium_panel_frames(width=1080, height=1920):
    panel_mask = rounded_mask((width, height), radius=48)
    frames = []

    for i in range(FRAME_COUNT):
        p = i / FRAME_COUNT
        t = p * TAU

        base = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        bd = ImageDraw.Draw(base)
        for y in range(height):
            mix = y / max(1, height - 1)
            bd.line((0, y, width, y), fill=lerp_color((8, 8, 14), (14, 12, 18), mix))

        # Kinetic diagonal ribbons for a distinct premium identity.
        ribbons = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ribbons)
        drift = int((0.5 + 0.5 * sin(t * 1.1)) * 280)
        rd.polygon(
            [
                (-220 + drift, 240),
                (520 + drift, 90),
                (740 + drift, 520),
                (20 + drift, 700),
            ],
            fill=rgba((255, 58, 98), 96),
        )
        rd.polygon(
            [
                (width - 180 - drift, 380),
                (width + 260 - drift, 260),
                (width + 200 - drift, 920),
                (width - 320 - drift, 840),
            ],
            fill=rgba((255, 168, 74), 82),
        )
        ribbons = ribbons.filter(ImageFilter.GaussianBlur(26))
        base = Image.alpha_composite(base, ribbons)

        noise = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        nd = ImageDraw.Draw(noise)
        for row in range(0, height, 10):
            flicker = int(7 + 5 * (0.5 + 0.5 * sin(t * 2.8 + row * 0.03)))
            nd.line((0, row, width, row), fill=rgba((28, 28, 36), flicker), width=1)
        base = Image.alpha_composite(base, noise)

        # Premium card now sits slightly tilted and alive.
        card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        card_box = (64, int(height * 0.55), width - 64, int(height * 0.90))
        glow_alpha = int(82 + 34 * (0.5 + 0.5 * sin(t * 1.9)))
        cd.rounded_rectangle(card_box, radius=58, fill=rgba((20, 22, 30), 224), outline=rgba((255, 142, 86), glow_alpha), width=2)

        badge_box = (card_box[0] + 42, card_box[1] + 42, card_box[0] + 320, card_box[1] + 94)
        cd.rounded_rectangle(badge_box, radius=18, fill=rgba((255, 68, 90), 230))

        # CTA redesigned with gradient-like split and orbiting glow dots.
        btn_box = (112, int(height * 0.73), width - 112, int(height * 0.805))
        cd.rounded_rectangle(btn_box, radius=34, fill=rgba((255, 248, 238), 255))
        cd.rounded_rectangle((btn_box[0] + 4, btn_box[1] + 4, (btn_box[0] + btn_box[2]) // 2, btn_box[3] - 4), radius=30, fill=rgba((255, 78, 102), 255))
        cd.rounded_rectangle(((btn_box[0] + btn_box[2]) // 2, btn_box[1] + 4, btn_box[2] - 4, btn_box[3] - 4), radius=30, fill=rgba((255, 160, 78), 255))

        orbit = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(orbit)
        bx = (btn_box[0] + btn_box[2]) // 2
        by = (btn_box[1] + btn_box[3]) // 2
        for k in range(10):
            a = t * 1.8 + (TAU * k / 10)
            r = 170 + 12 * sin(t * 2.2 + k)
            x = bx + cos(a) * r
            y = by + sin(a) * (r * 0.28)
            dot_col = (255, 92, 98) if k % 3 == 0 else (82, 230, 226)
            od.ellipse((x - 3, y - 3, x + 3, y + 3), fill=rgba(dot_col, 156))
        orbit = orbit.filter(ImageFilter.GaussianBlur(0.9))
        card = Image.alpha_composite(card, orbit)

        # Slider indicator with bigger motion to avoid previous subtle behavior.
        dots_y = int(height * 0.50)
        active_idx = (i // 12) % 3
        for di in range(3):
            cx = int(width * 0.47) + di * 46
            active = active_idx == di
            w = 30 if active else 12
            h = 12
            fill = (252, 224, 98) if active else (44, 58, 74)
            cd.rounded_rectangle((cx - w // 2, dots_y - h // 2, cx + w // 2, dots_y + h // 2), radius=6, fill=rgba(fill, 255))

        card = card.filter(ImageFilter.GaussianBlur(0.25))
        base = Image.alpha_composite(base, card)

        clipped = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        clipped.paste(base, (0, 0), panel_mask)
        frames.append(clipped)

    return frames


def main():
    radar_frames = create_radar_panel_frames()
    premium_frames = create_premium_panel_frames()

    outputs = []
    outputs.extend(write_gif_mp4_webm("driving_mode_radar_panel", radar_frames, 1080, 720))
    outputs.extend(write_gif_mp4_webm("premium_access_panel", premium_frames, 1080, 1920))

    for out in outputs:
        print(out)


if __name__ == "__main__":
    main()
