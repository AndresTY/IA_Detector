import time
import threading
import tkinter as tk
from pynput import keyboard, mouse
import sys
from pywinauto import Desktop
import configparser

class InputBlocker:
    def __init__(self):
        #self.password = "1234"  # CAMBIARLO!!!
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.password = config.get("Configuracion", "password", fallback="")
        self.blocking = False
        self.text_block = "BLOCKED"  
        self.ia_references = ["chatgpt", "copilot", "bard", "claude","deepseek","gemini"]
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move, 
                                            on_click=self.on_mouse_click)
        
        self.root = tk.Tk()
        self.root.title("Bloqueador")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None) #omitir ALT + F4
        self.root.withdraw()
        
        self.label = tk.Label(self.root, text=self.text_block, 
                            font=("Arial", 50), fg="red", bg="black")
        self.label.pack(pady=(100, 50))
        
        self.password_frame = tk.Frame(self.root, bg="black")
        self.password_frame.pack(pady=20)
        
        self.password_label = tk.Label(self.password_frame, text="Contraseña: ", 
                                    font=("Arial", 16), fg="white", bg="black")
        self.password_label.grid(row=0, column=0, padx=10)
        
        self.password_entry = tk.Entry(self.password_frame, font=("Arial", 16), show="*", 
                                     bg="white", fg="black", width=15)
        self.password_entry.grid(row=0, column=1, padx=10)
        self.password_entry.bind("<Return>", self.check_password)
        
        self.unlock_button = tk.Button(self.password_frame, text="Desbloquear", 
                                    font=("Arial", 14), bg="gray", fg="white",
                                    command=self.check_password)
        self.unlock_button.grid(row=0, column=2, padx=10)
        
        self.status_label = tk.Label(self.root, text="", 
                                    font=("Arial", 14), fg="yellow", bg="black")
        self.status_label.pack(pady=20)
        
        self.running = True
        self.beep_active = False
        
        self.beep_thread = threading.Thread(target=self.continuous_beep)
        self.beep_thread.daemon = True
        
        self.simulation_thread = threading.Thread(target=self.simulate_detection)
        self.simulation_thread.daemon = True
    
    def check_password(self, event=None):
        try:
            entered_password = self.password_entry.get()
            if entered_password == self.password:
                self.status_label.config(text="Contraseña correcta. Desbloqueando...")
                self.root.update()
                time.sleep(1)
                self.block_input(False)
            else:
                self.status_label.config(text="Contraseña incorrecta. Intente nuevamente.")
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus_set()
        except Exception as e:
            print(f"Error al verificar contraseña: {e}")
    
    def start(self):
        try:
            self.keyboard_listener.start()
            self.mouse_listener.start()
            
            self.beep_thread.start()
            
            self.simulation_thread.start()
            
            self.root.mainloop()
        except Exception as e:
            print(f"Error al iniciar la aplicación: {e}")
        finally:
            self.running = False
            time.sleep(0.5)
            sys.exit(0)
    
    def simulate_detection(self):
        while self.running:
            try:
                time.sleep(5)
                if self.running and not self.blocking:
                    windows = Desktop(backend="uia").windows()
                    for win in windows:
                        if win.window_text(): 
                            for i in self.ia_references:
                                if i in win.window_text().lower() :
                                    self.text_block += " - " + i
                                    self.label.config(text=self.text_block)
                                    print(f"Sitio de IA detectado: {win}")
                                    self.root.after(0, lambda: self.block_input(True))
                                    break
            except Exception as e:
                print(f"Error en simulación: {e}")
                time.sleep(1)
            
    def block_input(self, should_block):
        try:
            if should_block and not self.blocking:
                self.blocking = True
                self.beep_active = True
                
                self.password_entry.delete(0, tk.END)
                
                self.root.deiconify()
                self.root.focus_force()
                self.password_entry.focus_set()
                
                self.root.update()
                
            elif not should_block and self.blocking:
                self.blocking = False
                self.beep_active = False
                self.status_label.config(text="")
                self.root.withdraw()
        except Exception as e:
            print(f"Error al cambiar estado de bloqueo: {e}")
            
    def continuous_beep(self):
        while self.running:
            try:
                if self.beep_active:
                    try:
                        import winsound
                        winsound.Beep(1000, 300)
                    except:
                        print("\a")  
                
                time.sleep(0.5)
            except Exception as e:
                print(f"Error en pitido: {e}")
                time.sleep(1)
                
    def on_key_press(self, key):
        return not self.blocking
        
    def on_mouse_move(self, x, y):
        return not self.blocking
        
    def on_mouse_click(self, x, y, button, pressed):
        return not self.blocking

if __name__ == "__main__":
    print("Iniciando bloqueador de entrada...")
    try:
        blocker = InputBlocker()
        blocker.start()
    except Exception as e:
        print(f"Error general del programa: {e}")