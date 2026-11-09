#!/usr/bin/env python3
"""Generate the alarm sounds in res/raw (pure stdlib, so they're ours: no licensing questions).
Priority sounds (short):  p_two_beeps, p_three_beeps, p_chime, p_buzz
Urgent sounds (~2.4 s):   u_siren, u_yelp, u_klaxon, u_bell
Retro console-style effects. All original, made in the style of each console's sound chip, not copies:
  NES style (pulse/triangle/noise):  r_coin, r_jump, r_powerup, n_oneup, n_fireball, n_warp, n_alarm,
                                     n_trk_treasure, n_trk_lunar, n_trk_pogo (late-80s NES platformer music style)
  Genesis style (FM synthesis):      r_ring, s_spin, s_bounce, s_checkpoint, s_chime, s_alarm
  Game Boy style (4-bit, gritty):    g_boot, g_select, g_itemget, g_levelup, g_lowhp
  Monster-catching RPG style (GB):   m_wobble, m_heal, m_evolve, m_encounter, m_cry, m_save, m_bump, m_spotted
  N64 adventure style (reverb):      z_ocarina, z_secret, z_fairy, z_treasure, z_heart
  GameCube life-sim style (cozy):    c_pluck, c_chatter, c_mail, c_bells, c_net, c_clock
  MT-32 style early-90s PC jingles:  t_pirate, t_voodoo, t_fanfare, t_starfighter, t_noir, t_scifi, t_empire, t_colony
  Radio drama style (family audio):  o_whimsy, o_lesson, o_mystery, o_adventure
Run: python3 tools/make_sounds.py"""
import math, struct, wave, os
RATE = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'res', 'raw')

def tone(freq_fn, dur, amp=0.95, harm=(1.0, 0.30, 0.12), decay=None):
    n = int(RATE * dur); out = []; phase = 0.0; fade = int(RATE * 0.006)
    norm = sum(harm)
    for i in range(n):
        t = i / RATE
        phase += 2 * math.pi * freq_fn(t) / RATE
        v = sum(h * math.sin((2 * k + 1) * phase) for k, h in enumerate(harm)) / norm
        env = min(1.0, i / fade, (n - 1 - i) / fade)
        if decay: env *= math.exp(-t / decay)
        out.append(amp * env * v)
    return out

def silence(dur): return [0.0] * int(RATE * dur)

def save(name, samples):
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 32767)) for s in samples))
    print(f'{name}: {len(samples)/RATE:.2f}s')

def square(freq_fn, dur, amp=0.55, duty=0.5, decay=None):
    """Band-limited-ish square/pulse wave (chiptune voice)."""
    n = int(RATE * dur); out = []; phase = 0.0; fade = int(RATE * 0.003)
    for i in range(n):
        t = i / RATE
        phase = (phase + freq_fn(t) / RATE) % 1.0
        v = 1.0 if phase < duty else -1.0
        env = min(1.0, i / fade, (n - 1 - i) / fade)
        if decay: env *= math.exp(-t / decay)
        out.append(amp * env * v)
    return out

def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]

beep = lambda: tone(lambda t: 2000, 0.16)
# --- priority ---
save('p_two_beeps', beep() + silence(0.11) + beep() + silence(0.05))
save('p_three_beeps', beep() + silence(0.09) + beep() + silence(0.09) + beep() + silence(0.05))
save('p_chime', tone(lambda t: 1319, 0.45, harm=(1.0, 0.15), decay=0.25) + tone(lambda t: 988, 0.7, harm=(1.0, 0.15), decay=0.35))
save('p_buzz', tone(lambda t: 220, 0.22, harm=(1.0, 0.6, 0.4, 0.3)) + silence(0.08) + tone(lambda t: 220, 0.22, harm=(1.0, 0.6, 0.4, 0.3)))
# --- urgent ---
save('u_siren', tone(lambda t: 700 + 900 * math.sin(math.pi * ((t % 0.8) / 0.8)), 2.4))          # wail
save('u_yelp', tone(lambda t: 800 + 900 * ((t % 0.2) / 0.2), 2.4))                                  # fast sweep
save('u_klaxon', tone(lambda t: 950 if (t % 0.5) < 0.25 else 700, 2.4, harm=(1.0, 0.5, 0.3)))      # hi-lo
save('u_bell', sum((tone(lambda t: 2400 + 60 * math.sin(2 * math.pi * 25 * t), 0.06) + silence(0.02) for _ in range(30)), []))  # ringing bell
# --- retro (original 8-bit style effects) ---
NOTE = lambda name: {'C6': 1046.5, 'E6': 1318.5, 'G6': 1568.0, 'A5': 880.0, 'D6': 1174.7,
                     'C7': 2093.0, 'E7': 2637.0, 'G7': 3136.0, 'C5': 523.3, 'E5': 659.3, 'G5': 784.0}[name]
# coin: short low pickup blip, then a ringing higher note
save('r_coin', square(lambda t: NOTE('A5'), 0.07, duty=0.5) + square(lambda t: NOTE('D6'), 0.55, duty=0.5, decay=0.22))
# ring sparkle: two bright pulse voices a sixth apart, quick shimmer arpeggio
save('r_ring', mix(square(lambda t: [NOTE('C7'), NOTE('E7'), NOTE('G7')][min(2, int(t / 0.045))], 0.6, amp=0.35, duty=0.25, decay=0.25),
                   silence(0.03) + square(lambda t: NOTE('E7') * 1.003, 0.55, amp=0.25, duty=0.125, decay=0.2)))
# jump: rising pulse sweep
save('r_jump', square(lambda t: 150 * (2000 / 150) ** ((t / 0.26) ** 0.85), 0.26, duty=0.25, decay=0.6))  # 150 Hz -> 2 kHz
# power-up: fast rising arpeggio
arp = [NOTE('C5'), NOTE('E5'), NOTE('G5'), NOTE('C6'), NOTE('E6'), NOTE('G6'), NOTE('C7')]
save('r_powerup', sum((square(lambda t, f=f: f, 0.06, duty=0.5) for f in arp), []) + square(lambda t: NOTE('C7'), 0.25, decay=0.12))

