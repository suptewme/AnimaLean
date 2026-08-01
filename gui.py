import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import json
import time
from PIL import Image, ImageTk
import cv2
import numpy as np
from core import GiftGenerator
from utils import get_filename_without_ext, get_video_info

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

SETTINGS_FILE = "settings.json"

class JSONPackApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AnimaLean — Конвертер анимаций")
        self.geometry("1000x1150")
        self.minsize(900, 1050)
        
        self.generator = GiftGenerator()
        self.file_list = []
        self.is_processing = False
        self.start_time = 0
        self.preview_height = 300
        
        self.target_fps = 30
        self.target_resolution = 512
        self.sprite_grid_size = 64
        self.sync_settings = False
        self.advanced_mode = False
        
        self.is_playing = False
        self.is_paused = False
        self.current_frame_pos = 0
        self.total_frames = 0
        self.fps = 0
        self.video_duration = 0
        self.video_cap = None
        self.current_video_path = None
        self.playback_speed = 1.0
        self.speed_check_var = ctk.StringVar(value="off")
        self._updater_id = None
        
        self.settings = self.load_settings()
        self.setup_ui()
        self.apply_settings()
        
    def load_settings(self):
        default = {
            "output_folder": os.path.join(os.getcwd(), "сжатые"),
            "filename": "анимация",
            "format": "Telegram Style (TGS, Flutter)",
            "frame_size": 128,
            "max_frames": 20,
            "delay": 50,
            "quality": "minimal",
            "window_width": 1000,
            "window_height": 1150,
            "target_fps": 30,
            "target_resolution": 512,
            "sprite_grid_size": 64,
            "sync_settings": False,
            "advanced_mode": False
        }
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            return default
        except:
            return default
    
    def save_settings(self):
        try:
            self.settings["output_folder"] = self.folder_entry.get()
            self.settings["filename"] = self.name_entry.get()
            self.settings["format"] = self.format_menu.get()
            self.settings["frame_size"] = int(self.size_slider.get())
            self.settings["max_frames"] = int(self.frames_slider.get())
            self.settings["delay"] = int(self.delay_slider.get())
            self.settings["quality"] = self.quality_var.get()
            self.settings["window_width"] = self.winfo_width()
            self.settings["window_height"] = self.winfo_height()
            self.settings["target_fps"] = int(self.fps_slider.get())
            self.settings["target_resolution"] = int(self.res_slider.get())
            self.settings["sprite_grid_size"] = int(self.grid_slider.get())
            self.settings["sync_settings"] = self.sync_var.get() == "on"
            self.settings["advanced_mode"] = self.advanced_var.get() == "on"
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def apply_settings(self):
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, self.settings.get("output_folder", os.path.join(os.getcwd(), "сжатые")))
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.settings.get("filename", "анимация"))
        self.format_menu.set(self.settings.get("format", "Telegram Style (TGS, Flutter)"))
        self.size_slider.set(self.settings.get("frame_size", 128))
        self.size_label.configure(text=f"{self.settings.get('frame_size', 128)}px")
        self.frames_slider.set(self.settings.get("max_frames", 20))
        self.frames_label.configure(text=str(self.settings.get("max_frames", 20)))
        self.delay_slider.set(self.settings.get("delay", 50))
        self.delay_label.configure(text=f"{self.settings.get('delay', 50)}мс")
        self.quality_var.set(self.settings.get("quality", "minimal"))
        self.fps_slider.set(self.settings.get("target_fps", 30))
        self.fps_label.configure(text=f"{self.settings.get('target_fps', 30)} FPS")
        self.res_slider.set(self.settings.get("target_resolution", 512))
        self.res_label.configure(text=f"{self.settings.get('target_resolution', 512)}px")
        self.grid_slider.set(self.settings.get("sprite_grid_size", 64))
        self.grid_label.configure(text=f"{self.settings.get('sprite_grid_size', 64)}px")
        self.sync_var.set("on" if self.settings.get("sync_settings", False) else "off")
        self.advanced_var.set("on" if self.settings.get("advanced_mode", False) else "off")
        self.toggle_advanced()
        self.geometry(f"{self.settings.get('window_width', 1000)}x{self.settings.get('window_height', 1150)}")
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(main_frame, text="AnimaLean — Конвертер анимаций", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, pady=(0, 15), sticky="w")
        
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        self.file_list_label = ctk.CTkLabel(file_frame, text="Загружено файлов: 0", font=ctk.CTkFont(size=14))
        self.file_list_label.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(5, 0))
        
        file_btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_btn_frame.grid(row=1, column=0, pady=(5, 5), sticky="ew")
        file_btn_frame.grid_columnconfigure(0, weight=0)
        file_btn_frame.grid_columnconfigure(1, weight=0)
        file_btn_frame.grid_columnconfigure(2, weight=1)
        
        self.select_btn = ctk.CTkButton(file_btn_frame, text="Добавить файлы", command=self.select_files, fg_color="#D0D0D0", text_color="#1A1A1A", width=120)
        self.select_btn.grid(row=0, column=0, padx=(10, 10), sticky="w")
        
        self.clear_btn = ctk.CTkButton(file_btn_frame, text="Очистить", command=self.clear_files, fg_color="#D0D0D0", text_color="#FF6B6B", width=100)
        self.clear_btn.grid(row=0, column=1, padx=(0, 10), sticky="w")
        
        self.files_container = ctk.CTkFrame(file_frame, fg_color="#2A2A2A", corner_radius=6)
        self.files_container.grid(row=2, column=0, pady=(5, 5), sticky="ew")
        self.files_container.grid_columnconfigure(0, weight=1)
        
        self.files_scrollable = ctk.CTkScrollableFrame(self.files_container, fg_color="#2A2A2A", height=80)
        self.files_scrollable.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.load_progress_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        self.load_progress_frame.grid(row=3, column=0, pady=(5, 0), sticky="ew")
        self.load_progress_frame.grid_columnconfigure(0, weight=1)
        
        self.load_progress_bar = ctk.CTkProgressBar(self.load_progress_frame, height=10)
        self.load_progress_bar.grid(row=0, column=0, sticky="ew", padx=(10, 10))
        self.load_progress_bar.set(0)
        
        self.load_progress_label = ctk.CTkLabel(self.load_progress_frame, text="Загрузка: 0%", width=80)
        self.load_progress_label.grid(row=0, column=1)
        self.load_progress_frame.grid_remove()
        
        self.file_buttons = []
        self.update_files_display()
        
        self.video_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.video_container.grid(row=2, column=0, pady=(0, 10), sticky="ew")
        self.video_container.grid_columnconfigure(0, weight=1)
        
        self.preview_frame = ctk.CTkFrame(self.video_container, fg_color="#111111", corner_radius=8)
        self.preview_frame.grid(row=0, column=0, sticky="ew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Превью", fg_color="#111111", corner_radius=8, height=self.preview_height)
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        
        self.resize_handle = ctk.CTkButton(self.video_container, text="═", command=self.toggle_resize, fg_color="#2A2A2A", text_color="#888888", height=20, width=40)
        self.resize_handle.grid(row=1, column=0, pady=(5, 0))
        
        controls_row = ctk.CTkFrame(self.video_container, fg_color="transparent")
        controls_row.grid(row=2, column=0, pady=(10, 0), sticky="ew")
        controls_row.grid_columnconfigure(0, weight=1)
        
        left = ctk.CTkFrame(controls_row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        
        self.play_btn = ctk.CTkButton(left, text="▶", command=self.toggle_play, fg_color="#D0D0D0", text_color="#1A1A1A", width=40, height=30)
        self.play_btn.grid(row=0, column=0, padx=(0, 5))
        self.pause_btn = ctk.CTkButton(left, text="⏸", command=self.toggle_pause, fg_color="#D0D0D0", text_color="#1A1A1A", width=40, height=30)
        self.pause_btn.grid(row=0, column=1, padx=(0, 10))
        self.speed_check = ctk.CTkCheckBox(left, text="Ускорить", variable=self.speed_check_var, onvalue="on", offvalue="off", command=self.toggle_speed, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.speed_check.grid(row=0, column=2, padx=(0, 10))
        self.speed_slider = ctk.CTkSlider(left, from_=1.0, to=100.0, command=self.on_speed_change, number_of_steps=99, width=120)
        self.speed_slider.grid(row=0, column=3, padx=(0, 10))
        self.speed_slider.set(1.0)
        self.speed_label = ctk.CTkLabel(left, text="1.0x", width=40)
        self.speed_label.grid(row=0, column=4)
        
        timeline_wrap = ctk.CTkFrame(self.video_container, fg_color="transparent")
        timeline_wrap.grid(row=3, column=0, pady=(10, 0), sticky="ew")
        timeline_wrap.grid_columnconfigure(0, weight=1)
        timeline_wrap.grid_columnconfigure(1, weight=0)
        
        self.timeline_frame = ctk.CTkFrame(timeline_wrap, fg_color="#1A1A1A", corner_radius=6, height=40)
        self.timeline_frame.grid(row=0, column=0, sticky="ew")
        self.timeline_frame.grid_columnconfigure(0, weight=1)
        self.timeline_frame.grid_rowconfigure(0, weight=1)
        self.timeline_canvas = ctk.CTkCanvas(self.timeline_frame, bg="#1A1A1A", highlightthickness=0, height=40)
        self.timeline_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.timeline_canvas.bind("<Button-1>", self.on_timeline_click)
        self.timeline_canvas.bind("<B1-Motion>", self.on_timeline_drag)
        
        self.timer_label = ctk.CTkLabel(timeline_wrap, text="00:00 / 00:00", width=100, fg_color="#2A2A2A", corner_radius=6)
        self.timer_label.grid(row=0, column=1, padx=(10, 0), sticky="e")
        
        self.settings_frame = ctk.CTkFrame(main_frame)
        self.settings_frame.grid(row=4, column=0, pady=(0, 15), sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        self.build_settings()
        
        self.result_frame = ctk.CTkFrame(main_frame)
        self.result_frame.grid(row=5, column=0, pady=(0, 15), sticky="ew")
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_columnconfigure(1, weight=1)
        self.build_result()
        
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.grid(row=6, column=0, pady=(0, 10), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=20)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%", width=50)
        self.progress_label.grid(row=0, column=1)
        
        self.time_label = ctk.CTkLabel(main_frame, text="Время конвертации: --", fg_color="#2A2A2A", corner_radius=6, height=30)
        self.time_label.grid(row=7, column=0, pady=(0, 10), sticky="ew")
        
        self.generate_btn = ctk.CTkButton(main_frame, text="Конвертировать", command=self.generate, fg_color="#D0D0D0", text_color="#1A1A1A", font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.generate_btn.grid(row=8, column=0, pady=(0, 15), sticky="ew")
        
        self.status_label = ctk.CTkLabel(main_frame, text="Готов к работе", fg_color="#2A2A2A", corner_radius=6, height=35)
        self.status_label.grid(row=9, column=0, sticky="ew")
    
    def select_files(self):
        paths = filedialog.askopenfilenames(
            title="Выберите видео, GIF или изображения",
            filetypes=[
                ("Все файлы", "*.mp4 *.gif *.webm *.mov *.avi *.mkv *.png *.jpg *.jpeg *.bmp *.webp *.tiff"),
                ("Видео", "*.mp4 *.gif *.webm *.mov *.avi *.mkv"),
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff")
            ]
        )
        if paths:
            self.load_progress_frame.grid()
            total = len(paths)
            for i, path in enumerate(paths):
                if len(self.file_list) < 30:
                    self.file_list.append(path)
                    if i == 0:
                        self.load_video(path)
                progress = (i + 1) / total
                self.load_progress_bar.set(progress)
                self.load_progress_label.configure(text=f"Загрузка: {int(progress * 100)}%")
                self.update_files_display()
                self.update()
            self.load_progress_frame.grid_remove()
            self.load_progress_bar.set(0)
            self.load_progress_label.configure(text="Загрузка: 0%")
    
    def load_video(self, path):
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
        self.current_video_path = path
        info = get_video_info(path)
        if info:
            self.total_frames = info['frames']
            self.fps = info['fps']
            self.video_duration = info['duration']
            self.video_cap = cv2.VideoCapture(path)
            self.update_timer()
        self.show_preview(path)
    
    def show_preview(self, path):
        try:
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')):
                self.clear_files()
                img = Image.open(path)
                w = self.preview_frame.winfo_width() - 20
                h = self.preview_height - 20
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
                self.timeline_canvas.delete("all")
                self.timer_label.configure(text="Изображение")
                self.play_btn.configure(state="disabled", fg_color="#555555", text_color="#888888")
                self.pause_btn.configure(state="disabled", fg_color="#555555", text_color="#888888")
                self.speed_check.configure(state="disabled")
                self.speed_slider.configure(state="disabled")
            else:
                cap = None
                try:
                    cap = cv2.VideoCapture(path)
                    if cap is None or not cap.isOpened():
                        self.preview_label.configure(text="Не удалось открыть видео")
                        return
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        w = self.preview_frame.winfo_width() - 20
                        h = self.preview_height - 20
                        img.thumbnail((w, h), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.preview_label.configure(image=photo, text="")
                        self.preview_label.image = photo
                        self.draw_timeline()
                        self.play_btn.configure(state="normal", fg_color="#D0D0D0", text_color="#1A1A1A")
                        self.pause_btn.configure(state="normal", fg_color="#D0D0D0", text_color="#1A1A1A")
                        self.speed_check.configure(state="normal")
                        self.speed_slider.configure(state="normal")
                    else:
                        self.preview_label.configure(text="Не удалось прочитать кадр")
                        if cap is not None:
                            cap.release()
                        return
                except:
                    self.preview_label.configure(text="Ошибка загрузки")
                    if cap is not None:
                        cap.release()
                    return
                finally:
                    if cap is not None:
                        cap.release()
        except:
            self.preview_label.configure(text="Не удалось загрузить")
    
    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
    
    def update_timer(self):
        if self.total_frames == 0:
            return
        current = self.current_frame_pos / self.fps if self.fps > 0 else 0
        total = self.video_duration
        self.timer_label.configure(text=f"{self.format_time(current)} / {self.format_time(total)}")
    
    def draw_timeline(self):
        self.timeline_canvas.delete("all")
        w = self.timeline_canvas.winfo_width()
        if w < 10 or self.total_frames <= 0:
            self.after(100, self.draw_timeline)
            return
        self.timeline_canvas.create_rectangle(10, 5, w-10, 35, fill="#2A2A2A", outline="#444444")
        pos = 10 + (self.current_frame_pos / self.total_frames) * (w - 20)
        self.timeline_canvas.create_line(pos, 5, pos, 35, fill="#FFFFFF", width=2)
        self.update_timer()
    
    def on_timeline_click(self, event):
        w = self.timeline_canvas.winfo_width()
        if w < 10 or self.total_frames <= 0:
            return
        self.current_frame_pos = int(max(0, min(1, (event.x - 10) / (w - 20))) * self.total_frames)
        if self.video_cap:
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_pos)
            ret, frame = self.video_cap.read()
            if ret and frame is not None:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                w2 = self.preview_frame.winfo_width() - 20
                h2 = self.preview_height - 20
                img.thumbnail((w2, h2), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
        self.draw_timeline()
    
    def on_timeline_drag(self, event):
        self.on_timeline_click(event)
    
    def toggle_play(self):
        if not self.current_video_path:
            return
        if self.current_video_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')):
            return
        if self.is_playing:
            self.is_playing = False
            self.is_paused = False
            self.play_btn.configure(text="▶")
            self.pause_btn.configure(text="⏸")
            if self._updater_id is not None:
                self.after_cancel(self._updater_id)
                self._updater_id = None
            self.current_frame_pos = 0
            if self.video_cap:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.show_preview(self.current_video_path)
            return
        self.is_playing = True
        self.is_paused = False
        self.play_btn.configure(text="⏹")
        self.pause_btn.configure(text="⏸")
        if self._updater_id is not None:
            self.after_cancel(self._updater_id)
            self._updater_id = None
        self.play_video()
    
    def toggle_pause(self):
        if not self.is_playing:
            return
        if self.current_video_path and self.current_video_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')):
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.configure(text="▶")
            if self._updater_id is not None:
                self.after_cancel(self._updater_id)
                self._updater_id = None
        else:
            self.pause_btn.configure(text="⏸")
            self.play_video()
    
    def play_video(self):
        if not self.video_cap or not self.is_playing or self.is_paused:
            return
        try:
            ret, frame = self.video_cap.read()
            if not ret or frame is None:
                self.is_playing = False
                self.is_paused = False
                self.play_btn.configure(text="▶")
                self.pause_btn.configure(text="⏸")
                if self._updater_id is not None:
                    self.after_cancel(self._updater_id)
                    self._updater_id = None
                self.current_frame_pos = 0
                if self.video_cap:
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.show_preview(self.current_video_path)
                return
            self.current_frame_pos += 1
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            w = self.preview_frame.winfo_width() - 20
            h = self.preview_height - 20
            img.thumbnail((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
            self.draw_timeline()
            delay_ms = int(1000 / (self.fps * self.playback_speed)) if self.fps > 0 else 50
            self._updater_id = self.after(delay_ms, self.play_video)
        except:
            self.is_playing = False
            self.is_paused = False
            self.play_btn.configure(text="▶")
            self.pause_btn.configure(text="⏸")
            if self._updater_id is not None:
                self.after_cancel(self._updater_id)
                self._updater_id = None
    
    def toggle_speed(self):
        if self.speed_check_var.get() == "on":
            self.speed_slider.configure(state="normal")
        else:
            self.speed_slider.configure(state="disabled")
            self.playback_speed = 1.0
            self.speed_label.configure(text="1.0x")
    
    def on_speed_change(self, value):
        self.playback_speed = float(value)
        self.speed_label.configure(text=f"{self.playback_speed:.1f}x")
    
    def toggle_resize(self):
        self.preview_height = 500 if self.preview_height == 300 else 300
        self.preview_label.configure(height=self.preview_height)
        if self.current_video_path:
            self.show_preview(self.current_video_path)
    
    def clear_files(self):
        self.is_playing = False
        self.is_paused = False
        if self._updater_id is not None:
            self.after_cancel(self._updater_id)
            self._updater_id = None
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        self.file_list = []
        self.current_video_path = None
        self.current_frame_pos = 0
        self.total_frames = 0
        self.fps = 0
        self.video_duration = 0
        self.update_files_display()
        self.preview_label.configure(image="", text="Превью")
        self.timeline_canvas.delete("all")
        self.timer_label.configure(text="00:00 / 00:00")
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        self.time_label.configure(text="Время конвертации: --")
        self.size_result_label.configure(text="~0 KB")
        self.play_btn.configure(state="normal", fg_color="#D0D0D0", text_color="#1A1A1A")
        self.pause_btn.configure(state="normal", fg_color="#D0D0D0", text_color="#1A1A1A")
        self.speed_check.configure(state="normal")
        self.speed_slider.configure(state="normal")
    
    def update_files_display(self):
        for widget in self.files_scrollable.winfo_children():
            widget.destroy()
        self.file_buttons = []
        self.file_list_label.configure(text=f"Загружено файлов: {len(self.file_list)}")
        cols = 6
        for i, path in enumerate(self.file_list):
            frame = ctk.CTkFrame(self.files_scrollable, fg_color="#333333", corner_radius=6, width=50, height=50)
            frame.grid(row=i // cols, column=i % cols, padx=3, pady=3, sticky="nsew")
            frame.grid_propagate(False)
            label = ctk.CTkLabel(frame, text=str(i+1), font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF")
            label.grid(row=0, column=0, sticky="nsew")
            tooltip = ctk.CTkToplevel(self)
            tooltip.overrideredirect(True)
            tooltip.attributes("-topmost", True)
            tooltip.withdraw()
            tooltip_label = ctk.CTkLabel(tooltip, text=os.path.basename(path), fg_color="#2A2A2A", corner_radius=6, padx=10, pady=5)
            tooltip_label.pack()
            def on_enter(event, p=path, t=tooltip):
                t.geometry(f"+{event.x_root+10}+{event.y_root+10}")
                t.deiconify()
            def on_leave(event, t=tooltip):
                t.withdraw()
            frame.bind("<Enter>", on_enter)
            frame.bind("<Leave>", on_leave)
            frame.bind("<Button-1>", lambda e, idx=i: self.on_file_click(idx))
            self.file_buttons.append(frame)
    
    def on_file_click(self, idx):
        if idx < len(self.file_list):
            self.load_video(self.file_list[idx])
    
    def build_settings(self):
        ctk.CTkLabel(self.settings_frame, text="─── Настройки ───", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        sync_row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        sync_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.sync_var = ctk.StringVar(value="off")
        self.sync_check = ctk.CTkCheckBox(sync_row, text="Одинаковые параметры для всех", variable=self.sync_var, onvalue="on", offvalue="off", command=self.toggle_sync, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.sync_check.grid(row=0, column=0, padx=(0, 10))
        ctk.CTkLabel(self.settings_frame, text="Папка сохранения:").grid(row=2, column=0, sticky="w", pady=5)
        ff = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        ff.grid(row=2, column=1, sticky="ew")
        ff.grid_columnconfigure(0, weight=1)
        self.folder_entry = ctk.CTkEntry(ff, border_color="#FFFFFF", border_width=1, fg_color="#2A2A2A", text_color="#FFFFFF")
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.folder_btn = ctk.CTkButton(ff, text="Обзор", command=self.select_folder, fg_color="#D0D0D0", text_color="#1A1A1A", width=80)
        self.folder_btn.grid(row=0, column=1)
        ctk.CTkLabel(self.settings_frame, text="Название:").grid(row=3, column=0, sticky="w", pady=5)
        self.name_entry = ctk.CTkEntry(self.settings_frame, border_color="#FFFFFF", border_width=1, fg_color="#2A2A2A", text_color="#FFFFFF")
        self.name_entry.grid(row=3, column=1, sticky="ew", pady=5)
        self.name_entry.insert(0, "анимация")
        ctk.CTkLabel(self.settings_frame, text="Формат вывода:").grid(row=4, column=0, sticky="w", pady=5)
        self.format_menu = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=[
                "Telegram Style (TGS, Flutter)",
                "Lottie JSON (Flutter)",
                "SpriteSheet + JSON",
                "CSS Animation",
                "Android (Java)",
                "iOS (Swift)",
                "React",
                "WEBP",
                "JSON + base64",
                "GIF",
                "APNG",
                "MP4 (без звука)"
            ], 
            command=self.on_format_change,
            fg_color="#2A2A2A",
            button_color="#D0D0D0",
            text_color="#FFFFFF"
        )
        self.format_menu.grid(row=4, column=1, sticky="ew", pady=5)
        self.format_menu.set("Telegram Style (TGS, Flutter)")
        adv_row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        adv_row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 5))
        self.advanced_var = ctk.StringVar(value="off")
        self.advanced_check = ctk.CTkCheckBox(adv_row, text="Расширенные настройки", variable=self.advanced_var, onvalue="on", offvalue="off", command=self.toggle_advanced, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.advanced_check.grid(row=0, column=0, padx=(0, 10))
        self.basic_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.basic_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.basic_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.basic_frame, text="Размер кадра:").grid(row=0, column=0, sticky="w", pady=5)
        sf = ctk.CTkFrame(self.basic_frame, fg_color="transparent")
        sf.grid(row=0, column=1, sticky="ew", pady=5)
        sf.grid_columnconfigure(0, weight=1)
        self.size_slider = ctk.CTkSlider(sf, from_=64, to=256, command=self.on_size_change, number_of_steps=6)
        self.size_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.size_slider.set(128)
        self.size_label = ctk.CTkLabel(sf, text="128px", width=50)
        self.size_label.grid(row=0, column=1)
        ctk.CTkLabel(self.basic_frame, text="Кол-во кадров:").grid(row=1, column=0, sticky="w", pady=5)
        ff2 = ctk.CTkFrame(self.basic_frame, fg_color="transparent")
        ff2.grid(row=1, column=1, sticky="ew", pady=5)
        ff2.grid_columnconfigure(0, weight=1)
        self.frames_slider = ctk.CTkSlider(ff2, from_=8, to=60, command=self.on_frames_change, number_of_steps=13)
        self.frames_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.frames_slider.set(20)
        self.frames_label = ctk.CTkLabel(ff2, text="20", width=30)
        self.frames_label.grid(row=0, column=1)
        ctk.CTkLabel(self.basic_frame, text="Задержка:").grid(row=2, column=0, sticky="w", pady=5)
        df = ctk.CTkFrame(self.basic_frame, fg_color="transparent")
        df.grid(row=2, column=1, sticky="ew", pady=5)
        df.grid_columnconfigure(0, weight=1)
        self.delay_slider = ctk.CTkSlider(df, from_=30, to=150, command=self.on_delay_change, number_of_steps=12)
        self.delay_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.delay_slider.set(50)
        self.delay_label = ctk.CTkLabel(df, text="50мс", width=50)
        self.delay_label.grid(row=0, column=1)
        ctk.CTkLabel(self.basic_frame, text="Шаг сетки (SpriteSheet):").grid(row=3, column=0, sticky="w", pady=5)
        gf = ctk.CTkFrame(self.basic_frame, fg_color="transparent")
        gf.grid(row=3, column=1, sticky="ew", pady=5)
        gf.grid_columnconfigure(0, weight=1)
        self.grid_slider = ctk.CTkSlider(gf, from_=16, to=256, command=self.on_grid_change, number_of_steps=4)
        self.grid_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.grid_slider.set(64)
        self.grid_label = ctk.CTkLabel(gf, text="64px", width=50)
        self.grid_label.grid(row=0, column=1)
        self.advanced_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.advanced_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.advanced_frame.grid_columnconfigure(1, weight=1)
        self.advanced_frame.grid_remove()
        ctk.CTkLabel(self.advanced_frame, text="Target FPS:").grid(row=0, column=0, sticky="w", pady=5)
        fpsf = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        fpsf.grid(row=0, column=1, sticky="ew", pady=5)
        fpsf.grid_columnconfigure(0, weight=1)
        self.fps_slider = ctk.CTkSlider(fpsf, from_=10, to=60, command=self.on_fps_change, number_of_steps=10)
        self.fps_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.fps_slider.set(30)
        self.fps_label = ctk.CTkLabel(fpsf, text="30 FPS", width=60)
        self.fps_label.grid(row=0, column=1)
        ctk.CTkLabel(self.advanced_frame, text="Разрешение:").grid(row=1, column=0, sticky="w", pady=5)
        resf = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        resf.grid(row=1, column=1, sticky="ew", pady=5)
        resf.grid_columnconfigure(0, weight=1)
        self.res_slider = ctk.CTkSlider(resf, from_=128, to=1024, command=self.on_res_change, number_of_steps=15)
        self.res_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.res_slider.set(512)
        self.res_label = ctk.CTkLabel(resf, text="512px", width=60)
        self.res_label.grid(row=0, column=1)
        ctk.CTkLabel(self.settings_frame, text="Качество:").grid(row=8, column=0, sticky="w", pady=5)
        qf = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        qf.grid(row=8, column=1, sticky="w", pady=5)
        self.quality_var = ctk.StringVar(value="minimal")
        self.quality_min = ctk.CTkRadioButton(qf, text="Минимальный вес", variable=self.quality_var, value="minimal", command=self.on_quality_change, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.quality_min.grid(row=0, column=0, padx=(0, 15))
        self.quality_bal = ctk.CTkRadioButton(qf, text="Сбалансированный", variable=self.quality_var, value="balanced", command=self.on_quality_change, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.quality_bal.grid(row=0, column=1, padx=(0, 15))
        self.quality_high = ctk.CTkRadioButton(qf, text="Высокое качество", variable=self.quality_var, value="high", command=self.on_quality_change, fg_color="#D0D0D0", text_color="#FFFFFF")
        self.quality_high.grid(row=0, column=2)
    
    def toggle_sync(self):
        self.sync_settings = self.sync_var.get() == "on"
        self.save_settings()
    
    def toggle_advanced(self):
        self.advanced_mode = self.advanced_var.get() == "on"
        if self.advanced_mode:
            self.advanced_frame.grid()
        else:
            self.advanced_frame.grid_remove()
        self.save_settings()
    
    def build_result(self):
        ctk.CTkLabel(self.result_frame, text="─── Результат ───", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        ctk.CTkLabel(self.result_frame, text="Итоговый размер:").grid(row=1, column=0, sticky="w", pady=5)
        self.size_result_label = ctk.CTkLabel(self.result_frame, text="~0 KB", fg_color="#2A2A2A", corner_radius=6, height=30)
        self.size_result_label.grid(row=1, column=1, sticky="ew", pady=5)
        self.result_preview_frame = ctk.CTkFrame(self.result_frame, fg_color="#111111", corner_radius=8, height=180)
        self.result_preview_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        self.result_preview_frame.grid_columnconfigure(0, weight=1)
        self.result_preview_frame.grid_rowconfigure(0, weight=1)
        self.result_preview_label = ctk.CTkLabel(self.result_preview_frame, text="Готовый спрайт появится здесь", fg_color="#111111", corner_radius=8)
        self.result_preview_label.grid(row=0, column=0, sticky="nsew")
        rbf = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        rbf.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        rbf.grid_columnconfigure(0, weight=1)
        rbf.grid_columnconfigure(1, weight=1)
        self.result_delete_btn = ctk.CTkButton(rbf, text="Удалить", command=self.delete_result, fg_color="#D0D0D0", text_color="#FF6B6B", width=120)
        self.result_delete_btn.grid(row=0, column=0, padx=(0, 10))
        self.copy_btn = ctk.CTkButton(rbf, text="Копировать JSON", command=self.copy_json, fg_color="#D0D0D0", text_color="#1A1A1A", width=120)
        self.copy_btn.grid(row=0, column=1, padx=(0, 10))
        self.open_folder_btn = ctk.CTkButton(rbf, text="Открыть папку", command=self.open_output_folder, fg_color="#D0D0D0", text_color="#1A1A1A", width=120)
        self.open_folder_btn.grid(row=0, column=2)
    
    def copy_json(self):
        try:
            if hasattr(self, 'generator') and self.generator.json_path and os.path.exists(self.generator.json_path):
                with open(self.generator.json_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.clipboard_append(data)
                self.status_label.configure(text="JSON скопирован")
            else:
                self.status_label.configure(text="Нет JSON файла")
        except:
            self.status_label.configure(text="Ошибка копирования")
    
    def on_fps_change(self, value):
        self.target_fps = int(value)
        self.fps_label.configure(text=f"{self.target_fps} FPS")
        self.save_settings()
    
    def on_res_change(self, value):
        self.target_resolution = int(value)
        self.res_label.configure(text=f"{self.target_resolution}px")
        self.save_settings()
    
    def on_grid_change(self, value):
        grid_size = int(value)
        steps = [16, 32, 64, 128, 256]
        closest = min(steps, key=lambda x: abs(x - grid_size))
        self.grid_slider.set(closest)
        self.grid_label.configure(text=f"{closest}px")
        self.sprite_grid_size = closest
        self.save_settings()
    
    def on_size_change(self, v):
        self.size_label.configure(text=f"{int(v)}px")
        self.generator.set_frame_size(int(v))
        self.save_settings()
    
    def on_frames_change(self, v):
        self.frames_label.configure(text=str(int(v)))
        self.generator.set_max_frames(int(v))
        self.save_settings()
    
    def on_delay_change(self, v):
        self.delay_label.configure(text=f"{int(v)}мс")
        self.generator.set_delay(int(v))
        self.save_settings()
    
    def on_quality_change(self):
        self.generator.set_quality(self.quality_var.get())
        self.save_settings()
    
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.generator.set_output_folder(folder)
            self.save_settings()
    
    def on_format_change(self, choice):
        m = {
            "Telegram Style (TGS, Flutter)": "tgs",
            "Lottie JSON (Flutter)": "lottie",
            "SpriteSheet + JSON": "spritesheet",
            "CSS Animation": "css",
            "Android (Java)": "android",
            "iOS (Swift)": "ios",
            "React": "react",
            "WEBP": "webp",
            "JSON + base64": "json_base64",
            "GIF": "gif",
            "APNG": "apng",
            "MP4 (без звука)": "mp4"
        }
        self.generator.set_format(m.get(choice, "tgs"))
        self.save_settings()
    
    def generate_palette(self, frames):
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
                        for count, color in sorted_colors[:10]:
                            if len(color) == 3:
                                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                            else:
                                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                            if hex_color not in palette:
                                palette.append(hex_color)
                    if len(palette) >= 10:
                        break
        except:
            pass
        return palette[:10]
    
    def generate(self):
        if not self.file_list:
            self.status_label.configure(text="Сначала добавьте файлы!")
            return
        if self.is_processing:
            return
        self.is_processing = True
        self.generate_btn.configure(state="disabled", text="Обработка...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        self.start_time = time.time()
        self.status_label.configure(text="Начало конвертации...")
        threading.Thread(target=self.process_generation).start()
    
    def process_generation(self):
        try:
            output_folder = self.folder_entry.get()
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            fmt = self.format_menu.get()
            m = {
                "Telegram Style (TGS, Flutter)": "tgs",
                "Lottie JSON (Flutter)": "lottie",
                "SpriteSheet + JSON": "spritesheet",
                "CSS Animation": "css",
                "Android (Java)": "android",
                "iOS (Swift)": "ios",
                "React": "react",
                "WEBP": "webp",
                "JSON + base64": "json_base64",
                "GIF": "gif",
                "APNG": "apng",
                "MP4 (без звука)": "mp4"
            }
            format_type = m.get(fmt, "tgs")
            total = len(self.file_list)
            processed = 0
            total_size = 0
            for i, file_path in enumerate(self.file_list):
                self.after(0, self.update_progress, i, total, f"Обработка {i+1}/{total}: {os.path.basename(file_path)}")
                self.generator = GiftGenerator()
                self.generator.set_output_folder(output_folder)
                self.generator.set_frame_size(int(self.size_slider.get()))
                self.generator.set_max_frames(int(self.frames_slider.get()))
                self.generator.set_delay(int(self.delay_slider.get()))
                self.generator.set_quality(self.quality_var.get())
                self.generator.load_video(file_path)
                if not self.generator.extract_frames():
                    continue
                if format_type in ['css', 'spritesheet']:
                    palette = self.generate_palette(self.generator.frames)
                    palette_path = os.path.join(output_folder, f"{self.generator.filename}_colors.json")
                    with open(palette_path, 'w', encoding='utf-8') as f:
                        json.dump({"palette": palette}, f, indent=2)
                self.generator.generate_json(format_type)
                processed += 1
                total_size += self.generator.get_result_size()
                progress = (i + 1) / total
                self.after(0, self.update_progress_bar, progress)
            elapsed = time.time() - self.start_time
            self.after(0, self.generation_finished, processed, total, elapsed, total_size)
        except Exception as e:
            self.after(0, self.generation_error, str(e))
    
    def update_progress(self, i, total, message):
        self.status_label.configure(text=message)
    
    def update_progress_bar(self, progress):
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"{int(progress * 100)}%")
    
    def generation_finished(self, processed, total, elapsed, total_size):
        self.is_processing = False
        self.generate_btn.configure(state="normal", text="Конвертировать")
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        time_str = f"{minutes}м {seconds}с" if minutes > 0 else f"{seconds}с"
        self.time_label.configure(text=f"Время конвертации: {time_str}")
        size_kb = total_size / 1024
        if size_kb < 1024:
            size_str = f"~{size_kb:.1f} KB"
        else:
            size_str = f"~{size_kb/1024:.1f} MB"
        self.size_result_label.configure(text=size_str)
        if processed == total:
            self.status_label.configure(text=f"Готово! Обработано {processed} файлов")
        else:
            self.status_label.configure(text=f"Обработано {processed} из {total} файлов")
    
    def generation_error(self, msg):
        self.is_processing = False
        self.generate_btn.configure(state="normal", text="Конвертировать")
        self.status_label.configure(text=f"Ошибка: {msg}")
    
    def delete_result(self):
        self.result_preview_label.configure(image="", text="Готовый спрайт появится здесь")
        self.size_result_label.configure(text="~0 KB")
        self.status_label.configure(text="Результат удалён")
    
    def open_output_folder(self):
        folder = self.folder_entry.get()
        if os.path.exists(folder):
            os.startfile(folder)

if __name__ == "__main__":
    app = JSONPackApp()
    app.mainloop()
