import sys
from google.cloud import texttospeech

def text_to_speech(text, output_file):
    """Synthesizes speech from the input string of text or ssml."""
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice name must match the language code.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Neural2-D",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.05,
        pitch=-1.5,
        volume_gain_db=2.0
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tts.py <input_text_file> <output_mp3_file>")
        sys.exit(1)
        
    text_file = sys.argv[1]
    output_mp3 = sys.argv[2]
    
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
        
    text_to_speech(text, output_mp3)
