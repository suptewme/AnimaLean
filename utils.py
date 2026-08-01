import os
import cv2
from PIL import Image
import json

def get_file_size(filepath):
    return os.path.getsize(filepath)

def get_video_info(filepath):
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    return {
        'fps': fps,
        'frames': frame_count,
        'width': width,
        'height': height,
        'duration': duration
    }

def create_output_folder(base_path):
    output_folder = os.path.join(base_path, 'сжатые')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def clean_temp_files(folder):
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith('_temp.jpg') or f.endswith('_temp.png'):
                os.remove(os.path.join(folder, f))

def get_filename_without_ext(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]
