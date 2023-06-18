import wave
import json
from Word import Word
from WordEncoder import WordEncoder
from vosk import Model, KaldiRecognizer, SetLogLevel

class AudioAnalyzer:

    def __init__(self, model_path, audio_filename) -> None:
        self.model_path : str = model_path
        self.audio_filename : str = audio_filename
        self.wordsJson : str = ''

    def analyze(self):
        model = Model(self.model_path)
        wf = wave.open(self.audio_filename, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        # get the list of JSON dictionaries
        results = []
        # recognize speech using vosk model
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part_result = json.loads(rec.Result())
                results.append(part_result)
        part_result = json.loads(rec.FinalResult())
        results.append(part_result)

        # convert list of JSON dictionaries to list of 'Word' objects
        list_of_words = []
        for sentence in results:
            if len(sentence) == 1:
                # sometimes there are bugs in recognition 
                # and it returns an empty dictionary
                # {'text': ''}
                continue
            for obj in sentence['result']:
                w = Word(obj)  # create custom Word object
                list_of_words.append(w)  # and add it to list

        wf.close()  # close audiofile
        self.wordsJson = json.dumps(list_of_words, cls=WordEncoder)
    
    def getWordsJson(self):
        return self.wordsJson

# model_path = "/Users/stephenswetonic/Documents/projects/sentencemixing/sentencemixing/src/python/vosk-model-en-us-0.22"
# audio_filename = "/Users/stephenswetonic/Documents/projects/sentencemixing/sentencemixing/src/python/phil.wav"