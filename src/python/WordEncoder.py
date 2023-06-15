import json

class WordEncoder(json.JSONEncoder):
    def default(self, obj):
            return {"id" : obj.start, "end" : obj.end, "word" : obj.word}