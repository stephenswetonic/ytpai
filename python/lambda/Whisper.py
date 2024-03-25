import whisper_timestamped as whisper

audio = whisper.load_audio("python/lambda/file.wav")

model = whisper.load_model("base", device="cpu")

# list of segments, list of words, {text, start, end}
result = whisper.transcribe(model, audio, language="en")
print(result)