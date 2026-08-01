import sys
import os

try:
    import customtkinter
    import cv2
    import PIL
    import imageio
except ImportError as e:
    # Если библиотеки нет, пытаемся вывести ошибку в консоль
    print(f"Ошибка: отсутствует библиотека {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    
    # Если консоль скрыта флажком --windowed, выводим красивое графическое окно ошибки
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка запуска AnimaLens", 
            f"Отсутствует необходимая библиотека: {e}\n\nПожалуйста, установите зависимости из файла requirements.txt."
        )
    except:
        pass
        
    # Безопасный вызов input() только если есть доступный стандартный ввод
    if sys.stdin and not sys.stdin.closed and sys.stdin.readable():
        try:
            input("Нажмите Enter для выхода...")
        except:
            pass
            
    sys.exit(1)

from gui import JSONPackApp

if __name__ == "__main__":
    app = JSONPackApp()
    app.mainloop()
