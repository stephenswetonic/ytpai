import vosk
from moviepy import *

import boto3
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    print(event)