# ===== more console-style effects (original) =====
import random
def triangle(freq_fn, dur, amp=0.6, decay=None):
    n = int(RATE * dur); out = []; ph = 0.0; fade = int(RATE * 0.003)
    for i in range(n):
        t = i / RATE; ph = (ph + freq_fn(t) / RATE) % 1.0
        v = 4 * abs(ph - 0.5) - 1
        v = round(v * 7.5) / 7.5          # NES triangle is a 4-bit staircase
        env = min(1.0, i / fade, (n - 1 - i) / fade)
        if decay: env *= math.exp(-t / decay)
        out.append(amp * env * v)
    return out

def noise(rate_hz, dur, amp=0.4, decay=None, seed=1):
    rnd = random.Random(seed); n = int(RATE * dur); out = []; hold = 0.0; acc = 1.0
    for i in range(n):
        acc += rate_hz / RATE
        if acc >= 1.0: acc -= 1.0; hold = rnd.choice((-1.0, 1.0))
        env = 1.0 if not decay else math.exp(-(i / RATE) / decay)
        out.append(amp * env * hold)
    return out

def fm(car_fn, ratio, index_fn, dur, amp=0.8, decay=None, attack=0.004):
    """2-operator FM voice, like the Genesis YM2612."""
    n = int(RATE * dur); out = []; pc = 0.0; pm = 0.0
    for i in range(n):
        t = i / RATE; f = car_fn(t)
        pm += 2 * math.pi * f * ratio / RATE
        pc += 2 * math.pi * f / RATE
        v = math.sin(pc + index_fn(t) * math.sin(pm))
        env = min(1.0, i / max(1, int(RATE * attack)), (n - 1 - i) / max(1, int(RATE * 0.004)))
        if decay: env *= math.exp(-t / decay)
        out.append(amp * env * v)
    return out

def gb(samples, levels=16):
    """Game Boy flavour: 4-bit amplitude and ~ 16 kHz sample-and-hold grit."""
    out = []; hold = 0.0
    for i, v in enumerate(samples):
        if i % 3 == 0: hold = round((max(-1, min(1, v)) + 1) * (levels - 1) / 2) / ((levels - 1) / 2) - 1
        out.append(hold * 0.9)
    return out

hz = lambda semis: 440.0 * 2 ** (semis / 12)   # semitones from A4

# --- NES style ---
save('n_oneup', mix(sum((square(lambda t, f=hz(s): f, 0.075, duty=0.25) for s in (10, 14, 17, 22, 26)), []) + square(lambda t: hz(29), 0.3, duty=0.25, decay=0.15),
                    triangle(lambda t: hz(-14), 0.6, amp=0.4)))
pass  # n_fireball is made below (flaming version)
pass  # n_warp is made below (deeper, chunkier version)
save('n_alarm', mix(sum((square(lambda t, f=f: f, 0.06, amp=0.45, duty=0.25) for _ in range(20) for f in (hz(19), hz(12))), []),
                    sum((triangle(lambda t: hz(-21), 0.3, amp=0.35) + silence(0.3) for _ in range(4)), [])))
# --- Genesis style (FM) ---
save('s_spin', mix(fm(lambda t: 180 + 1500 * (t / 0.6) ** 2, 2.0, lambda t: 3.0 * (1 - t / 0.6) + 0.5, 0.6, amp=0.6),
                   noise(14000, 0.6, amp=0.12, decay=0.4)))
save('s_bounce', fm(lambda t: 280 + 700 * min(1, t / 0.12) + 40 * math.sin(2 * math.pi * 28 * t), 1.0, lambda t: 2.5 * math.exp(-t / 0.15), 0.4, decay=0.25))
save('s_checkpoint', mix(fm(lambda t: hz(19), 3.5, lambda t: 4 * math.exp(-t / 0.2), 0.9, amp=0.5, decay=0.35),
                         silence(0.12) + fm(lambda t: hz(26), 3.5, lambda t: 4 * math.exp(-t / 0.2), 0.9, amp=0.5, decay=0.4)))
save('s_chime', mix(*[silence(0.07 * k) + fm(lambda t, f=hz(s): f, 3.0, lambda t: 3 * math.exp(-t / 0.15), 0.5, amp=0.35, decay=0.25)
                      for k, s in enumerate((31, 27, 24, 19, 15))]))
save('s_alarm', sum((fm(lambda t, f=f: f, 1.0, lambda t: 1.8, 0.3, amp=0.75) for _ in range(4) for f in (hz(7), hz(2))), []))
# --- Game Boy style (4-bit) ---
save('g_boot', gb(square(lambda t: hz(14), 0.07, amp=0.7, duty=0.5) + square(lambda t: hz(26), 0.6, amp=0.7, duty=0.5, decay=0.2)))
save('g_select', gb(square(lambda t: hz(22), 0.04, amp=0.7, duty=0.25) + square(lambda t: hz(29), 0.07, amp=0.7, duty=0.25, decay=0.05)))
save('g_itemget', gb(mix(sum((square(lambda t, f=hz(s): f, 0.08, amp=0.45, duty=0.125) for s in (12, 16, 19, 24, 28, 31)), []) + square(lambda t: hz(36), 0.4, amp=0.45, duty=0.125, decay=0.2),
                         silence(0.48) + square(lambda t: hz(28) * (1 + 0.01 * math.sin(2 * math.pi * 7 * t)), 0.4, amp=0.3, duty=0.5, decay=0.25))))
save('g_levelup', gb(sum((square(lambda t, f=hz(s): f, 0.055, amp=0.6, duty=0.5) for s in (3, 5, 7, 10, 12, 15)), []) +
                     sum((square(lambda t, f=f: f, 0.05, amp=0.6, duty=0.5) for _ in range(4) for f in (hz(15), hz(19))), [])))
