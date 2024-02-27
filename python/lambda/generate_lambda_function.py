import json
import boto3
import os
import mimetypes
import base64
from moviepy.editor import *

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = "sam-app-s3uploadbucket-qkgqfgtltuzq"
    
    bodyJson = json.loads(event['body'])
    chosenWords = bodyJson['chosenWords']
    sessionKey = str(bodyJson['sessionKey'])
    isVideo = bodyJson['isVideo']
    audioOnly = bodyJson['audioOnly']
    
    # Determine source and final file paths
    sourcePath = ''
    finalPath = ''
    if isVideo and not audioOnly:
        sourcePath = '/tmp/' + sessionKey + ".mp4"
        finalPath = '/tmp/' + sessionKey + "final.mp4"
        download_file_from_s3(bucket, sessionKey, sourcePath)
        generateVideo(sessionKey, chosenWords, sourcePath)
    else:
        sourcePath = '/tmp/' + sessionKey + ".wav"
        finalPath = '/tmp/' + sessionKey + "final.wav"
        download_file_from_s3(bucket, sessionKey, sourcePath)
        generateAudio(sessionKey, chosenWords, sourcePath)
    
    # Read the MP4 or WAV file content from the file path
    file_content = read_file_content(finalPath)

    # Encode the file content as base64
    encoded_file_content = base64.b64encode(file_content).decode('utf-8')
    
    # Set response headers
    headers = {
        'Content-Type': mimetypes.guess_type(finalPath)[0],  # Change to 'video/mp4' for MP4 files
        'Content-Disposition': 'attachment; filename="output.wav"'  # Adjust filename as needed
    }

    # Return the HTTP response
    return {
        'statusCode': 200,
        'headers': headers,
        'body': encoded_file_content,
        'isBase64Encoded': True
    }
    
def read_file_content(file_path):
    with open(file_path, 'rb') as file:
        return file.read()

# Takes json word objects and appends sublcips into video
def generateVideo(sessionKey, wordsJson, sourceVideoPath):
    words = json.loads(wordsJson)
    subclips = []
    
    if os.path.exists(sourceVideoPath):
        print('source path exists')
    else:
        print('source not downloaded!')
    
    fullVideoClip = VideoFileClip(sourceVideoPath)

    for i in range(len(words)):
        subclips.append(
            fullVideoClip.subclip(float(words[i]["id"]), float(words[i]["end"]))
        )
    concatClip = concatenate_videoclips(subclips)
    
    concatClip.write_videofile('/tmp/' + sessionKey + "final.mp4", temp_audiofile='/tmp/tempaudio.mp3')
    
# Takes json word objects and appends sublcips into audio
def generateAudio(sessionKey, wordsJson, sourceAudioPath):
    words = json.loads(wordsJson)
    subclips = []
    
    fullAudioClip = AudioFileClip(sourceAudioPath)

    for i in range(len(words)):
        subclips.append(
            fullAudioClip.subclip(float(words[i]["id"]), float(words[i]["end"]))
        )

    concatClip = concatenate_audioclips(subclips)
    concatClip.write_audiofile(
        '/tmp/' + sessionKey + "final.wav", codec="pcm_s16le"
    )
    
# Downloads a file from S3 to local storage
def download_file_from_s3(bucket_name, object_key, local_file_path):
    # Download the file from S3
    s3.download_file(bucket_name, object_key, local_file_path)