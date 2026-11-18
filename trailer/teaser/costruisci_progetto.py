"""Genera TEASER_CAVALLI_MONGOLI.fcproj (FilmCraft 0.12, schema 15): storia Instagram 1080x1920, 30 fps, 12 s.

Il montaggio è scritto in fotogrammi di sequenza (30 fps) e segue la mappa dei colpi della musica (music.py):
  0-75    apertura: primo piano della cartella, messa a fuoco (nessun testo: i titoli si aggiungono a parte)
  75      BRAAM 1 + flash  -> il cursore arriva e seleziona la cartella (scossone)
  117     BRAAM 2 + glitch -> si apre il menu contestuale
  141-222 rallenty 0.25x su «Sposta nel Cestino», zoom lento (riser + orologio)
  222-240 stutter: il click ripetuto 3 volte, sempre più vicino (3 colpi)
  240-246 nero e silenzio
  246     BOOM -> la cartella sparisce al rallentatore (266), con eco fantasma
  300-360 impatto finale su fondo sfocato: spazio libero per i titoli, aggiunti a parte
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPS = 254016000000            # tick al secondo (base tempi di FilmCraft)
FPS = 30
FR = TPS // FPS               # tick per fotogramma di sequenza
W, H = 1080, 1920
SRC_W, SRC_H = 1246, 786

# la registrazione schermo originale è a frame-rate variabile: FilmCraft la legge male,
# quindi si usa una copia a 60 fps costanti (ffmpeg -vf fps=60)
VIDEO = os.path.join(HERE, "girato-cancellazione-60fps.mov")
MUSIC = os.path.join(HERE, "musica-teaser.wav")
GFX = {k: os.path.join(HERE, "grafica", f) for k, f in
       [("vignetta", "vignettatura.png")]}


def sec(s):
    return int(round(s * TPS))


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


# ---------------------------------------------------------------- media
_next = [100]


def nid():
    _next[0] += 1
    return _next[0]


def interpret():
    return {"frame_rate": None, "par": None, "ignore_alpha": False, "invert_alpha": False}


def color(transfer="Bt709", rng="Limited"):
    return {"matrix": "Bt709", "transfer": transfer, "primaries": "Bt709", "range": rng}


def media_item(iid, name, path, info, label):
    return {"id": iid, "name": name, "label": label, "kind": {"Media": {
        "media": {"File": {"path": path}}, "info": info, "interpret": interpret(),
        "mark_in": None, "mark_out": None, "markers": [], "offline": False, "proxy": None}},
        "metadata": {}, "created": iid}


items = {}
V_ID, A_ID = 1, 2
vdur = probe_duration(VIDEO)
items[V_ID] = media_item(V_ID, os.path.basename(VIDEO), VIDEO, {
    "name": os.path.basename(VIDEO), "kind": "Movie", "duration": sec(vdur),
    "video": {"width": SRC_W, "height": SRC_H, "frame_rate": {"num": 60, "den": 1}, "par": [1, 1],
              "codec": "H.264 (High)", "pixel_format": "YUV 4:2:0 8-bit", "color": color(), "has_alpha": False,
              "bitrate": 3032466},
    "audio_streams": [], "container": "QuickTime", "start_timecode": None, "file_size": os.path.getsize(VIDEO)},
    "Violet")
adur = probe_duration(MUSIC)
items[A_ID] = media_item(A_ID, os.path.basename(MUSIC), MUSIC, {
    "name": os.path.basename(MUSIC), "kind": "AudioOnly", "duration": sec(adur), "video": None,
    "audio_streams": [{"sample_rate": 48000, "channels": 2, "codec": "PCM", "bits_per_sample": 16}],
    "container": "WAV", "start_timecode": None, "file_size": os.path.getsize(MUSIC)}, "Caribbean")
G_ID = {}
for i, (k, p) in enumerate(GFX.items()):
    iid = 3 + i
    G_ID[k] = iid
    items[iid] = media_item(iid, os.path.basename(p), p, {
        "name": os.path.basename(p), "kind": "Still", "duration": sec(5),
        "video": {"width": W, "height": H, "frame_rate": {"num": 30, "den": 1}, "par": [1, 1], "codec": "PNG",
                  "pixel_format": "RGBA 8-bit", "color": color("Srgb", "Full"), "has_alpha": True, "bitrate": None},
        "audio_streams": [], "container": "Image", "start_timecode": None, "file_size": os.path.getsize(p)},
        "Lavender")


# ---------------------------------------------------------------- parametri animabili
def P(v):
    if isinstance(v, bool):
        return {"Bool": v}
    if isinstance(v, (tuple, list)):
        return {"Vec2": {"x": float(v[0]), "y": float(v[1])}}
    if isinstance(v, int) and not isinstance(v, bool):
        return {"Float": float(v)}
    return {"Float": float(v)}


def param(v, keys=None):
    """keys: lista di (tick_sorgente, valore, interp)."""
    d = {"value": P(v)}
    if keys:
        d["keyframes"] = [{"time": int(t), "value": P(val), "interp": ip,
                           "out_influence": 1 / 3, "in_influence": 1 / 3} for t, val, ip in keys]
    return d


class Clip:
    def __init__(self, item, start_f, dur_f, src_in_s=0.0, speed=1.0, reverse=False, name=None):
        self.id = nid()
        self.item, self.start_f, self.dur_f = item, start_f, dur_f
        self.src_in = sec(src_in_s)
        self.speed, self.reverse = speed, reverse
        self.name = name or items[item]["name"]
        self.motion = {"anchor": None, "position": (W / 2, H / 2), "scale": 100.0, "rotation": 0.0}
        self.kf = {}          # param -> [(frame_rel, value, interp)]
        self.opacity = 100.0
        self.op_kf = []
        self.blend = 0
        self.extra = []       # effetti aggiuntivi

    def src_tick(self, rel_f):
        """fotogramma relativo alla clip -> tick di tempo sorgente (base dei keyframe)."""
        return self.src_in + int(round(rel_f * FR * self.speed))

    def key(self, name, rel_f, val, interp="Linear"):
        self.kf.setdefault(name, []).append((rel_f, val, interp))
        return self

    def fx(self, effect, params=None):
        self.extra.append({"effect": effect, "enabled": True, "params": params or {}})
        return self

    def json(self, video=True):
        if video:
            anchor = self.motion["anchor"] or ((SRC_W / 2, SRC_H / 2) if self.item == V_ID else (W / 2, H / 2))
            m = {}
            for nm in ("position", "scale", "rotation"):
                ks = [(self.src_tick(f), v, ip) for f, v, ip in self.kf.get(nm, [])]
                m[nm] = param(self.motion[nm], ks or None)
            aks = [(self.src_tick(f), v, ip) for f, v, ip in self.kf.get("anchor", [])]
            effects = [
                {"effect": "motion", "enabled": True, "params": {
                    "anchor": param(anchor, aks or None), "anti_flicker": param(0.0), "position": m["position"],
                    "rotation": m["rotation"], "scale": m["scale"], "scale_width": param(100.0),
                    "uniform_scale": param(True)}},
                {"effect": "opacity", "enabled": True, "params": {
                    "blend": {"value": {"Choice": self.blend}},
                    "opacity": param(self.opacity, [(self.src_tick(f), v, ip) for f, v, ip in self.op_kf] or None)}},
                {"effect": "time_remap", "enabled": True, "params": {"speed": param(self.speed * 100)}},
            ] + self.extra
        else:
            effects = [
                {"effect": "volume", "enabled": True, "params": {"bypass": param(False), "level": param(0.0)}},
                {"effect": "channel_volume", "enabled": True,
                 "params": {"bypass": param(False), "left": param(0.0), "right": param(0.0)}},
                {"effect": "panner", "enabled": True, "params": {"balance": param(0.0)}},
            ]
        return {"id": self.id, "item": self.item, "name": self.name, "label": items[self.item]["label"],
                "start": self.start_f * FR, "duration": self.dur_f * FR, "source_in": self.src_in,
                "speed": self.speed, "reverse": self.reverse, "enabled": True, "link": None, "group": None,
                "effects": effects, "markers": [], "gain_db": 0.0, "frame_hold": None, "scale_to_frame": False}


def frame_on(clip, x, y, scale):
    """Inquadra il punto sorgente (x, y) al centro dello schermo verticale, senza scoprire bordi neri."""
    s = scale / 100
    hw, hh = W / 2 / s, H / 2 / s
    x = min(max(x, hw), SRC_W - hw) if hw < SRC_W / 2 else SRC_W / 2
    y = min(max(y, hh), SRC_H - hh) if hh < SRC_H / 2 else SRC_H / 2
    return (x, y)


def shot(start_f, dur_f, src_in, speed, poi, scale0, scale1, interp="Linear"):
    c = Clip(V_ID, start_f, dur_f, src_in, speed)
    c.motion["anchor"] = frame_on(c, poi[0], poi[1], min(scale0, scale1))
    c.motion["scale"] = scale0
    c.key("scale", 0, scale0, interp).key("scale", dur_f, scale1, interp)
    return c


def shake(c, at_rel, amp=14, rot=2.2, frames=8):
    """Scossone da impatto: posizione e rotazione che oscillano e si smorzano."""
    import math
    for i in range(frames + 1):
        k = (1 - i / frames) ** 2
        dx = amp * k * (1 if i % 2 else -1)
        dy = amp * 0.7 * k * (-1 if i % 3 else 1)
        c.key("position", at_rel + i, (W / 2 + dx, H / 2 + dy))
        c.key("rotation", at_rel + i, rot * k * (1 if i % 2 == 0 else -1))
    return c


FOLDER = (892, 300)
MENU_ITEM = (560, 296)

v1, v2, v3, v4 = [], [], [], []
trans_v1 = []
TOT = 360                     # 12 s

# eventi misurati sul girato a 60 fps: selezione 3.033 s, menu 5.267, «Conserva» sfiorato 6.07,
# «Sposta nel Cestino» 6.20, lampeggio del click 7.05-7.12, menu svanisce 7.17-7.22, cartella sparita 7.433

# A — apertura (0-75): primo piano della cartella, messa a fuoco lenta
A = shot(0, 75, 0.20, 0.6, FOLDER, 330, 400, "EaseIn")
A.op_kf = [(0, 0.0, "Linear"), (20, 100.0, "Linear")]
A.fx("gaussian_blur", {"blurriness": param(0.0, [(A.src_tick(0), 40.0, "EaseOut"), (A.src_tick(35), 0.0, "Linear")])})
v1.append(A)

# B — BRAAM 1 a 75: il cursore arriva e seleziona (selezione al fotogramma 112)
B = shot(75, 42, 1.80, 1.0, (870, 330), 270, 305, "Linear")
shake(B, 0, 18, 2.6, 9)
v1.append(B)

# C — BRAAM 2 a 117: si apre il menu (fotogramma 127)
C = shot(117, 24, 5.10, 0.5, (450, 420), 250, 265, "Linear")
shake(C, 0, 12, 1.8, 7)
v1.append(C)

# D — rallenty 0.25x (141-222) su «Sposta nel Cestino»: «Conserva» a 184, «Sposta» evidenziato a 200
D = shot(141, 81, 5.71, 0.25, MENU_ITEM, 270, 345, "EaseIn")
D.motion["anchor"] = frame_on(D, 385, 296, 270)
D.key("anchor", 0, D.motion["anchor"], "Linear").key("anchor", 81, frame_on(D, 415, 297, 345), "Linear")
v1.append(D)

# E — stutter (222-240): il click, tre volte, sempre più vicino alla scritta
for i, sc in enumerate((360, 440, 530)):
    e = Clip(V_ID, 222 + 6 * i, 6, 7.00, 1.0)
    e.motion["anchor"] = frame_on(e, 392, 297, sc)
    e.motion["scale"] = sc
    e.key("scale", 0, sc * 1.06).key("scale", 6, sc)
    shake(e, 0, 10 + 4 * i, 1.5 + i, 5)
    v1.append(e)

# (240-246: nero e silenzio)

# F — BOOM a 246: la cartella sparisce al rallentatore (fotogramma 266)
F = shot(246, 54, 7.267, 0.25, FOLDER, 320, 270, "EaseOut")
F.op_kf = [(0, 100.0, "Linear"), (46, 100.0, "Linear"), (54, 0.0, "Linear")]
shake(F, 0, 22, 3.0, 10)
v1.append(F)
# eco fantasma in ritardo: la cartella "resta" per qualche fotogramma dopo essere sparita
Fg = shot(246, 54, 7.21, 0.25, FOLDER, 335, 285, "EaseOut")
Fg.opacity = 38.0
Fg.blend = 0      # Normal: indice del Blend Mode certo
Fg.op_kf = [(0, 38.0, "Linear"), (40, 38.0, "Linear"), (54, 0.0, "Linear")]
Fg.fx("gaussian_blur", {"blurriness": param(14.0)})
v2.append(Fg)

# G — impatto finale a 300 (300-360): il desktop SENZA la cartella, sfocato e scuro.
# Fondo libero per i titoli, che vengono aggiunti a parte.
G = shot(300, TOT - 300, 9.0, 1.0, FOLDER, 248, 262, "Linear")
G.opacity = 40.0
G.op_kf = [(0, 0.0, "Linear"), (5, 40.0, "Linear"), (40, 40.0, "Linear"), (60, 0.0, "Linear")]
G.fx("gaussian_blur", {"blurriness": param(60.0)})
shake(G, 0, 14, 1.0, 8)
v1.append(G)

# (nessun cartello: i testi vengono aggiunti a parte)


# transizioni sui tagli del binario V1
def transition(effect, a, b, dur_f, params=None):
    cut = b.start_f
    return {"id": nid(), "effect": {"effect": effect, "enabled": True, "params": params or {}},
            "start": (cut - dur_f // 2) * FR, "duration": dur_f * FR, "from": a.id, "to": b.id,
            "align": "CenterAtCut", "reverse": False}


trans_v1.append(transition("flash", A, B, 6))
trans_v1.append(transition("glitch", B, C, 6))
trans_v1.append(transition("chroma_leak", C, D, 6))
E1, E2, E3 = [c for c in v1 if c.start_f in (222, 228, 234)]
trans_v1.append(transition("flash", D, E1, 2))
trans_v1.append(transition("flash", E1, E2, 2))
trans_v1.append(transition("flash", E2, E3, 2))
trans_v1.append(transition("dip_to_white", F, G, 4))

# vignettatura su tutto il video
vig = Clip(G_ID["vignetta"], 0, TOT)
vv = [vig]

music = Clip(A_ID, 0, TOT, 0.0, 1.0)


def track(tid, kind, name, clips, transitions=(), video=True):
    return {"id": tid, "kind": kind, "name": name, "items": [c.json(video) for c in sorted(clips, key=lambda c: c.start_f)],
            "transitions": list(transitions), "locked": False, "sync_lock": True, "enabled": True, "muted": False,
            "solo": False, "channels": "Stereo", "volume_db": 0.0, "pan": 0.0, "effects": [],
            "mixer": {"mode": "Read", "output": None, "record_arm": False, "solo_safe": False, "input_map": "Stereo"}}


SEQ = 50
seq = {"id": SEQ, "name": "TEASER 9x16", "label": "Forest", "kind": {"Sequence": {
    "settings": {"width": W, "height": H, "frame_rate": {"num": FPS, "den": 1}, "par": [1, 1], "sample_rate": 48000,
                 "drop_frame": False, "preset": f"{W}x{H} {FPS}", "audio_master": "Stereo",
                 "preview_codec": "ProRes 422", "max_bit_depth": False, "max_render_quality": True,
                 "working_space": "Rec. 709", "color": {"working": "Rec709", "wide_gamut": False, "auto_tone_map": True}},
    "video_tracks": [track(11, "Video", "Video 1", v1, trans_v1), track(12, "Video", "Video 2", v2),
                     track(13, "Video", "Video 3", vv), track(14, "Video", "Video 4", v3)],
    "audio_tracks": [track(21, "Audio", "Audio 1", [music], video=False)],
    "markers": [], "mark_in": None, "mark_out": None, "work_area": None, "start_timecode": 0,
    "master_volume_db": 0.0, "master_effects": [],
    "master_mixer": {"mode": "Read", "output": None, "record_arm": False, "solo_safe": False, "input_map": "Stereo"},
    "submix_tracks": [], "caption_tracks": []}}, "metadata": {}, "created": SEQ}
items[SEQ] = seq

project = {"format": "filmcraft.project", "schema_version": 15, "generator": "FilmCraft 0.12.0", "project": {
    "name": "TEASER_CAVALLI_MONGOLI",
    "settings": {"renderer": "FilmCraft GPU Acceleration (wgpu)", "video_display": "Timecode",
                 "audio_display_samples": True, "default_still_duration": 1270080000000,
                 "default_transition_duration_frames": 24, "default_audio_transition_duration": 254016000000,
                 "ingest": {"enabled": False, "action": "createProxies", "destination": None, "preset": ""},
                 "title_safe": [20.0, 20.0], "action_safe": [10.0, 10.0], "capture_format": "DV",
                 "scratch": {"captured": None, "videoPreviews": None, "audioPreviews": None, "autoSave": None}},
    "root": {"id": 0, "name": "TEASER_CAVALLI_MONGOLI", "children": [{"Item": k} for k in sorted(items)]},
    "items": {str(k): v for k, v in sorted(items.items())}, "next_id": _next[0] + 1}}

out = os.path.join(HERE, "TEASER_CAVALLI_MONGOLI.fcproj")
with open(out, "w") as f:
    json.dump(project, f)
print("scritto", out, "clip V1:", len(v1), "transizioni:", len(trans_v1))