save('g_lowhp', gb(sum((square(lambda t: 1568, 0.1, amp=0.7, duty=0.5) + silence(0.1) for _ in range(12)), [])))

# ===== monster-catching RPG style (Game Boy era, original) =====
pass  # m_wobble is made below (revised)
save('m_heal', gb(mix(sum((square(lambda t, f=hz(s): f, d, amp=0.45, duty=0.5) for s, d in ((12, 0.12), (19, 0.12), (16, 0.12), (24, 0.3))), []),
                      sum((triangle(lambda t, f=hz(s): f, 0.33, amp=0.4) for s in (0, 7)), []))))
pass  # m_evolve is made below (revised)
save('m_encounter', gb(sum((square(lambda t: 1800 - 5000 * t, 0.2, amp=0.6, duty=0.5) + square(lambda t: 800 + 5000 * t, 0.2, amp=0.6, duty=0.25) for _ in range(6)), [])))

# ===== N64 adventure style (sampled-sounding instruments + reverb, original) =====
def reverb(samples, wet=0.35, tail=1.0):
    """Small Schroeder reverb: 4 parallel combs + 2 allpasses."""
    x = samples + [0.0] * int(RATE * tail)
    def comb(sig, d, g):
        out = [0.0] * len(sig); buf = [0.0] * d; j = 0
        for i, v in enumerate(sig):
            y = buf[j]; buf[j] = v + y * g; j = (j + 1) % d; out[i] = y
        return out
    def allpass(sig, d, g):
        out = [0.0] * len(sig); buf = [0.0] * d; j = 0
        for i, v in enumerate(sig):
            b = buf[j]; y = -v + b; buf[j] = v + b * g; j = (j + 1) % d; out[i] = y
        return out
    combs = [comb(x, int(RATE * ms / 1000), 0.80) for ms in (29.7, 37.1, 41.1, 43.7)]
    r = [sum(c[i] for c in combs) / 4 for i in range(len(x))]
    r = allpass(allpass(r, int(RATE * 0.005), 0.7), int(RATE * 0.0017), 0.7)
    return [(1 - wet) * a + wet * b for a, b in zip(x, r)]

def flute(freq, dur, amp=0.55):
    rnd = random.Random(int(freq)); n = int(RATE * dur); out = []; ph = 0.0
    for i in range(n):
        t = i / RATE
        f = freq * (1 + 0.006 * math.sin(2 * math.pi * 5.5 * t) * min(1, t / 0.15))
        ph += 2 * math.pi * f / RATE
        env = min(1.0, t / 0.05) * min(1.0, (dur - t) / 0.08)
        v = math.sin(ph) + 0.18 * math.sin(2 * ph) + 0.06 * math.sin(3 * ph) + 0.05 * rnd.uniform(-1, 1)
        out.append(amp * env * v / 1.25)
    return out

def harp(freq, dur, amp=0.45):
    return [amp * math.exp(-(i / RATE) / 0.35) * (math.sin(2 * math.pi * freq * i / RATE) + 0.3 * math.sin(4 * math.pi * freq * i / RATE)) / 1.3
            for i in range(int(RATE * dur))]

def bell(freq, dur, amp=0.4):
    return fm(lambda t: freq, 2.76, lambda t: 2.0 * math.exp(-t / 0.4), dur, amp=amp, decay=0.6)

save('z_ocarina', reverb(flute(hz(15), 0.28) + flute(hz(10), 0.28) + flute(hz(19), 0.42) + flute(hz(17), 0.28) + flute(hz(22), 0.95), wet=0.38, tail=0.8))
save('z_secret', reverb(mix(*[silence(0.11 * k) + harp(hz(s), 0.6) for k, s in enumerate((12, 16, 19, 23, 26, 28))]), wet=0.35, tail=0.6))
save('z_fairy', reverb(mix(*[silence(0.05 * k) + [0.35 * math.exp(-(i / RATE) / 0.12) * math.sin(2 * math.pi * f * i / RATE) for i in range(int(RATE * 0.3))]
                             for k, f in enumerate((2637, 3136, 3520, 2794, 3951, 3322))]), wet=0.45, tail=0.6))
save('z_treasure', reverb(mix([0.35 * min(1, (i / RATE) / 0.8) * (math.sin(2 * math.pi * hz(-9) * i / RATE) + math.sin(2 * math.pi * hz(-5) * i / RATE) + math.sin(2 * math.pi * hz(-2) * i / RATE)) / 3
                               for i in range(int(RATE * 0.9))],
                              silence(0.85) + bell(hz(15), 0.8) , silence(0.85) + bell(hz(22), 0.8, amp=0.3)), wet=0.3, tail=0.5))
save('z_heart', reverb(sum((square(lambda t: 1760, 0.07, amp=0.35, duty=0.5) + silence(0.05) + square(lambda t: 1760, 0.07, amp=0.35, duty=0.5) + silence(0.41)
                            for _ in range(4)), []), wet=0.3, tail=0.3)[:int(RATE * 2.4)])

# ===== more Game Boy monster-RPG style (original) =====
save('m_cry', gb(mix(square(lambda t: 900 + 500 * math.sin(2 * math.pi * 9 * t) - 900 * t, 0.55, amp=0.45, duty=0.125, decay=0.4),
                     noise(3000 + 0, 0.55, amp=0.25, decay=0.3, seed=7))))
save('m_save', gb(sum((square(lambda t, f=hz(s): f, d, amp=0.55, duty=0.5) for s, d in ((7, 0.09), (12, 0.09), (16, 0.09), (19, 0.09))), [])
                  + mix(square(lambda t: hz(24), 0.35, amp=0.4, duty=0.5, decay=0.2), square(lambda t: hz(19), 0.35, amp=0.3, duty=0.25, decay=0.2))))
