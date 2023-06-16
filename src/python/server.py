import falcon
import os
import mimetypes
from wsgiref.simple_server import make_server
from falcon_multipart.middleware import MultipartMiddleware
import json
from moviepy.editor import *
from AudioAnalyzer import AudioAnalyzer

class Source(object):
    def on_put(self, req, resp):
        sessionKey = req.get_param("key")
        
        isVideo = req.get_param("isVideo")
        isVideo = True if isVideo == "true" else False

        fileObj = req.get_param("file")
        raw = fileObj.file.read()

        path = "src/python/storage/" + sessionKey
        wordsJson = ""
        if not os.path.exists(path):
            os.makedirs(path)

        if isVideo:
            #save video
            with open((path + "/video.mp4"), 'wb') as f:
                f.write(raw)
            fullClip = VideoFileClip((path + "/video.mp4"))
            fullClip.audio.write_audiofile((path + "/audio.wav"), ffmpeg_params=["-ac", "1"], codec="pcm_s16le")
            wordsJson = processAudio(sessionKey)
        else:
            #save audio
            with open((path + "/audio.wav"), 'wb') as f:
                f.write(raw)
            wordsJson = processAudio(sessionKey)
        
        resp.text = json.dumps({'wordsJson' : wordsJson})
        resp.status = falcon.HTTP_200

class SourceVideo(object):
    def on_put(self, req, resp):
        resp.status = falcon.HTTP_200

class Generate(object):
    def on_put(self, req, resp):
        mediaObj = req.get_media()
        sessionKey = mediaObj.get("sessionKey")
        chosenWords = mediaObj.get("chosenWords")
        isVideo = mediaObj.get("isVideo")
        audioOnly = mediaObj.get("audioOnly")

        path = ""
        if isVideo and not audioOnly:
            path = "src/python/storage/" + str(sessionKey) + "/concat.mp4"
            generateVideo(sessionKey, chosenWords)
        else:
            path = "src/python/storage/" + str(sessionKey) + "/concat.wav"
            generateAudio(sessionKey, chosenWords)

        
        generatedFile = open(path, "rb")
        content_length = os.path.getsize(path)

        resp.content_type = mimetypes.guess_type(path)[0]
        resp.stream = generatedFile
        resp.content_length = content_length
        resp.status = falcon.HTTP_200

def processAudio(sessionKey):
    audioFile = "src/python/storage/" + str(sessionKey) + "/audio.wav"
    audioAnalyzer = AudioAnalyzer("/Users/stephenswetonic/Documents/projects/sentencemixing/sentencemixing/src/python/models/vosk-model-small-en-us-0.15", audioFile)
    audioAnalyzer.analyze()
    return audioAnalyzer.getWordsJson()

def generateVideo(sessionKey, wordsJson):
    words = json.loads(wordsJson)
    subclips = []
    fullVideoClip = VideoFileClip("src/python/storage/" + str(sessionKey) + "/video.mp4")

    for i in range(len(words)):
        subclips.append(fullVideoClip.subclip(float(words[i]["id"]), float(words[i]["end"])))
    concatClip = concatenate_videoclips(subclips)
    concatClip.write_videofile("src/python/storage/" + str(sessionKey) + "/concat.mp4")

def generateAudio(sessionKey, wordsJson):
    words = json.loads(wordsJson)
    subclips = []
    fullAudioClip = AudioFileClip("src/python/storage/" + str(sessionKey) + "/audio.wav")

    for i in range(len(words)):
        subclips.append(fullAudioClip.subclip(float(words[i]['id']), float(words[i]['end'])))

    concatClip = concatenate_audioclips(subclips)
    concatClip.write_audiofile('src/python/storage/' + str(sessionKey) + "/concat.wav", codec="pcm_s16le")



app = falcon.App(middleware=[falcon.CORSMiddleware(
    allow_origins='*', allow_credentials='*'), MultipartMiddleware()])
app.add_route("/source", Source())
app.add_route("/sourcevideo", SourceVideo())
app.add_route("/generate", Generate())

if __name__ == '__main__':
    with make_server('', 8000, app) as httpd:
        print('Serving on port 8000...')

        # Serve until process is killed
        httpd.serve_forever()