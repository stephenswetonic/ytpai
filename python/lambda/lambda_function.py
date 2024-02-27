from vosk import Model, KaldiRecognizer, SetLogLevel
from moviepy.editor import *
from AudioAnalyzer import AudioAnalyzer
import boto3
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = "sam-app-s3uploadbucket-qkgqfgtltuzq"
    
    bodyJson = json.loads(event['body'])

    sessionKey = str(bodyJson['sessionKey'])
    isVideo = bodyJson['isVideo']
    audioOnly = bodyJson['audioOnly']
    useBigModel = bodyJson['useBigModel']
    lang = bodyJson['lang']
    
    # Create temp file path
    tempSourcePath = ''
    if isVideo:
        tempSourcePath = '/tmp/' + sessionKey + '.mp4'
    else:
        tempSourcePath = '/tmp/' + sessionKey + '.wav'
        
    # Download from S3
    try:
        download_file_from_s3(bucket, sessionKey, tempSourcePath)
    except Exception as e:
        print(f"Error occurred while downloading source.. {e}")
        
    if isVideo:
        # Open video and save its audio
        fullClip = VideoFileClip((tempSourcePath))
        fullClip.audio.write_audiofile(
            ('/tmp/' + sessionKey + ".wav"), ffmpeg_params=["-ac", "1"], codec="pcm_s16le"
        )
    
    # Get the vosk model from s3
    tempModelDir = '/tmp/model/'
    try:
        download_objects_from_s3('swetonic-vosk-models', 'vosk-model-small-en-us-0.15/', tempModelDir)
    except Exception as e:
        print("Error downloading model...")
        raise e
    
    try:
        # Process the audio
        wordsJson = processAudio(sessionKey, useBigModel, lang)
        print(wordsJson)
    
        # Return a success response
        return {
            'statusCode': 200,
            'body': wordsJson
        }
    except Exception as e:
        print("Error processing audio...")
        return {
            'statusCode': 500,
            'error': str(e)
        }
        
def download_file_from_s3(bucket_name, object_key, local_file_path):
    # Download the file from S3
    s3.download_file(bucket_name, object_key, local_file_path)
    
def download_objects_from_s3(bucket_name, prefix, local_dir):
    # List all objects in the bucket with the given prefix (folder)
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                # Extract the key (object path) from the object
                key = obj['Key']
                
                # Skip if the key is the prefix (folder itself)
                if key == prefix:
                    continue
                
                # Construct the local file path to download the object
                local_file_path = os.path.join(local_dir, os.path.relpath(key, prefix))
                
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download the object
                s3.download_file(bucket_name, key, local_file_path)
    
# TODO support all models
# Takes audio file and returns json list of word objects
def processAudio(sessionKey, useBigModel, lang):
    audioFile = '/tmp/' + str(sessionKey) + ".wav"
    modelPath = '/tmp/model/'

    # modelPath = ""
    # if lang == "en":
    #     modelPath = bigModelPath if useBigModel else smallModelPath
    # elif lang == "es":
    #     modelPath = esModelPath
    # elif lang == "fr":
    #     modelPath = frModelPath
    # elif lang == "ru":
    #     modelPath = ruModelPath
    # elif lang == "de":
    #     modelPath = deModelPath

    audioAnalyzer = AudioAnalyzer(modelPath, audioFile)
    audioAnalyzer.analyze()
    return audioAnalyzer.getWordsJson()