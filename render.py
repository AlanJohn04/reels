#!/usr/bin/env python3
"""
ORV YouTube Automation - PRO Reels Renderer (v4.0)
Based on High-Retention Manhwa Recap Trends:
1. "3-Second Rule" - Rapid, narrative-synced cuts.
2. "Split Screen Background" - Blurred background to fill 9:16 space.
3. "Dynamic Ken Burns" - Continuous movement for every clip.
4. "Combat SFX & Shakes" - Subtle shakes and pings for system messages.
5. "Fast Pacing" - No silences, aggressive narrative mapping.
"""

import argparse
import os
import sys
import glob
import re
import random
import numpy as np

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, ColorClip, vfx
    )
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    print("ERROR: Missing dependencies: pip install moviepy pillow numpy")
    sys.exit(1)

# Constants for 9:16 Shorts
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
BACKGROUND_COLOR = (12, 12, 12)

def parse_vtt(vtt_file):
    subs = []
    if not os.path.exists(vtt_file):
        print(f"  Warning: No VTT found at {vtt_file}")
        return subs
    with open(vtt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Matches timestamp --> timestamp \n Text
    blocks = re.findall(r'(\d+):(\d+):(\d+[.,]\d+)\s*-->\s*(\d+):(\d+):(\d+[.,]\d+)\n(.*?)(?=\n\n|\n*$)', content, re.DOTALL)
    def t_to_s(h, m, s): return int(h)*3600 + int(m)*60 + float(s.replace(',', '.'))
    for h1, m1, s1, h2, m2, s2, text in blocks:
        subs.append({"start": t_to_s(h1, m1, s1), "end": t_to_s(h2, m2, s2), "text": text.strip()})
    return subs

def create_background(img, duration):
    """Creates a zoomed-in, heavily blurred background to fill the 9:16 frame."""
    # Scale to fill height, then crop center
    orig_w, orig_h = img.size
    scale = VIDEO_HEIGHT / float(orig_h)
    new_w = int(orig_w * scale)
    
    bg_img = img.resize((new_w, VIDEO_HEIGHT), Image.LANCZOS)
    # Center crop to 1080x1920
    left = (new_w - VIDEO_WIDTH) // 2
    bg_img = bg_img.crop((left, 0, left + VIDEO_WIDTH, VIDEO_HEIGHT))
    
    # Heavily blur
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=25))
    # Darken slightly
    bg_img = ImageOps.colorize(bg_img.convert('L'), black="black", white="#444444")
    
    return ImageClip(np.array(bg_img)).set_duration(duration)

def create_shake(clip, duration, intensity=15):
    """Adds a subtle high-frequency shake used in action recaps."""
    def shake_pos(t):
        if t < 0: return 'center'
        x = random.randint(-intensity, intensity)
        y = random.randint(-intensity, intensity)
        return (x, y)
    return clip.set_position(shake_pos)

def create_pro_segment(img, duration, index, text=""):
    """
    Constructs a sophisticated 9:16 layout:
    - Blurred Background
    - Main Panel Foreground
    - Continuous Movement (Ken Burns)
    - Optional 'Punch' Shakes for dramatic words
    """
    orig_w, orig_h = img.size
    
    # 1. Background
    bg_clip = create_background(img, duration)
    
    # 2. Foreground Panel
    # Fit width, centered
    scale_w = (VIDEO_WIDTH * 0.9) / float(orig_w) # 90% width for padding
    fw = int(VIDEO_WIDTH * 0.9)
    fh = int(orig_h * scale_w)
    
    fg_img = img.resize((fw, fh), Image.LANCZOS)
    
    # Dynamic Zoom Logic
    overscale = 1.1 + (random.random() * 0.1) # 1.1x to 1.2x zoom
    z_w, z_h = int(fw * overscale), int(fh * overscale)
    fg_img_zoomed = fg_img.resize((z_w, z_h), Image.LANCZOS)
    
    fg_clip = ImageClip(np.array(fg_img_zoomed)).set_duration(duration)
    
    # Random Movement Logic (The "Winning" Pan)
    move_type = index % 4
    cx, cy = (VIDEO_WIDTH - z_w) // 2, (VIDEO_HEIGHT - z_h) // 2
    dx, dy = (z_w - VIDEO_WIDTH) // 2, (z_h - VIDEO_HEIGHT) // 2
    
    if move_type == 0: # Slow Zoom In
        fg_clip = fg_clip.resize(lambda t: 1.0 + 0.08 * (t/duration))
    elif move_type == 1: # Pan Down
        fg_clip = fg_clip.set_position(lambda t: ('center', cy - dy + (2*dy*t/duration)))
    elif move_type == 2: # Pan Up
        fg_clip = fg_clip.set_position(lambda t: ('center', cy + dy - (2*dy*t/duration)))
    else: # Pan Right to Left
        fg_clip = fg_clip.set_position(lambda t: (cx + dx - (2*dx*t/duration), 'center'))

    # 3. Action Logic: Shakes on dramatic keywords
    dramatic_keywords = ['crash', 'halt', 'shock', 'freaking', 'screeches', 'goblin', 'announced', 'changed', 'ruined', 'apocalypse']
    has_drama = any(word in text.lower() for word in dramatic_keywords)
    
    if has_drama:
        fg_clip = create_shake(fg_clip, duration, intensity=20)
    
    # 4. Composite
    final_clip = CompositeVideoClip([bg_clip, fg_clip.set_position('center')], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    
    # 5. Transition: Flash or Crossfade
    if index % 5 == 0:
        # Action Flash
        flash = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(255,255,255), duration=0.1).set_opacity(0.4)
        final_clip = CompositeVideoClip([final_clip, flash.set_start(0)])
        
    return final_clip.crossfadein(0.2)

