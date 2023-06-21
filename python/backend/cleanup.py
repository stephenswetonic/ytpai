import os, time
import shutil

storagePath = "/Users/stephenswetonic/Documents/projects/ytpai/python/backend/storage"
cutoffTime = int(time.time() * 1000) - 3_600_000

if os.path.exists(storagePath):
    dirs = os.listdir(storagePath)
    for dir in dirs:
        if dir[0] != '.' and int(dir) < cutoffTime:
            print("deleted directory", dir)
            shutil.rmtree((storagePath + '/' + dir))