save('m_bump', gb(mix(square(lambda t: 140 - 120 * t, 0.12, amp=0.7, duty=0.5, decay=0.06), noise(1500, 0.08, amp=0.4, decay=0.03))))
save('m_spotted', gb(square(lambda t: hz(31), 0.05, amp=0.7, duty=0.25) + silence(0.02) + square(lambda t: hz(31), 0.05, amp=0.7, duty=0.25)
                     + silence(0.04) + square(lambda t: hz(36), 0.3, amp=0.7, duty=0.25, decay=0.15)))

# ===== flaming fireball (replaces the short NES one) =====
def lowpass(samples, cutoff_fn):
    out = []; y = 0.0
    for i, v in enumerate(samples):
        a = 1 - math.exp(-2 * math.pi * cutoff_fn(i / RATE) / RATE)
        y += a * (v - y); out.append(y)
    return out

def fireball():
    dur = 0.65; n = int(RATE * dur); rnd = random.Random(42)
    white = [rnd.uniform(-1, 1) for _ in range(n)]
    # roar: noise through a sweeping low-pass (bright burst, then the flame recedes)
    roar = lowpass(white, lambda t: 6000 * math.exp(-t / 0.18) + 500)
    env = [min(1.0, (i / RATE) / 0.03) * math.exp(-(i / RATE) / 0.28) for i in range(n)]
    roar = [3.2 * r * e for r, e in zip(roar, env)]
    # crackle: random short pops, denser at the start
    crackle = [0.0] * n
    for _ in range(70):
        t0 = rnd.random() ** 1.6 * (dur - 0.02); i0 = int(t0 * RATE); amp = rnd.uniform(0.25, 0.6) * math.exp(-t0 / 0.35)
        for k in range(int(RATE * 0.004)):
            if i0 + k < n: crackle[i0 + k] += amp * rnd.uniform(-1, 1) * (1 - k / (RATE * 0.004))
    # whoosh tone: falling pulse that gives it a "launched" feel
    tone_ = square(lambda t: 900 * math.exp(-t / 0.12) + 120, 0.3, amp=0.25, duty=0.125, decay=0.12)
    return mix(roar, crackle, tone_)
save('n_fireball', fireball())

# ===== GameCube life-sim style (cozy, original) =====
def marimba(freq, dur=0.5, amp=0.5):
    n = int(RATE * dur); out = []
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / 0.003)
        v = math.exp(-t / 0.18) * math.sin(2 * math.pi * freq * t) + 0.35 * math.exp(-t / 0.03) * math.sin(2 * math.pi * freq * 4 * t)
        out.append(amp * env * v)
    return out

def pop(amp=0.6):
    return [amp * math.exp(-(i / RATE) / 0.012) * math.sin(2 * math.pi * (900 - 6000 * i / RATE) * i / RATE) for i in range(int(RATE * 0.06))]

save('c_pluck', reverb(pop() + marimba(hz(19), 0.5), wet=0.2, tail=0.3))
rnd_c = random.Random(3)
def syllable(f):
    # soft vowel-ish blip: two formant-ish partials, quick pitch glide
    return [0.35 * min(1, (i / RATE) / 0.008) * math.exp(-(i / RATE) / 0.04) *
            (math.sin(2 * math.pi * f * (1 + 0.3 * i / RATE) * i / RATE) + 0.5 * math.sin(2 * math.pi * f * 2.5 * i / RATE))
            for i in range(int(RATE * 0.075))]
save('c_chatter', reverb(sum((syllable(rnd_c.choice((520, 580, 650, 700, 780, 880))) + silence(rnd_c.choice((0.01, 0.02, 0.035))) for _ in range(12)), []), wet=0.15, tail=0.25))
save('c_mail', reverb(mix(*[silence(0.12 * k) + marimba(hz(s), 0.6, amp=0.45) for k, s in enumerate((12, 16, 19, 24))],
                          silence(0.5) + bell(hz(28), 0.7, amp=0.25)), wet=0.25, tail=0.4))
save('c_bells', reverb(mix(*[silence(rnd_c.uniform(0, 0.35)) + bell(rnd_c.choice((2093, 2349, 2637, 3136)), 0.35, amp=0.18) for _ in range(9)]), wet=0.3, tail=0.3))
save('c_net', reverb(lowpass([random.Random(5).uniform(-1, 1) * math.sin(math.pi * i / (RATE * 0.35)) for i in range(int(RATE * 0.35))], lambda t: 800 + 5000 * t)[:] and
                     [2.5 * v for v in lowpass([random.Random(5).uniform(-1, 1) * math.sin(math.pi * i / (RATE * 0.35)) for i in range(int(RATE * 0.35))], lambda t: 800 + 5000 * t)]
                     + silence(0.05) + pop(0.5) + marimba(hz(24), 0.35, amp=0.35), wet=0.2, tail=0.3))
save('c_clock', reverb(sum((marimba(hz(s), 0.3, amp=0.45) for _ in range(2) for s in (19, 15, 17, 10)), []) + marimba(hz(10), 0.2, amp=0.0), wet=0.3, tail=0.2)[:int(RATE * 2.4)])

# ===== warp pipe, deeper + chunkier: stepped pitch drop 330 -> 80 Hz, pulse + octave-down triangle =====
def warp_step(t, d=0.24):
    step = int(t / 0.024)                      # pitch changes in chunky 24 ms steps
    return 330 * (80 / 330) ** min(1.0, step * 0.024 / d)
save('n_warp', sum((mix(square(lambda t: warp_step(t), 0.24, amp=0.5, duty=0.5),
                        triangle(lambda t: warp_step(t) / 2, 0.24, amp=0.55)) + silence(0.04) for _ in range(3)), []))

# ===== revised: ball wobble (lower, slower) and evolution (piano, lower) =====
def wobble_click():
    # a low two-part "rock": tick down then tock up, like a ball rocking on the ground
    return (square(lambda t: 170 - 300 * t, 0.07, amp=0.6, duty=0.25) + noise(3000, 0.025, amp=0.25)
            + silence(0.06) + square(lambda t: 120 + 200 * t, 0.06, amp=0.5, duty=0.25) + noise(2500, 0.02, amp=0.2))