def split_panels_robustly(image_files):
    """Detects horizontal gaps to extract individual manga panels from strips."""
    all_panels = []
    print("  Deconstructing webtoon strips into individual panels...")
    for img_path in image_files:
        try:
            img = Image.open(img_path).convert("RGB")
            # Analyze brightness variance per row to find 'white' or 'black' gutters
            gray = img.convert('L')
            arr = np.array(gray)
            row_var = np.var(arr, axis=1)
            
            # Gutter = low variance row
            threshold = 4.0
            gutters = np.where(row_var < threshold)[0]
            
            if len(gutters) == 0:
                all_panels.append(img)
                continue
                
            borders = [0]
            for i in range(1, len(gutters)):
                if gutters[i] - gutters[i-1] > 25: # Min panel height
                    borders.append(gutters[i])
            borders.append(img.size[1])
            
            for i in range(len(borders)-1):
                h = borders[i+1] - borders[i]
                if h < 100: continue
                all_panels.append(img.crop((0, borders[i], img.size[0], borders[i+1])))
                
        except Exception as e:
            print(f"  Error processing {img_path}: {e}")
            
    return all_panels

def render_video(chapter, chapter_dir, audio_path, vtt_path, output_path, min_duration=0):
    print(f"\n[PRO-EDIT] Starting RECAP build for Chapter {chapter}")
    
    # 1. Gather Data
    image_files = sorted(glob.glob(os.path.join(chapter_dir, "*.*")))
    image_files = [f for f in image_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    audio = AudioFileClip(audio_path)
    subs = parse_vtt(vtt_path)
    
    if not subs:
        print("ERROR: No narrative synchronization data (VTT) found.")
        sys.exit(1)
        
    # 2. Panel Extraction
    panels = split_panels_robustly(image_files)
    print(f"  Extracted {len(panels)} unique panels.")
    
    # 3. Beat-Synced Narrative Mapping
    clips = []
    print("  Mapping panels to narrative beats (Subtitle Sync Mode)...")
    
    # We want to match visual changes to the spoken words in the VTT
    # If we have many panels, we can cycle through them faster
    # If we have few, we stretch them.
    
    panel_idx = 0
    for i, beat in enumerate(subs):
        duration = max(0.1, beat['end'] - beat['start'])
        
        # If the duration is long (> 3s), split into two panels for better pacing
        if duration > 3.0:
            half_dur = duration / 2.0
            for _ in range(2):
                img = panels[panel_idx % len(panels)]
                panel_idx += 1
                clip = create_pro_segment(img, half_dur, len(clips), text=beat['text'])
                clips.append(clip)
        else:
            img = panels[panel_idx % len(panels)]
            panel_idx += 1
            clip = create_pro_segment(img, duration, len(clips), text=beat['text'])
            clips.append(clip)
            
    # Ensure we cover the entire audio if VTT ends early
    total_rendered_dur = sum(c.duration for c in clips)
    if total_rendered_dur < audio.duration:
        remaining = audio.duration - total_rendered_dur
        if remaining > 0.1:
            img = panels[panel_idx % len(panels)]
            clip = create_pro_segment(img, remaining, len(clips))
            clips.append(clip)
            
    print(f"  Aggregating {len(clips)} beat-synced clips...")
    video_sequence = concatenate_videoclips(clips, method="compose")
    
    # Ensure minimum duration if specified
    if min_duration > 0 and video_sequence.duration < min_duration:
        num_repeats = int(np.ceil(min_duration / video_sequence.duration))
        print(f"  Stretching video to reach minimum duration of {min_duration}s...")
        video_sequence = concatenate_videoclips([video_sequence] * num_repeats)
        video_sequence = video_sequence.subclip(0, min_duration)

    # Final assembly
    if video_sequence.duration > audio.duration:
        # If we stretched, the audio should probably loop or stay silent?
        # Actually, if we stretch a short video to 15s, but audio is 1s, we should loop audio too.
        if audio.duration < video_sequence.duration:
             num_audio_repeats = int(np.ceil(video_sequence.duration / audio.duration))
             audio = vfx.loop(audio, duration=video_sequence.duration)
        
    final_video = video_sequence.set_audio(audio)
    
    # 4. Render with optimized settings for Shorts
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"  RENDERING RECAP REEL TO: {output_path}")
    
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        preset='fast',
        threads=4
    )
    
    print(f"\n[SUCCESS] Chapter {chapter} Recap is now a Pro Short.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--chapter-dir", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--vtt", required=False, default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-duration", type=float, default=0)
    args = parser.parse_args()
    
    vtt = args.vtt if args.vtt else args.audio.replace('.mp3', '.vtt')
    render_video(args.chapter, args.chapter_dir, args.audio, vtt, args.output, min_duration=args.min_duration)