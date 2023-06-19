import falcon
import os
import mimetypes
from wsgiref.simple_server import make_server
from falcon_multipart.middleware import MultipartMiddleware
import json
from moviepy.editor import *
from AudioAnalyzer import AudioAnalyzer

storagePath = "storage/"
modelPath = "models/vosk-model-small-en-us-0.15"

# Falcon resource for recieving audio/video and processing into json list of words
# sessionKey - Unix timestamp from client. Used to name folder for files
# isVideo - boolean string
# Response - json list of words
class Source(object):
    def on_put(self, req, resp):
        sessionKey = req.get_param("key")
        
        isVideo = req.get_param("isVideo")
        isVideo = True if isVideo == "true" else False

        fileObj = req.get_param("file")
        raw = fileObj.file.read()

        path = storagePath + sessionKey
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

# Falcon resource for generating audio/video output
# sessionKey - Unix timestamp from client. Used to name folder for files
# isVideo - boolean string
# audioOnly - boolean string, true for audio, true or false for video
# chosenWords - json list of word objects: {"id" : String, "end" : String, "word" : String}
# "id" alias for start time
# Response - wav audio or mp4 video
class Generate(object):
    def on_put(self, req, resp):
        mediaObj = req.get_media()
        sessionKey = mediaObj.get("sessionKey")
        chosenWords = mediaObj.get("chosenWords")
        isVideo = mediaObj.get("isVideo")
        audioOnly = mediaObj.get("audioOnly")

        path = ""
        if isVideo and not audioOnly:
            path = storagePath + str(sessionKey) + "/concat.mp4"
            generateVideo(sessionKey, chosenWords)
        else:
            path = storagePath + str(sessionKey) + "/concat.wav"
            generateAudio(sessionKey, chosenWords)

        
        generatedFile = open(path, "rb")
        content_length = os.path.getsize(path)

        resp.content_type = mimetypes.guess_type(path)[0]
        resp.stream = generatedFile
        resp.content_length = content_length
        resp.status = falcon.HTTP_200

# Takes audio file and returns json list of word objects
def processAudio(sessionKey):
    audioFile = storagePath + str(sessionKey) + "/audio.wav"
    audioAnalyzer = AudioAnalyzer(modelPath, audioFile)
    audioAnalyzer.analyze()
    return audioAnalyzer.getWordsJson()

# Takes json word objects and appends sublcips into video
def generateVideo(sessionKey, wordsJson):
    words = json.loads(wordsJson)
    subclips = []
    fullVideoClip = VideoFileClip(storagePath + str(sessionKey) + "/video.mp4")

    for i in range(len(words)):
        subclips.append(fullVideoClip.subclip(float(words[i]["id"]), float(words[i]["end"])))
    concatClip = concatenate_videoclips(subclips)
    concatClip.write_videofile(storagePath + str(sessionKey) + "/concat.mp4")

# Takes json word objects and appends sublcips into audio
def generateAudio(sessionKey, wordsJson):
    words = json.loads(wordsJson)
    subclips = []
    fullAudioClip = AudioFileClip(storagePath + str(sessionKey) + "/audio.wav")

    for i in range(len(words)):
        subclips.append(fullAudioClip.subclip(float(words[i]['id']), float(words[i]['end'])))

    concatClip = concatenate_audioclips(subclips)
    concatClip.write_audiofile(storagePath + str(sessionKey) + "/concat.wav", codec="pcm_s16le")

# Falcon app
app = application = falcon.App(middleware=[falcon.CORSMiddleware(
    allow_origins='*', allow_credentials='*'), MultipartMiddleware()])
app.add_route("/source", Source())
app.add_route("/generate", Generate())

