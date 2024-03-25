import json

# Helps convert words to json
class WordEncoder(json.JSONEncoder):
    def default(self, obj):
            return {"id" : str(obj.start), "end" : str(obj.end), "word" : obj.word}