save('m_wobble', gb(sum((silence(0.32) + wobble_click() for _ in range(3)), [])
                    + silence(0.35) + square(lambda t: hz(12), 0.07, amp=0.6) + square(lambda t: hz(19), 0.5, amp=0.6, decay=0.22)))

def piano(freq, dur, amp=0.5):
    """Additive piano-ish tone: stretched harmonics, each decaying faster, soft hammer click."""
    n = int(RATE * dur); B = 0.0004; out = []
    parts = [(k, (1 / k ** 1.15), 1.4 / k ** 0.7, freq * k * math.sqrt(1 + B * k * k)) for k in range(1, 9)]
    for i in range(n):
        t = i / RATE
        v = sum(a * math.exp(-t / d) * math.sin(2 * math.pi * f * t) for k, a, d, f in parts)
        env = min(1.0, t / 0.002) * min(1.0, (dur - t) / 0.03)
        out.append(amp * env * v / 2.2)
    return out

# accelerating rising arpeggio C3..C6, then a held C-major chord (all on piano)
notes = [-21, -17, -14, -9, -5, -2, 3, 7, 10, 15]          # C3 E3 G3 C4 E4 G4 C5 E5 G5 C6 (semitones from A4)
gaps = [0.17, 0.15, 0.13, 0.115, 0.1, 0.09, 0.08, 0.07, 0.065, 0.0]
t0 = 0.0; layers = []
for s_, g in zip(notes, gaps):
    layers.append(silence(t0) + piano(hz(s_), 0.9, amp=0.4)); t0 += g
chord_at = t0 + 0.18
for s_ in (-9, -5, -2, 3):                                   # C4 E4 G4 C5
    layers.append(silence(chord_at) + piano(hz(s_), 1.6, amp=0.32))
save('m_evolve', reverb(mix(*layers), wet=0.22, tail=0.4))

# ===== GameCube life-sim style: longer versions (~2 s) of the short clips (overrides the ones above) =====
rnd_c2 = random.Random(11)
save('c_pluck', reverb(pop() + marimba(hz(19), 0.45) + silence(0.15) + pop(0.5) + marimba(hz(24), 0.35)
                       + sum((marimba(hz(s_), 0.2, amp=0.4) for s_ in (19, 21, 24)), []) + marimba(hz(28), 0.6, amp=0.45), wet=0.22, tail=0.4))
save('c_chatter', reverb(sum((syllable(rnd_c2.choice((480, 520, 580, 650, 700, 780, 880))) + silence(rnd_c2.choice((0.01, 0.02, 0.035, 0.05)))
                              for _ in range(22)), []), wet=0.15, tail=0.3))
save('c_mail', reverb(mix(*[silence(0.13 * k) + marimba(hz(s_), 0.7, amp=0.42) for k, s_ in enumerate((7, 12, 16, 19, 24, 28))],
                          silence(0.85) + bell(hz(31), 1.0, amp=0.25), silence(1.05) + bell(hz(28), 0.9, amp=0.18)), wet=0.28, tail=0.5))
save('c_bells', reverb(mix(*[silence(rnd_c2.uniform(0, 1.3)) + bell(rnd_c2.choice((2093, 2349, 2637, 3136, 3520)), 0.4, amp=0.16) for _ in range(18)],
                           silence(1.35) + bell(2637, 0.6, amp=0.22)), wet=0.3, tail=0.4))
swish = lambda d: [2.5 * v for v in lowpass([random.Random(5).uniform(-1, 1) * math.sin(math.pi * i / (RATE * d)) for i in range(int(RATE * d))], lambda t: 600 + 4000 * t / d)]
save('c_net', reverb(swish(0.6) + silence(0.08) + pop(0.55) + marimba(hz(19), 0.3, amp=0.35) + marimba(hz(24), 0.3, amp=0.35)
                     + marimba(hz(31), 0.6, amp=0.4), wet=0.22, tail=0.4))

# ===== Roland MT-32 style jingles (LA-synth-ish instruments; original tunes, moods of early-90s PC games) =====
mf = lambda m: 440.0 * 2 ** ((m - 69) / 12)        # MIDI note -> Hz

def _render(n, fn):
    return [fn(i / RATE) for i in range(n)]

def i_brass(f, d, amp=0.35):
    # saw-ish partials with a filter "blat": brightness rises fast then settles
    n = int(RATE * d); K = 7
    def v(t):
        bright = 0.35 + 0.65 * math.exp(-t / 0.08)
        s_ = sum((bright ** (k - 1)) / k * math.sin(2 * math.pi * f * k * t * (1 + 0.003 * math.sin(2 * math.pi * 5 * t))) for k in range(1, K + 1))
        env = min(1, t / 0.03) * min(1, (d - t) / 0.05)
        return amp * env * s_ / 1.6
    return _render(n, v)

def i_strings(f, d, amp=0.25):
    n = int(RATE * d)
    def v(t):
        s_ = 0.0
        for det in (-0.004, 0.0, 0.005):
            ff = f * (1 + det) * (1 + 0.004 * math.sin(2 * math.pi * 5.5 * t))
            s_ += sum(math.sin(2 * math.pi * ff * k * t) / k for k in range(1, 5))
        env = min(1, t / 0.18) * min(1, (d - t) / 0.12)
        return amp * env * s_ / 5
    return _render(n, v)

def i_steeldrum(f, d, amp=0.45):
    return fm(lambda t: f, 2.0, lambda t: 1.6 * math.exp(-t / 0.08), d, amp=amp, decay=0.28)

