"""
plot coordinates on video from images with OpenCV

Olivier Friard 2020-2021
"""

import os
import cv2
import sys
import pandas as pd
import numpy as np
import json
import pathlib
import sys

TSV_FILE = sys.argv[1]
IMAGES_DIR = sys.argv[2]
VIDEO_OUTPUT_PATH = sys.argv[3]

MASK = "*.jpg"

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
MAROON = (128, 0, 0)
TEAL = (0, 128, 128)
PURPLE = (128, 0, 128)
WHITE = (255, 255, 255)

drawing_thickness = 1
codec = 'mp4v'

nf = 30000

xy = pd.read_csv(TSV_FILE, sep='\t', header=None, index_col=0)
xy.columns = [ "x", "y"]
print(xy)

fourcc = cv2.VideoWriter_fourcc(*codec)
output_framesize = (1280, 720)  # (1920, 1080)
out = cv2.VideoWriter(filename = VIDEO_OUTPUT_PATH, fourcc = fourcc, fps = 25, frameSize = output_framesize, isColor = True)

count = 0
mem_traj = []
mem_x, mem_y = 0, 0
nb_images = len(list(pathlib.Path(IMAGES_DIR).glob(MASK)))

for idx, image_file_path in enumerate(sorted(pathlib.Path(IMAGES_DIR).glob(MASK))):

    image = cv2.imread(str(image_file_path))
    print(f"{idx + 1}/{nb_images}")

    if image_file_path.name not in xy.index:
        print(f"{image_file_path.name} not in index")
        continue

    x, y = xy.loc[image_file_path.name,]
    print(x,y)

    if output_framesize == (1920, 1080):
        x = int(x * 1920/1280)
        y = int(y * 1920/1280)


    if len(mem_traj) >= 2:
        print("red line")
        for memxy1, memxy2 in zip(mem_traj, mem_traj[1:]):
            cv2.line(image,
                (memxy1[0], memxy1[1]), (memxy2[0], memxy2[1]),
                    color=RED,
                    thickness=drawing_thickness,
                    lineType=8
                    )
    mem_traj.append((x, y))

    mem_x, mem_y = x, y

    out.write(image)


out.release()

print(f"{VIDEO_OUTPUT_PATH} done")
