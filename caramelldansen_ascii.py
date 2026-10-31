
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

try:
    import pygame
except ImportError:
    sys.exit("нету пайгейма")

DEFAULT_BPM = 165.0
COLS, ROWS = 108, 39
FPS = 30
BG = (11, 9, 25)
DIM = (71, 65, 108)
WHITE = (237, 222, 255)
PINK = (255, 109, 182)
VIOLET = (178, 130, 255)
CYAN = (111, 230, 248)
GOLD = (255, 218, 127)
SKIN = (255, 200, 174)

#графа
EARS, OUT, SWING, PAWS, WAVE, UP, CROSS = range(7)
MOVE_NAMES = ["EARS", "ARMS OUT", "ARM SWING", "PAWS", "WAVE", "HANDS UP", "CROSS"]
BEATS_PER_MOVE = 4
SEQUENCE = [EARS, EARS, OUT, SWING, EARS, PAWS, WAVE, EARS,
            UP, SWING, EARS, CROSS, OUT, WAVE, PAWS, UP]


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, value):
    t = clamp((value - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Art:
    def __init__(self):
        self.cells = {}

    def put(self, x, y, ch, color=WHITE):
        x, y = round(x), round(y)
        if 0 <= x < COLS and 0 <= y < ROWS and ch != " ":
            self.cells[(x, y)] = (ch, color)

    def text(self, x, y, message, color=WHITE):
        for i, ch in enumerate(message):
            self.put(x + i, y, ch, color)

    def line(self, x0, y0, x1, y1, color, char=None):
        dx, dy = x1 - x0, y1 - y0
        steps = max(1, round(max(abs(dx) * 1.8, abs(dy) * 1.4)))
        if char is None:
            if abs(dx) > abs(dy) * 1.7:
                char = "-"
            elif dx * dy > 0:
                char = "\\"
            elif dx * dy < 0:
                char = "/"
            else:
                char = "|"
        for i in range(steps + 1):
            t = i / steps
            self.put(lerp(x0, x1, t), lerp(y0, y1, t), char, color)


def arm_pose(move, t, side):
    s = math.sin(math.pi * t)
    c = math.cos(math.pi * t)
    fast = math.sin(2 * math.pi * t)
    bounce = abs(s)

    if move == EARS:
        return (side * (11.8 + 0.6 * math.sin(2 * math.pi * t)),
                14.0 + 0.9 * s * side,
                side * (7.0 + 0.8 * s),
                6.2 - 0.9 * math.sin(math.pi * t + (0 if side > 0 else math.pi)) )
    if move == OUT:
        return (side * 11.0, 17.0,
                side * 20.0, 14.0 + 2.0 * fast * side * 0.9 + 0.6 * s)
    if move == SWING:
        k = 0.5 + 0.5 * c
        k = smoothstep(0, 1, k)
        return (lerp(side * 7.0, side * 11.8, k), lerp(22.0, 14.0, k),
                lerp(side * 9.0, side * 7.0, k), lerp(29.0, 6.2, k))
    if move == PAWS:
        return (side * 8.0, 19.0 + 0.6 * bounce,
                side * 3.0, 13.5 - 1.8 * abs(fast))
    if move == WAVE:
        u = smoothstep(-0.8, 0.8, side * s)
        return (lerp(side * 11.0, side * 10.0, u), lerp(18.0, 9.0, u),
                lerp(side * 18.5, side * 9.0, u), lerp(21.0, 2.0, u))
    if move == UP:
        return (side * 9.0, 10.0,
                side * (5.5 + 1.2 * s * side), 2.4 + 1.0 * bounce)
    cross = 0.5 + 0.5 * math.sin(math.pi * t * 2)
    return (side * 6.0, 20.0,
            lerp(side * 6.0, -side * 3.0, cross), 17.0 - 1.0 * bounce)


def dancer(art, anchor_x, music_sec, bpm, shift, palette, energy, alternate=False):
    beat = max(0, music_sec - shift) * bpm / 60
    phase = beat * math.pi
    direction = -1 if alternate else 1
    groove = math.sin(phase + (0.12 if alternate else 0))
    bounce = abs(math.sin(phase))
    accent = math.sin(phase * 2)
    amp = 0.9 + 0.35 * energy
    step_idx = int(beat // BEATS_PER_MOVE)
    move = SEQUENCE[step_idx % len(SEQUENCE)]
    prev_move = SEQUENCE[(step_idx - 1) % len(SEQUENCE)]
    blend = smoothstep(0.0, 0.6, beat - step_idx * BEATS_PER_MOVE) if step_idx > 0 else 1.0
    jump = bounce * 1.4 if move in (UP, SWING) else 0.0
    head_tilt = 1.0 if move == WAVE else 0.4
    hips_swing = 2.4 if move in (EARS, OUT, PAWS) else 1.6
    hips_x = anchor_x + direction * (hips_swing * amp * groove)
    chest_x = anchor_x + direction * (1.2 * amp * groove)
    head_x = chest_x + head_tilt * direction * groove
    head_y = 10.8 - 0.80 * bounce * amp - jump * 0.6 + 0.18 * math.sin(phase * 2)
    shoulder_y = 19.0 - 0.35 * bounce - jump * 0.6
    hip_y = 26.0 - 0.30 * bounce - jump * 0.5
    feet_y = 34.0
    hair_color, shirt_color = palette

    for side in (-1, 1):
        for row in range(8, 21):
            wind = math.sin(phase - row * 0.35) * (row - 8) * 0.07
            xx = head_x + side * (7.0 + 0.11 * (row - 9)) + wind
            art.put(xx, row + head_y - 11, "@" if row % 3 == 0 else ":", hair_color)
            if row > 12:
                art.put(xx + side * 1.1, row + head_y - 11, ".", hair_color)

    for side in (-1, 1):
        hip = (hips_x + side * 2.2, hip_y + 2)
        step = direction * groove * 1.35 * side
        heel_lift = max(0, side * groove) * 1.7 * amp + jump * 1.2
        knee = (hips_x + side * (3.0 + 0.6 * bounce) + step * 0.4, 30.5 - heel_lift * 0.4)
        foot = (hips_x + side * 4.2 + step, feet_y - heel_lift)
        art.line(*hip, *knee, SKIN)
        art.line(*knee, *foot, SKIN)
        art.line(foot[0] - 1.3, foot[1], foot[0] + 1.5, foot[1], shirt_color, "=")

    for side in (-1, 1):
        cur = arm_pose(move, beat, side)
        old = arm_pose(prev_move, beat, side)
        ex, ey, hx, hy = (lerp(o, c, blend) for o, c in zip(old, cur))
        shoulder = (chest_x + side * 4.5, shoulder_y)
        elbow = (chest_x + ex, ey - jump * 0.6)
        hand = (chest_x + hx, hy - jump * 0.6)
        art.line(*shoulder, *elbow, SKIN)
        art.line(*elbow, *hand, SKIN)
        art.put(*elbow, "o", SKIN)
        art.put(*hand, "O", SKIN)
        art.line(hand[0], hand[1] - 0.4, hand[0] - side * (1.1 + 0.3 * accent), hand[1] - 2.2, SKIN)
        art.line(hand[0], hand[1] - 0.2, hand[0] + side * 1.1, hand[1] - 2.0, SKIN)

    art.line(head_x, head_y + 4.0, chest_x, shoulder_y - 0.5, SKIN)
    for y in range(round(shoulder_y), round(hip_y) + 1):
        t = clamp((y - shoulder_y) / (hip_y - shoulder_y), 0, 1)
        center = lerp(chest_x, hips_x, t)
        width = lerp(4.5, 3.3, t)
        for x in range(round(center - width), round(center + width) + 1):
            if abs(x - center) <= width:
                art.put(x, y, ":" if (x + y) % 3 else "*", shirt_color)
    art.text(chest_x - 1, shoulder_y + 1 - bounce * 0.25, "\\V/", WHITE)
    art.text(hips_x - 1, hip_y - 2 - bounce * 0.25, "<+>", WHITE)
    for y in range(round(hip_y), round(hip_y + 4)):
        spread = 4.1 + (y - hip_y) * 1.1
        for x in range(round(hips_x - spread), round(hips_x + spread) + 1):
            ch = "=" if y >= hip_y + 3 else ("%" if (x + y) % 4 else "*")
            art.put(x, y, ch, shirt_color)

    for dy in range(-5, 4):
        for dx in range(-8, 9):
            ell = (dx / 7.6) ** 2 + (dy / 4.8) ** 2
            if ell <= 1:
                if dy < -2 or abs(dx) > 5:
                    art.put(head_x + dx, head_y + dy, "%" if (dx + dy) % 4 else "@", hair_color)
                else:
                    art.put(head_x + dx, head_y + dy, ".", SKIN)

    art.text(head_x - 4, head_y - 3, "~^^~~^^~", hair_color)
    blink = (int(music_sec * 3.5) % 29 == 0)
    art.text(head_x - 3, head_y - 0.1, "-" if blink else "^", WHITE)
    art.text(head_x + 3, head_y - 0.1, "-" if blink else "^", WHITE)
    art.put(head_x - 5, head_y + 1, "*", PINK)
    art.put(head_x + 5, head_y + 1, "*", PINK)
    art.put(head_x, head_y + 2, "w" if step_idx % 2 == 0 else "o", WHITE)
    for side in (-1, 1):
        art.put(head_x + side * 6.5, head_y - 2, "~", hair_color)


def get_audio_envelope(music_file):
    try:
        sample = pygame.mixer.Sound(str(music_file))
        length = sample.get_length()
        raw = sample.get_raw()
        channels = pygame.mixer.get_init()[2]
        sample_rate = pygame.mixer.get_init()[0]
        pcm = memoryview(raw).cast("h")
        hop = max(1, int(sample_rate * 0.05))
        envelope = []
        for start in range(0, len(pcm) // channels, hop):
            end = min(len(pcm) // channels, start + hop)
            total, count = 0, 0
            for i in range(start, end, 12):
                total += abs(pcm[i * channels])
                count += 1
            envelope.append(total / max(1, count))
        maximum = max(envelope, default=1) or 1
        return length, [clamp(v / maximum * 1.9, 0.0, 1.0) for v in envelope]
    except Exception:
        return 0.0, []


def background(art, seconds, beat, energy, length, palette):
    art.text(30, 0, "*  C A R A M E L L D A N S E N  *", GOLD)
    art.text(5, 5, "+" + "-" * 97 + "+", DIM)
    art.text(5, 36, "+" + "-" * 97 + "+", DIM)

    for idx in range(40):
        x = 7 + idx * 2.35
        h = 0.5 + 4.2 * abs(math.sin(idx * 0.31 - seconds * 3.5)) * (0.3 + energy)
        for j in range(round(h)):
            art.put(x, 35 - j, "|" if j < 2 else ":", CYAN if idx % 2 else PINK)

    randomizer = random.Random(2026)
    for _ in range(75):
        x = randomizer.randrange(7, 102)
        y = randomizer.randrange(6, 34)
        if (15 < x < 45 or 64 < x < 95) and y > 8:
            continue
        drift = round(math.sin(seconds * 0.6 + x) * 1.0)
        blink = math.sin(seconds * 3.4 + x * 0.7 + y) > 0.65
        if blink:
            art.put(x + drift, y, "+" if x % 2 else ".", DIM)

    art.text(16, 6, ". * .", palette[0])
    art.text(74, 6, ". * .", palette[1])

    if length > 0:
        progress = clamp(seconds / length, 0, 1)
        n = round(progress * 51)
        label = f"{int(seconds // 60):02}:{int(seconds % 60):02} / {int(length // 60):02}:{int(length % 60):02}"
        art.text(23, 37, "[" + "=" * n + ">" + "-" * (51 - n) + "] " + label, GOLD)
    else:
        art.text(44, 37, f"{int(seconds // 60):02}:{int(seconds % 60):02}", GOLD)


def main():
    parser = argparse.ArgumentParser(description="карамельки")
    parser.add_argument("music", nargs="?", default="caramelldansen.mp3", help="MP3/OGG/WAV file")
    parser.add_argument("--bpm", type=float, default=DEFAULT_BPM, help="165 speedy remix; 138 original")
    parser.add_argument("--offset", type=float, default=0.0, help="Beat offset in seconds (+ means move starts later)")
    args = parser.parse_args()
    if args.bpm <= 0:
        parser.error("--bpm must be positive")
    music_file = Path(args.music).expanduser().resolve()
    if not music_file.is_file():
        sys.exit(f"не найдена музыка")

    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.init()
    if not pygame.mixer.get_init():
        sys.exit("нетьу звука")
    try:
        pygame.mixer.music.load(str(music_file))
    except pygame.error as error:
        sys.exit(f"не удалось открыть музыку: {error}")

    length, envelope = get_audio_envelope(music_file)
    font = pygame.font.SysFont("consolas,couriernew,dejavusansmono,liberationmono", 16, bold=True)
    cell_w = max(9, font.size("M")[0])
    cell_h = font.get_linesize()
    width, height = COLS * cell_w + 50, ROWS * cell_h + 35
    display = pygame.display.set_mode((width, height))
    pygame.display.set_caption("карамельки")
    clock = pygame.time.Clock()
    glyph_cache = {}
    bpm = args.bpm
    offset = args.offset
    paused = False
    last_seconds = 0.0

    def draw_glyph(char, color, x, y):
        key = (char, color)
        if key not in glyph_cache:
            glyph_cache[key] = font.render(char, True, color)
        display.blit(glyph_cache[key], (25 + x * cell_w, 12 + y * cell_h))

    try:
        pygame.mixer.music.play()
        started = True
        while started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    started = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        started = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                        (pygame.mixer.music.pause if paused else pygame.mixer.music.unpause)()
                    elif event.key == pygame.K_r:
                        pygame.mixer.music.play()
                        paused = False
                        last_seconds = 0.0
                    elif event.key == pygame.K_UP:
                        bpm += 0.5
                    elif event.key == pygame.K_DOWN:
                        bpm = max(1, bpm - 0.5)
                    elif event.key in (pygame.K_LEFTBRACKET, pygame.K_COMMA):
                        offset -= 0.05
                    elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PERIOD):
                        offset += 0.05

            pos = pygame.mixer.music.get_pos()
            if pos >= 0 and not paused:
                last_seconds = pos / 1000.0
            seconds = last_seconds
            if not paused and not pygame.mixer.music.get_busy():
                started = False
                continue

            i = min(len(envelope) - 1, int(seconds * 20)) if envelope else 0
            energy = envelope[i] if envelope else 0.65
            beat = max(0.0, seconds - offset) * bpm / 60.0
            art = Art()
            background(art, seconds, beat, energy, length, (PINK, VIOLET))
            dancer(art, 32, seconds, bpm, offset, (PINK, VIOLET), energy)
            dancer(art, 76, seconds, bpm, offset, (VIOLET, CYAN), energy, alternate=True)
            move_name = MOVE_NAMES[SEQUENCE[int(beat // BEATS_PER_MOVE) % len(SEQUENCE)]]
            art.text(7, 38, f"BPM:{bpm:5.1f}  OFFSET:{offset:+.2f}s  MOVE:{move_name:<9} SPACE pause  R restart", DIM)
            if paused:
                art.text(46, 4, "* PAUSED *", GOLD)
            display.fill(BG)
            for (x, y), (ch, col) in art.cells.items():
                draw_glyph(ch, col, x, y)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        pygame.mixer.music.stop()
        pygame.quit()


if __name__ == "__main__":
    main()