def i_organ(f, d, amp=0.22):
    n = int(RATE * d)
    def v(t):
        s_ = math.sin(2*math.pi*f*t) + 0.6*math.sin(2*math.pi*2*f*t) + 0.4*math.sin(2*math.pi*3*f*t) + 0.25*math.sin(2*math.pi*4*f*t)
        env = min(1, t / 0.01) * min(1, (d - t) / 0.04) * (1 + 0.08 * math.sin(2 * math.pi * 6.5 * t))
        return amp * env * s_ / 2.2
    return _render(n, v)

def i_harpsi(f, d, amp=0.3):
    n = int(RATE * d)
    def v(t):
        s_ = sum(math.exp(-t * (3 + 2.5 * k)) * math.sin(2 * math.pi * f * k * t) / (k ** 0.6) for k in range(1, 9))
        return amp * min(1, t / 0.001) * s_ / 3
    return _render(n, v)

def i_bass(f, d, amp=0.5):
    n = int(RATE * d)
    def v(t):
        s_ = math.sin(2*math.pi*f*t) + 0.5*math.exp(-t/0.05)*math.sin(2*math.pi*2*f*t) + 0.25*math.exp(-t/0.03)*math.sin(2*math.pi*3*f*t)
        return amp * min(1, t / 0.004) * math.exp(-t / 0.5) * min(1, (d - t) / 0.03) * s_ / 1.5
    return _render(n, v)

def i_mute_trumpet(f, d, amp=0.32):
    n = int(RATE * d)
    def v(t):
        vib = 1 + 0.006 * math.sin(2 * math.pi * 6 * t) * min(1, t / 0.2)
        s_ = sum((0.55 ** (k - 1)) * math.sin(2 * math.pi * f * vib * k * t) for k in range(1, 6))
        env = min(1, t / 0.02) * min(1, (d - t) / 0.04)
        return amp * env * s_ / 2
    return _render(n, v)

def i_lead(f, d, amp=0.25, glide_from=None):
    g0 = glide_from or f
    return square(lambda t: f + (g0 - f) * math.exp(-t / 0.03), d, amp=amp, duty=0.3)

def i_fife(f, d, amp=0.3):
    return flute(f, d, amp=amp)

def i_timpani(f, d=0.6, amp=0.6):
    rnd = random.Random(int(f))
    return [amp * math.exp(-(i / RATE) / 0.25) * (math.sin(2 * math.pi * f * (1 + 0.15 * math.exp(-(i / RATE) / 0.03)) * i / RATE) + 0.15 * rnd.uniform(-1, 1) * math.exp(-(i / RATE) / 0.02))
            for i in range(int(RATE * d))]

def i_snare(d=0.12, amp=0.35, seed=9):
    rnd = random.Random(seed)
    return [amp * math.exp(-(i / RATE) / 0.04) * (rnd.uniform(-1, 1) + 0.4 * math.sin(2 * math.pi * 190 * i / RATE)) for i in range(int(RATE * d))]

def i_handdrum(d=0.2, amp=0.5):
    return [amp * math.exp(-(i / RATE) / 0.07) * math.sin(2 * math.pi * (140 + 120 * math.exp(-(i / RATE) / 0.02)) * i / RATE) for i in range(int(RATE * d))]

def seq(events, total):
    """events: (start_s, samples). Mixed into a buffer of `total` seconds."""
    buf = [0.0] * int(RATE * total)
    for st, smp in events:
        o = int(RATE * st)
        for k, v in enumerate(smp):
            if o + k < len(buf): buf[o + k] += v
    peak = max(1e-9, max(abs(x) for x in buf))
    g = min(1.0, 0.9 / peak)
    return [x * g for x in buf]

def mt32(name, events, total, wet=0.25):
    save(name, reverb(seq(events, total), wet=wet, tail=0.5))

# 1) Pirate island steel drums (C major, reggae lilt)
e = 0.15; ev = []
for k, m in enumerate([79, 76, 79, 81, 84, 81, 79, 76, 74, 76, 79]):
    ev.append((k * e, i_steeldrum(mf(m), 0.5 if k < 10 else 1.0)))
for k, (b, ch) in enumerate([(48, (64, 67, 72)), (53, (65, 69, 72)), (55, (62, 67, 71)), (48, (64, 67, 72))]):
    ev.append((k * 4 * e, i_bass(mf(b), 4 * e)))
    for m in ch: ev.append((k * 4 * e + 2 * e, marimba(mf(m), 0.3, amp=0.2)))
mt32('t_pirate', ev, 2.6)

# 2) Voodoo swamp (D minor organ + harpsichord + hand drum)
e = 0.17; ev = [(0, i_organ(mf(m), 2.3)) for m in (50, 53, 57)]
for k, m in enumerate([74, 77, 76, 74, 73, 74, 69]):
    ev.append((k * e, i_harpsi(mf(m), 0.4 if k < 6 else 1.0)))
for k in range(0, 13, 2): ev.append((k * e, i_handdrum(amp=0.45 if k % 4 == 0 else 0.3)))
mt32('t_voodoo', ev, 2.5, wet=0.3)

# 3) Archaeology fanfare (B-flat brass, timpani, strings)
ev = [(0, i_timpani(mf(46), 0.5)), (0.1, i_timpani(mf(46), 0.5, amp=0.4))]
for st, m, d in [(0.0, 70, 0.3), (0.3, 77, 0.45), (0.75, 75, 0.15), (0.9, 74, 0.15), (1.05, 72, 0.15), (1.2, 70, 0.3), (1.5, 77, 0.9)]:
    ev.append((st, i_brass(mf(m), d)))
for m in (58, 65, 70): ev.append((1.5, i_strings(mf(m), 0.9)))
ev.append((1.5, i_timpani(mf(41), 0.7)))
mt32('t_fanfare', ev, 2.6)

# 4) Starfighter briefing (C minor strings, rising brass fifths)
ev = [(0, i_strings(mf(m), 2.4, amp=0.2)) for m in (48, 55, 63)]
for st, m, d in [(0.2, 60, 0.25), (0.45, 67, 0.25), (0.7, 72, 0.25), (0.95, 74, 0.2), (1.15, 75, 0.2), (1.35, 79, 1.0)]:
    ev.append((st, i_brass(mf(m), d, amp=0.32)))
