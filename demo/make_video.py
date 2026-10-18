"""Free-tool demo video builder: slides (PIL terminal-style frames) + edge-tts narration + ffmpeg. Usage: python3 make_video.py spec.json out.mp4"""
import json, sys, subprocess, asyncio, os, tempfile
from PIL import Image, ImageDraw, ImageFont
import edge_tts
spec = json.load(open(sys.argv[1])); out = sys.argv[2]; voice = spec.get("voice", "en-US-GuyNeural")
M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
d = tempfile.mkdtemp(); parts = []
def frame(s, path):
    im = Image.new("RGB", (1280, 720), (18, 20, 26)); g = ImageDraw.Draw(im)
    g.rectangle([0, 0, 1280, 64], fill=(35, 40, 52)); g.text((24, 14), s["title"], font=ImageFont.truetype(B, 30), fill=(255, 200, 80))
    if s.get("label"): g.text((900, 22), s["label"], font=ImageFont.truetype(B, 18), fill=(120, 200, 255))
    f = ImageFont.truetype(M, s.get("size", 20)); y = 84
    for ln in s["lines"]:
        col = (120, 230, 140) if ln.startswith("$") else (255, 110, 110) if "BLOCK" in ln else (230, 230, 230)
        g.text((28, y), ln, font=f, fill=col); y += int(s.get("size", 20) * 1.45)
    im.save(path)
async def tts(t, p): await edge_tts.Communicate(t, voice, rate=spec.get("rate", "+0%")).save(p)
for i, s in enumerate(spec["slides"]):
    png, mp3, mp4 = [f"{d}/{i}.{e}" for e in ("png", "mp3", "mp4")]
    frame(s, png); asyncio.run(tts(s["say"], mp3))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-i", mp3, "-af", "apad=pad_dur=0.6", "-shortest", "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-ar", "44100", mp4], check=True)
    parts.append(mp4)
open(f"{d}/l.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{d}/l.txt", "-c", "copy", out], check=True)
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip(), "s ->", out)
