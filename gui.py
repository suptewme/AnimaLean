import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from PIL import Image, ImageTk
import cv2
from core import GiftGenerator
from utils import create_output_folder, get_filename_without_ext

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class JSONPackApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("JSONPack — Генератор анимированных спрайтов")
        self.geometry("800x850")
        self.minsize(750, 800)
        
        self.generator = GiftGenerator()
        self.current_video_path = None
        self.preview_frame = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            main_frame, 
            text="📦 JSONPack — Генератор анимированных спрайтов",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="w")
        
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        
        self.select_btn = ctk.CTkButton(
            file_frame,
            text="Выбрать видео",
            command=self.select_video,
            fg_color="#D0D0D0",
            text_color="#1A1A1A",
            hover_color="#E8E8E8"
        )
        self.select_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="Файл не выбран",
            fg_color="#2A2A2A",
            corner_radius=6,
            height=35
        )
        self.file_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        self.delete_btn = ctk.CTkButton(
            file_frame,
            text="🗑 Удалить",
            command=self.delete_video,
            fg_color="#D0D0D0",
            text_color="#FF6B6B",
            hover_color="#E8E8E8",
            width=100
        )
        self.delete_btn.grid(row=0, column=2)
        
        self.preview_frame = ctk.CTkFrame(main_frame, fg_color="#111111", corner_radius=8)
        self.preview_frame.grid(row=2, column=0, pady=(0, 15), sticky="ew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Превью видео",
            fg_color="#111111",
            corner_radius=8,
            height=200
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.grid(row=3, column=0, pady=(0, 15), sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            settings_frame,
            text="─── Настройки ───",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        ctk.CTkLabel(settings_frame, text="Папка сохранения:").grid(row=1, column=0, sticky="w", pady=5)
        folder_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        folder_frame.grid(row=1, column=1, sticky="ew")
        folder_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            border_color="#FFFFFF",
            border_width=1,
            fg_color="#2A2A2A",
            text_color="#FFFFFF"
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.folder_entry.insert(0, os.path.join(os.getcwd(), "сжатые"))
        
        self.folder_btn = ctk.CTkButton(
            folder_frame,
            text="Обзор",
            command=self.select_folder,
            fg_color="#D0D0D0",
            text_color="#1A1A1A",
            hover_color="#E8E8E8",
            width=80
        )
        self.folder_btn.grid(row=0, column=1)
        
        ctk.CTkLabel(settings_frame, text="Название:").grid(row=2, column=0, sticky="w", pady=5)
        self.name_entry = ctk.CTkEntry(
            settings_frame,
            border_color="#FFFFFF",
            border_width=1,
            fg_color="#2A2A2A",
            text_color="#FFFFFF"
        )
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.name_entry.insert(0, "подарок")
        
        ctk.CTkLabel(settings_frame, text="Формат вывода:").grid(row=3, column=0, sticky="w", pady=5)
        self.format_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=[
                "Telegram Style (TGS, Flutter)",
                "Lottie JSON (Flutter)",
                "SpriteSheet + JSON",
                "CSS Animation",
                "Android (Java)",
                "iOS (Swift)",
                "React"
            ],
            command=self.on_format_change,
            fg_color="#2A2A2A",
            button_color="#D0D0D0",
            button_hover_color="#E8E8E8",
            text_color="#FFFFFF"
        )
        self.format_menu.grid(row=3, column=1, sticky="ew", pady=5)
        self.format_menu.set("Telegram Style (TGS, Flutter)")
        
        ctk.CTkLabel(settings_frame, text="Размер кадра:").grid(row=4, column=0, sticky="w", pady=5)
        size_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        size_frame.grid(row=4, column=1, sticky="ew", pady=5)
        size_frame.grid_columnconfigure(0, weight=1)
        size_frame.grid_columnconfigure(1, weight=0)
        size_frame.grid_columnconfigure(2, weight=0)
        
        self.size_slider = ctk.CTkSlider(
            size_frame,
            from_=64,
            to=256,
            command=self.on_size_change,
            number_of_steps=6
        )
        self.size_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.size_slider.set(128)
        
        self.size_label = ctk.CTkLabel(size_frame, text="128px", width=50)
        self.size_label.grid(row=0, column=1)
        
        ctk.CTkLabel(settings_frame, text="Кол-во кадров:").grid(row=5, column=0, sticky="w", pady=5)
        frames_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        frames_frame.grid(row=5, column=1, sticky="ew", pady=5)
        frames_frame.grid_columnconfigure(0, weight=1)
        frames_frame.grid_columnconfigure(1, weight=0)
        frames_frame.grid_columnconfigure(2, weight=0)
        
        self.frames_slider = ctk.CTkSlider(
            frames_frame,
            from_=8,
            to=60,
            command=self.on_frames_change,
            number_of_steps=13
        )
        self.frames_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.frames_slider.set(20)
        
        self.frames_label = ctk.CTkLabel(frames_frame, text="20", width=30)
        self.frames_label.grid(row=0, column=1)
        
        ctk.CTkLabel(settings_frame, text="Задержка:").grid(row=6, column=0, sticky="w", pady=5)
        delay_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        delay_frame.grid(row=6, column=1, sticky="ew", pady=5)
        delay_frame.grid_columnconfigure(0, weight=1)
        delay_frame.grid_columnconfigure(1, weight=0)
        delay_frame.grid_columnconfigure(2, weight=0)
        
        self.delay_slider = ctk.CTkSlider(
            delay_frame,
            from_=30,
            to=150,
            command=self.on_delay_change,
            number_of_steps=12
        )
        self.delay_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.delay_slider.set(50)
        
        self.delay_label = ctk.CTkLabel(delay_frame, text="50мс", width=50)
        self.delay_label.grid(row=0, column=1)
        
        ctk.CTkLabel(settings_frame, text="Качество:").grid(row=7, column=0, sticky="w", pady=5)
        quality_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        quality_frame.grid(row=7, column=1, sticky="w", pady=5)
        
        self.quality_var = ctk.StringVar(value="minimal")
        
        self.quality_min = ctk.CTkRadioButton(
            quality_frame,
            text="Минимальный вес",
            variable=self.quality_var,
            value="minimal",
            command=self.on_quality_change,
            fg_color="#D0D0D0",
            hover_color="#E8E8E8",
            text_color="#FFFFFF"
        )
        self.quality_min.grid(row=0, column=0, padx=(0, 15))
        
        self.quality_bal = ctk.CTkRadioButton(
            quality_frame,
            text="Сбалансированный",
            variable=self.quality_var,
            value="balanced",
            command=self.on_quality_change,
            fg_color="#D0D0D0",
            hover_color="#E8E8E8",
            text_color="#FFFFFF"
        )
        self.quality_bal.grid(row=0, column=1, padx=(0, 15))
        
        self.quality_high = ctk.CTkRadioButton(
            quality_frame,
            text="Высокое качество",
            variable=self.quality_var,
            value="high",
            command=self.on_quality_change,
            fg_color="#D0D0D0",
            hover_color="#E8E8E8",
            text_color="#FFFFFF"
        )
        self.quality_high.grid(row=0, column=2)
        
        result_frame = ctk.CTkFrame(main_frame)
        result_frame.grid(row=4, column=0, pady=(0, 15), sticky="ew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            result_frame,
            text="─── Результат ───",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        ctk.CTkLabel(result_frame, text="Итоговый размер:").grid(row=1, column=0, sticky="w", pady=5)
        self.size_result_label = ctk.CTkLabel(
            result_frame,
            text="~0 KB",
            fg_color="#2A2A2A",
            corner_radius=6,
            height=30
        )
        self.size_result_label.grid(row=1, column=1, sticky="ew", pady=5)
        
        self.result_preview_frame = ctk.CTkFrame(
            result_frame,
            fg_color="#111111",
            corner_radius=8,
            height=180
        )
        self.result_preview_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        self.result_preview_frame.grid_columnconfigure(0, weight=1)
        self.result_preview_frame.grid_rowconfigure(0, weight=1)
        
        self.result_preview_label = ctk.CTkLabel(
            self.result_preview_frame,
            text="Готовый спрайт появится здесь",
            fg_color="#111111",
            corner_radius=8
        )
        self.result_preview_label.grid(row=0, column=0, sticky="nsew")
        
        result_btn_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_btn_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        result_btn_frame.grid_columnconfigure(0, weight=1)
        result_btn_frame.grid_columnconfigure(1, weight=1)
        
        self.result_delete_btn = ctk.CTkButton(
            result_btn_frame,
            text="🗑 Удалить",
            command=self.delete_result,
            fg_color="#D0D0D0",
            text_color="#FF6B6B",
            hover_color="#E8E8E8",
            width=120
        )
        self.result_delete_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.open_folder_btn = ctk.CTkButton(
            result_btn_frame,
            text="📂 Открыть папку",
            command=self.open_output_folder,
            fg_color="#D0D0D0",
            text_color="#1A1A1A",
            hover_color="#E8E8E8",
            width=120
        )
        self.open_folder_btn.grid(row=0, column=1)
        
        self.generate_btn = ctk.CTkButton(
            main_frame,
            text="Сжать и создать JSON",
            command=self.generate,
            fg_color="#D0D0D0",
            text_color="#1A1A1A",
            hover_color="#E8E8E8",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50
        )
        self.generate_btn.grid(row=5, column=0, pady=(0, 15), sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Готов к работе",
            fg_color="#2A2A2A",
            corner_radius=6,
            height=35
        )
        self.status_label.grid(row=6, column=0, sticky="ew")

    def select_video(self):
        file_path = filedialog.askopenfilename(
            title="Выберите видео или GIF",
            filetypes=[
                ("Видео файлы", "*.mp4 *.gif *.webm *.mov *.avi *.mkv"),
                ("MP4 видео", "*.mp4"),
                ("GIF анимация", "*.gif"),
                ("WebM видео", "*.webm"),
                ("MOV видео", "*.mov"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self.current_video_path = file_path
        self.file_label.configure(text=os.path.basename(file_path))
        
        if not self.name_entry.get() or self.name_entry.get() == "подарок":
            base_name = get_filename_without_ext(file_path)
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, base_name)
        
        self.generator.load_video(file_path)
        self.show_preview(file_path)
        self.status_label.configure(text=f"Загружено: {os.path.basename(file_path)}")

    def show_preview(self, file_path):
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                max_size = (300, 200)
                pil_img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(pil_img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
        except:
            self.preview_label.configure(text="Не удалось загрузить превью")

    def delete_video(self):
        self.current_video_path = None
        self.file_label.configure(text="Файл не выбран")
        self.preview_label.configure(image="", text="Превью видео")
        self.generator.frames = []
        self.status_label.configure(text="Файл удалён")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.generator.set_output_folder(folder)

    def on_format_change(self, choice):
        format_map = {
            "Telegram Style (TGS, Flutter)": "tgs",
            "Lottie JSON (Flutter)": "lottie",
            "SpriteSheet + JSON": "spritesheet",
            "CSS Animation": "css",
            "Android (Java)": "android",
            "iOS (Swift)": "ios",
            "React": "react"
        }
        self.generator.set_format(format_map.get(choice, "tgs"))

    def on_size_change(self, value):
        size = int(value)
        self.size_label.configure(text=f"{size}px")
        self.generator.set_frame_size(size)

    def on_frames_change(self, value):
        frames = int(value)
        self.frames_label.configure(text=str(frames))
        self.generator.set_max_frames(frames)

    def on_delay_change(self, value):
        delay = int(value)
        self.delay_label.configure(text=f"{delay}мс")
        self.generator.set_delay(delay)

    def on_quality_change(self):
        self.generator.set_quality(self.quality_var.get())

    def generate(self):
        if not self.current_video_path:
            self.status_label.configure(text="❌ Сначала выберите видео!")
            return
        
        self.generate_btn.configure(state="disabled", text="⏳ Обработка...")
        self.status_label.configure(text="⏳ Извлечение кадров...")
        
        thread = threading.Thread(target=self.process_generation)
        thread.start()

    def process_generation(self):
        try:
            format_map = {
                "Telegram Style (TGS, Flutter)": "tgs",
                "Lottie JSON (Flutter)": "lottie",
                "SpriteSheet + JSON": "spritesheet",
                "CSS Animation": "css",
                "Android (Java)": "android",
                "iOS (Swift)": "ios",
                "React": "react"
            }
            
            format_type = format_map.get(self.format_menu.get(), "tgs")
            
            self.generator.set_output_folder(self.folder_entry.get())
            
            if format_type in ["tgs", "lottie"]:
                self.generator.set_frame_size(int(self.size_slider.get()))
                self.generator.set_max_frames(int(self.frames_slider.get()))
                self.generator.set_delay(int(self.delay_slider.get()))
                self.generator.set_quality(self.quality_var.get())
                
                frames_extracted = self.generator.extract_frames()
                if not frames_extracted:
                    self.after(0, self.generation_error, "Не удалось извлечь кадры из видео")
                    return
                
                result = self.generator.generate_json(format_type)
            else:
                self.generator.set_frame_size(int(self.size_slider.get()))
                self.generator.set_max_frames(int(self.frames_slider.get()))
                self.generator.set_delay(int(self.delay_slider.get()))
                self.generator.set_quality(self.quality_var.get())
                
                frames_extracted = self.generator.extract_frames()
                if not frames_extracted:
                    self.after(0, self.generation_error, "Не удалось извлечь кадры из видео")
                    return
                
                result = self.generator.generate_json(format_type)
            
            if result:
                self.after(0, self.generation_success)
            else:
                self.after(0, self.generation_error, "Ошибка при создании файлов")
                
        except Exception as e:
            self.after(0, self.generation_error, str(e))

    def generation_success(self):
        size = self.generator.get_result_size()
        size_kb = size / 1024
        size_str = f"~{size_kb:.1f} KB" if size_kb < 1024 else f"~{size_kb/1024:.1f} MB"
        
        self.size_result_label.configure(text=size_str)
        self.status_label.configure(text="✅ Готово! Файлы сохранены")
        self.generate_btn.configure(state="normal", text="Сжать и создать JSON")
        
        if self.generator.sprite_path and os.path.exists(self.generator.sprite_path):
            try:
                img = Image.open(self.generator.sprite_path)
                max_size = (300, 180)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.result_preview_label.configure(image=photo, text="")
                self.result_preview_label.image = photo
            except:
                self.result_preview_label.configure(text="Спрайт создан")

    def generation_error(self, error_msg):
        self.status_label.configure(text=f"❌ Ошибка: {error_msg}")
        self.generate_btn.configure(state="normal", text="Сжать и создать JSON")

    def delete_result(self):
        self.result_preview_label.configure(image="", text="Готовый спрайт появится здесь")
        self.size_result_label.configure(text="~0 KB")
        self.status_label.configure(text="Результат удалён")

    def open_output_folder(self):
        folder = self.folder_entry.get()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showerror("Ошибка", "Папка не найдена")

if __name__ == "__main__":
    app = JSONPackApp()
    app.mainloop()