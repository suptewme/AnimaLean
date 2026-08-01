import sys
import os

try:
    import customtkinter
    import cv2
    import PIL
    import imageio
except ImportError as e:
    print(f"❌ Ошибка: отсутствует библиотека {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

from gui import JSONPackApp

if __name__ == "__main__":
    app = JSONPackApp()
    app.mainloop()
