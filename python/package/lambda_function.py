import vosk
from moviepy import *

import boto3
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Define the bucket name and object key
    bucket_name = 'your-bucket-name'
    object_key = 'path/to/your/file.txt'
    
    # Download the file from S3 to the local /tmp directory
    local_file_path = '/tmp/file.txt'
    s3.download_file(bucket_name, object_key, local_file_path)
    
    # Pass the local file path to your Python function
    result = process_file(local_file_path)
    
    return {
        'statusCode': 200,
        'body': result
    }

def process_file(file_path):
    # Your Python function that expects a file path
    with open(file_path, 'r') as file:
        content = file.read()
        # Do something with the file content
        return content
