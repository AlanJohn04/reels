import os
import sys
import argparse
import subprocess

def generate_local_audio(text_path, output_mp3, output_vtt):
    print(f"Generating audio from {text_path} with edge-tts...")
    
    # We use Christopher (deep American natural male voice) often used in recaps
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", "en-US-ChristopherNeural", 
        "--rate", "+10%", # Fast pace for shorts/reels
        "-f", text_path,
        "--write-media", output_mp3,
        "--write-subtitles", output_vtt
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Audio and VTT generation complete.")
    except Exception as e:
        print(f"Error running edge-tts: {e}")
        # Fallback to python TTS if edge-tts fails?
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--output-vtt", required=True)
    args = parser.parse_args()
    generate_local_audio(args.text_file, args.output_file, args.output_vtt)