ev += [(0.2, i_timpani(mf(36), 0.4)), (1.35, i_timpani(mf(36), 0.8))]
mt32('t_starfighter', ev, 2.6)

# 5) Noir detective jazz (walking bass, muted trumpet, brushes)
sw = [0, 0.2, 0.3, 0.5, 0.6, 0.8, 0.9, 1.1]       # swung eighths
ev = [(t, i_bass(mf(m), 0.22, amp=0.55)) for t, m in zip([0, 0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1], [43, 47, 50, 52, 53, 52, 50, 47])]
for t, m, d in [(0.3, 74, 0.2), (0.5, 77, 0.1), (0.6, 79, 0.2), (0.8, 80, 0.1), (0.9, 79, 0.3), (1.2, 77, 0.2), (1.4, 74, 0.6)]:
    ev.append((t, i_mute_trumpet(mf(m), d)))
for k in range(8): ev.append((k * 0.3 + 0.15, i_snare(0.08, amp=0.12, seed=k)))
mt32('t_noir', ev, 2.5, wet=0.3)

# 6) Space janitor sci-fi (synth arpeggios + gliding lead + bleeps)
ev = []
for k, m in enumerate([57, 60, 64, 69] * 4): ev.append((k * 0.075, square(lambda t, f=mf(m): f, 0.07, amp=0.18, duty=0.25)))
for st, m, g in [(0.0, 76, 64), (0.6, 81, 76), (0.9, 79, 81), (1.2, 84, 79)]:
    ev.append((st, i_lead(mf(m), 0.5 if st < 1.2 else 0.8, glide_from=mf(g))))
for k in range(5): ev.append((1.3 + 0.08 * k, square(lambda t, f=2400 + 300 * k: f, 0.03, amp=0.12)))
ev.append((0, i_bass(mf(33), 2.0, amp=0.4)))
mt32('t_scifi', ev, 2.3)

# 7) Empire advance (stately brass + strings + timpani)
ev = []
for st, m, d in [(0.0, 60, 0.3), (0.3, 64, 0.3), (0.6, 67, 0.3), (0.9, 72, 1.3)]:
    ev.append((st, i_brass(mf(m), d)))
for m in (55, 60, 64): ev.append((0.9, i_strings(mf(m), 1.3)))
ev += [(0.0, i_timpani(mf(36), 0.3)), (0.6, i_timpani(mf(43), 0.3)), (0.9, i_timpani(mf(36), 0.9))]
mt32('t_empire', ev, 2.5)

# 8) New world colony (fife + snare rudiments + harpsichord bass, G major)
ev = []
for k, m in enumerate([79, 81, 83, 84, 86, 83, 84, 81, 79]):
    ev.append((k * 0.16, i_fife(mf(m), 0.16 if k < 8 else 0.7)))
for k in range(18): ev.append((k * 0.08, i_snare(0.06, amp=0.18 if k % 4 else 0.3, seed=k)))
for k, m in enumerate([43, 50, 47, 50, 43]): ev.append((k * 0.32, i_harpsi(mf(m), 0.4, amp=0.3)))
mt32('t_colony', ev, 2.3, wet=0.2)

# ===== family radio-drama style cues (small-town orchestra; original tunes) =====
def i_pizz(f, d=0.4, amp=0.4):
    return [amp * min(1, (i / RATE) / 0.002) * math.exp(-(i / RATE) / 0.11) *
            (math.sin(2 * math.pi * f * i / RATE) + 0.4 * math.sin(4 * math.pi * f * i / RATE) + 0.15 * math.sin(6 * math.pi * f * i / RATE)) / 1.5
            for i in range(int(RATE * d))]

def i_clarinet(f, d, amp=0.3):
    n = int(RATE * d)
    def v(t):
        vib = 1 + 0.004 * math.sin(2 * math.pi * 5 * t) * min(1, t / 0.25)
        s_ = math.sin(2*math.pi*f*vib*t) + 0.45*math.sin(2*math.pi*3*f*vib*t) + 0.2*math.sin(2*math.pi*5*f*vib*t) + 0.08*math.sin(2*math.pi*7*f*vib*t)
        return amp * min(1, t / 0.04) * min(1, (d - t) / 0.05) * s_ / 1.7
    return _render(n, v)

def i_horn(f, d, amp=0.3):
    n = int(RATE * d)
    def v(t):
        s_ = sum((0.45 ** (k - 1)) * math.sin(2 * math.pi * f * k * t) for k in range(1, 5))
        return amp * min(1, t / 0.07) * min(1, (d - t) / 0.08) * s_ / 1.7
    return _render(n, v)

# 1) Soda shop whimsy: bouncy pizzicato bass + clarinet tune + flute answer (F major)
ev = []
for k, m in enumerate([41, 48, 45, 48, 46, 53, 48, 41]): ev.append((k * 0.25, i_pizz(mf(m), 0.3, amp=0.45)))
for st, m, d in [(0.0, 72, 0.25), (0.25, 77, 0.25), (0.5, 76, 0.125), (0.625, 74, 0.125), (0.75, 72, 0.5), (1.25, 69, 0.25), (1.5, 70, 0.25)]:
    ev.append((st, i_clarinet(mf(m), d)))
for st, m, d in [(1.75, 81, 0.15), (1.9, 84, 0.15), (2.05, 89, 0.6)]: ev.append((st, flute(mf(m), d, amp=0.3)))
mt32('o_whimsy', ev, 2.8, wet=0.22)

# 2) Gentle lesson: warm piano melody over soft strings (C major, slow)
ev = [(0, i_strings(mf(m), 2.8, amp=0.16)) for m in (48, 55, 64)]
for st, m in [(0.0, 76), (0.35, 79), (0.7, 77), (1.05, 76), (1.4, 74), (1.75, 72)]: ev.append((st, piano(mf(m), 1.0, amp=0.35)))
for m in (60, 64, 67, 72): ev.append((1.75, piano(mf(m), 1.2, amp=0.22)))
mt32('o_lesson', ev, 3.0, wet=0.28)

