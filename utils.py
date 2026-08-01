import os
import cv2
from PIL import Image
import json
import numpy as np

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

def generate_palette(frames, max_colors=10):
    palette = []
    try:
        for frame in frames:
            if len(frame.shape) == 3:
                if frame.shape[2] == 3:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGBA)
                pil_img = Image.fromarray(frame_rgb)
                colors = pil_img.getcolors(maxcolors=256)
                if colors:
                    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                    for count, color in sorted_colors[:max_colors]:
                        if len(color) == 3:
                            hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                        else:
                            hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                        if hex_color not in palette:
                            palette.append(hex_color)
                if len(palette) >= max_colors:
                    break
    except:
        pass
    return palette[:max_colors]
