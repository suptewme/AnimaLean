import cv2
import os
import json
import gzip
import base64
from PIL import Image
from io import BytesIO
import imageio
import numpy as np
from utils import get_video_info
from formats import (
    build_lottie_json, build_sprite_json, 
    build_css_animation, build_android_xml,
    build_swift_code, build_react_component
)

class GiftGenerator:
    def __init__(self):
        self.video_path = None
        self.frames = []
        self.sprite_path = None
        self.json_path = None
        self.output_format = 'tgs'
        self.frame_size = 128
        self.max_frames = 20
        self.delay = 50
        self.quality = 'minimal'
        self.output_folder = None
        self.filename = 'gift'

    def load_video(self, path):
        self.video_path = path
        self.filename = os.path.splitext(os.path.basename(path))[0]
        return get_video_info(path)

    def extract_frames(self):
        if not self.video_path:
            return False
        
        info = get_video_info(self.video_path)
        if not info:
            return False
        
        total_frames = info['frames']
        fps = info['fps']
        
        cap = cv2.VideoCapture(self.video_path)
        frames_list = []
        
        step = max(1, int(total_frames / self.max_frames))
        count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % step == 0:
                h, w = frame.shape[:2]
                aspect = w / h
                target_size = self.frame_size
                if w > h:
                    new_w = target_size
                    new_h = int(target_size / aspect)
                else:
                    new_h = target_size
                    new_w = int(target_size * aspect)
                
                frame = cv2.resize(frame, (new_w, new_h))
                
                if self.quality == 'minimal':
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame)
                    pil_img = pil_img.convert('P', palette=Image.ADAPTIVE, colors=64)
                    frame = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)
                
                frames_list.append(frame)
                
                if len(frames_list) >= self.max_frames:
                    break
            count += 1
        
        cap.release()
        self.frames = frames_list
        return len(self.frames) > 0

    def extract_frames_for_lottie(self):
        if not self.video_path:
            return False
        
        info = get_video_info(self.video_path)
        if not info:
            return False
        
        total_frames = info['frames']
        fps = info['fps']
        
        cap = cv2.VideoCapture(self.video_path)
        frames_list = []
        encoded_frames = []
        
        step = max(1, int(total_frames / self.max_frames))
        count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % step == 0:
                h, w = frame.shape[:2]
                aspect = w / h
                target_size = self.frame_size
                if w > h:
                    new_w = target_size
                    new_h = int(target_size / aspect)
                else:
                    new_h = target_size
                    new_w = int(target_size * aspect)
                
                frame = cv2.resize(frame, (new_w, new_h))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                if self.quality == 'minimal':
                    pil_img = pil_img.convert('P', palette=Image.ADAPTIVE, colors=64)
                    pil_img = pil_img.convert('RGB')
                
                buffered = BytesIO()
                pil_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                encoded_frames.append(img_str)
                frames_list.append(frame)
                
                if len(frames_list) >= self.max_frames:
                    break
            count += 1
        
        cap.release()
        self.frames = frames_list
        return encoded_frames

    def build_sprite(self):
        if not self.frames:
            return False
        
        cols = int(len(self.frames) ** 0.5)
        if cols * cols < len(self.frames):
            cols += 1
        rows = (len(self.frames) + cols - 1) // cols
        
        sprite_width = cols * self.frame_size
        sprite_height = rows * self.frame_size
        
        sprite_img = Image.new('RGBA', (sprite_width, sprite_height), (0, 0, 0, 0))
        
        for i, frame in enumerate(self.frames):
            row = i // cols
            col = i % cols
            x = col * self.frame_size
            y = row * self.frame_size
            
            h, w = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)
            
            if self.quality == 'minimal':
                pil_frame = pil_frame.convert('P', palette=Image.ADAPTIVE, colors=64)
                pil_frame = pil_frame.convert('RGB')
            
            new_img = Image.new('RGBA', (self.frame_size, self.frame_size), (0, 0, 0, 0))
            paste_x = (self.frame_size - w) // 2
            paste_y = (self.frame_size - h) // 2
            if pil_frame.mode != 'RGBA':
                pil_frame = pil_frame.convert('RGBA')
            new_img.paste(pil_frame, (paste_x, paste_y))
            sprite_img.paste(new_img, (x, y))
        
        output_folder = self.output_folder or 'сжатые'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        sprite_path = os.path.join(output_folder, f'{self.filename}_sprite.png')
        
        if self.quality == 'minimal':
            sprite_img = sprite_img.convert('P', palette=Image.ADAPTIVE, colors=128)
            sprite_img = sprite_img.convert('RGBA')
        
        sprite_img.save(sprite_path, optimize=True, compress_level=9)
        self.sprite_path = sprite_path
        return True

    def generate_json(self, format_type='tgs'):
        if not self.frames:
            return None
        
        cols = int(len(self.frames) ** 0.5)
        if cols * cols < len(self.frames):
            cols += 1
        rows = (len(self.frames) + cols - 1) // cols
        
        output_folder = self.output_folder or 'сжатые'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        json_data = None
        json_path = None
        
        if format_type == 'tgs':
            encoded = self.extract_frames_for_lottie()
            if not encoded:
                return None
            lottie_data = build_lottie_json(
                encoded, 
                self.frame_size, 
                self.frame_size, 
                1000 // self.delay
            )
            json_path = os.path.join(output_folder, f'{self.filename}.tgs')
            with open(json_path, 'wb') as f:
                json_str = json.dumps(lottie_data, separators=(',', ':'))
                compressed = gzip.compress(json_str.encode('utf-8'), compresslevel=9)
                f.write(compressed)
        
        elif format_type == 'lottie':
            encoded = self.extract_frames_for_lottie()
            if not encoded:
                return None
            lottie_data = build_lottie_json(
                encoded,
                self.frame_size,
                self.frame_size,
                1000 // self.delay
            )
            json_path = os.path.join(output_folder, f'{self.filename}.json')
            with open(json_path, 'w') as f:
                json.dump(lottie_data, f, separators=(',', ':'))
        
        elif format_type == 'spritesheet':
            self.build_sprite()
            json_data = build_sprite_json(
                self.frames, cols, rows, 
                self.frame_size, self.frame_size, 
                self.delay
            )
            json_path = os.path.join(output_folder, f'{self.filename}_data.json')
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
        
        elif format_type == 'css':
            self.build_sprite()
            css_data = build_css_animation(
                self.frames, cols, rows,
                self.frame_size, self.frame_size,
                len(self.frames) * self.delay
            )
            json_path = os.path.join(output_folder, f'{self.filename}.css')
            with open(json_path, 'w') as f:
                f.write(css_data)
            json_data = {'css_file': json_path}
        
        elif format_type == 'android':
            self.build_sprite()
            xml_data = build_android_xml(len(self.frames), self.delay)
            json_path = os.path.join(output_folder, f'{self.filename}.xml')
            with open(json_path, 'w') as f:
                f.write(xml_data)
            json_data = {'xml_file': json_path}
        
        elif format_type == 'ios':
            self.build_sprite()
            swift_data = build_swift_code(len(self.frames), self.frame_size, self.frame_size, self.delay)
            json_path = os.path.join(output_folder, f'{self.filename}.swift')
            with open(json_path, 'w') as f:
                f.write(swift_data)
            json_data = {'swift_file': json_path}
        
        elif format_type == 'react':
            self.build_sprite()
            jsx_data = build_react_component(len(self.frames), self.frame_size, self.frame_size, self.delay)
            json_path = os.path.join(output_folder, f'{self.filename}.jsx')
            with open(json_path, 'w') as f:
                f.write(jsx_data)
            json_data = {'jsx_file': json_path}
        
        self.json_path = json_path
        return json_data

    def get_result_size(self):
        total = 0
        if self.sprite_path and os.path.exists(self.sprite_path):
            total += os.path.getsize(self.sprite_path)
        if self.json_path and os.path.exists(self.json_path):
            total += os.path.getsize(self.json_path)
        return total

    def set_output_folder(self, folder):
        self.output_folder = folder
        if not os.path.exists(folder):
            os.makedirs(folder)

    def set_format(self, format_type):
        self.output_format = format_type

    def set_frame_size(self, size):
        self.frame_size = size

    def set_max_frames(self, max_frames):
        self.max_frames = max_frames

    def set_delay(self, delay):
        self.delay = delay

    def set_quality(self, quality):
        self.quality = quality