# 3) Mystery tiptoe: staccato pizzicato in D minor + sneaky low clarinet + soft timpani
ev = []
for k, m in enumerate([50, 53, 57, 56, 57, 53, 50, 49]): ev.append((k * 0.2, i_pizz(mf(m), 0.25, amp=0.45)))
for st, m, d in [(0.8, 62, 0.2), (1.0, 65, 0.2), (1.2, 64, 0.2), (1.4, 61, 0.7)]: ev.append((st, i_clarinet(mf(m), d, amp=0.28)))
ev += [(0.0, i_timpani(mf(38), 0.4, amp=0.3)), (1.4, i_timpani(mf(38), 0.6, amp=0.35))]
mt32('o_mystery', ev, 2.5, wet=0.25)

# 4) Adventure begins: horn call over rising strings (E-flat), snare roll into a held chord
ev = [(0, i_strings(mf(m), 2.9, amp=0.17)) for m in (51, 58, 63)]
for st, m, d in [(0.0, 63, 0.3), (0.3, 70, 0.45), (0.75, 68, 0.15), (0.9, 67, 0.15), (1.05, 65, 0.3), (1.35, 70, 0.3), (1.65, 75, 1.0)]:
    ev.append((st, i_horn(mf(m), d)))
for k in range(10): ev.append((1.15 + k * 0.05, i_snare(0.05, amp=0.1 + 0.015 * k, seed=20 + k)))
ev.append((1.65, i_timpani(mf(39), 0.8, amp=0.45)))
mt32('o_adventure', ev, 3.0, wet=0.28)

# ===== NES platformer music style tracks (2A03: 2 pulses + triangle + noise; original tunes) =====
def nes_lead(f, d, duty=0.5, amp=0.32):
    # pulse lead with delayed vibrato and a slight volume decay, like a 2A03 envelope
    return square(lambda t: f * (1 + 0.012 * math.sin(2 * math.pi * 6 * t) * max(0, min(1, (t - 0.12) / 0.1))), d, amp=amp, duty=duty, decay=1.2)

def nes_hat(amp=0.12, seed=0):
    return noise(12000, 0.035, amp=amp, decay=0.012, seed=seed)

def nes_kick(amp=0.5):
    return triangle(lambda t: 160 * math.exp(-t / 0.03) + 45, 0.09, amp=amp)

def nes_track(name, tempo_bpm, lead, harm, bass, steps, total):
    """lead/harm/bass: lists of (step, midi, len_steps); 16th-note steps."""
    st = 60 / tempo_bpm / 4
    ev = []
    for k, m, L in lead: ev.append((k * st, nes_lead(mf(m), L * st * 0.95, duty=0.5)))
    for k, m, L in harm: ev.append((k * st, nes_lead(mf(m), L * st * 0.95, duty=0.25, amp=0.18)))
    for k, m, L in bass: ev.append((k * st, triangle(lambda t, f=mf(m): f, L * st * 0.9, amp=0.5)))
    for k in range(steps):
        if k % 4 == 0: ev.append((k * st, nes_kick()))
        if k % 2 == 1: ev.append((k * st, nes_hat(seed=k)))
        if k % 8 == 4: ev.append((k * st, noise(5000, 0.08, amp=0.22, decay=0.03, seed=100 + k)))
    save(name, seq(ev, total))

# 1) Treasure hunt: bright, bouncy, C major
nes_track('n_trk_treasure', 150,
    lead=[(0, 72, 2), (2, 76, 2), (4, 79, 3), (7, 77, 1), (8, 76, 2), (10, 74, 2), (12, 72, 2), (14, 74, 2),
          (16, 76, 2), (18, 79, 2), (20, 84, 4), (24, 83, 2), (26, 81, 2), (28, 79, 4)],
    harm=[(0, 64, 4), (4, 67, 4), (8, 65, 4), (12, 64, 4), (16, 67, 4), (20, 72, 4), (24, 71, 4), (28, 67, 4)],
    bass=[(k * 2, m, 2) for k, m in enumerate([48, 55, 48, 55, 53, 60, 53, 60, 48, 55, 48, 55, 55, 62, 55, 43])],
    steps=32, total=3.4)

# 2) Lunar expedition: soaring, A minor -> C major lift, slower
nes_track('n_trk_lunar', 120,
    lead=[(0, 69, 4), (4, 72, 2), (6, 76, 2), (8, 74, 6), (14, 72, 2), (16, 71, 2), (18, 72, 2), (20, 74, 2), (22, 76, 2), (24, 79, 8)],
    harm=[(0, 64, 8), (8, 65, 8), (16, 67, 8), (24, 72, 8)],
    bass=[(k * 2, m, 2) for k, m in enumerate([45, 52, 45, 52, 41, 48, 41, 48, 43, 50, 43, 50, 48, 55, 48, 55])],
    steps=32, total=4.2)

# 3) Pogo bounce: quick hops, F major, octave-jumping bass
nes_track('n_trk_pogo', 168,
    lead=[(0, 77, 1), (1, 81, 1), (2, 84, 2), (4, 81, 1), (5, 84, 1), (6, 89, 2), (8, 88, 1), (9, 86, 1), (10, 84, 2), (12, 81, 2), (14, 84, 2),
          (16, 77, 1), (17, 81, 1), (18, 84, 2), (20, 86, 2), (22, 88, 2), (24, 89, 6)],
    harm=[(0, 69, 4), (4, 72, 4), (8, 70, 4), (12, 69, 4), (16, 69, 4), (20, 70, 4), (24, 72, 6)],
    bass=[(k, m, 1) for k, m in enumerate([41, 53] * 8 + [46, 58] * 4 + [48, 60] * 2 + [41, 53])],
    steps=30, total=3.1)
