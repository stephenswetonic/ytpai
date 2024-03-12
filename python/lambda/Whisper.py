import whisper_timestamped as whisper

audio = whisper.load_audio("python/lambda/file.wav")

model = whisper.load_model("base", device="cpu")

result = whisper.transcribe(model, audio, language="en")

import json
print(json.dumps(result, indent = 2, ensure_ascii = False))