import asyncio
import websockets
from moviepy.editor import *
import json
from AudioAnalyzer import AudioAnalyzer

async def echo(websocket, path):
    async for message in websocket:
        if type(message) == bytes:
            with open('sentencemixing/src/python/audio.wav', 'wb') as f:
                f.write(message)
        
            audioAnalyzer = AudioAnalyzer(
                "/Users/stephenswetonic/Documents/projects/sentencemixing/sentencemixing/src/python/vosk-model-small-en-us-0.15", 
                "sentencemixing/src/python/audio.wav")
            audioAnalyzer.analyze()
            await websocket.send(audioAnalyzer.getWordsJson())
        elif message[0] == '[':
            print(message)
            processAudio(message)
            processedClip = open("sentencemixing/src/python/concat.wav", 'rb')
            #processedClip = bytes(processedClip)
            await websocket.send(processedClip)
        else:
            await websocket.send(message)

def processAudio(wordsJson):
    words = json.loads(wordsJson)
    subclips = []
    fullAudioClip = AudioFileClip("sentencemixing/src/python/audio.wav")

    for i in range(len(words)):
        subclips.append(fullAudioClip.subclip(words[i]['id'], words[i]['end']))

    concatclip = concatenate_audioclips(subclips)
    concatclip.write_audiofile('sentencemixing/src/python/concat.wav')


asyncio.get_event_loop().run_until_complete(
    websockets.serve(echo, 'localhost', 8000, max_size=2**40))
asyncio.get_event_loop().run_forever()