import time
import threading
import tkinter as tk
from pynput import keyboard, mouse
import sys
from pywinauto import Desktop
import configparser
import psutil
import os
import subprocess
import json
import platform

class InputBlocker:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.password = config.get("Configuracion", "password", fallback="")
        self.blocking = False
        self.text_block = "BLOCKED"  
        self.ia_references = ["chatgpt", "copilot", "bard", "claude", "deepseek", "gemini"]
        
        # VSCode AI extensions to detect
        self.vscode_ai_extensions = [
            "GitHub Copilot",
            "Tabnine",
            "CodeGPT",
            "IntelliCode",
            "Codeium",
            "Amazon CodeWhisperer",
            "CodeLlama",
            "Kite",
            "AWS Toolkit"
        ]
        
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
        
        self.detection_thread = threading.Thread(target=self.detection_loop)
        self.detection_thread.daemon = True
    
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
            
            self.detection_thread.start()
            
            self.root.mainloop()
        except Exception as e:
            print(f"Error al iniciar la aplicación: {e}")
        finally:
            self.running = False
            time.sleep(0.5)
            sys.exit(0)
    
    def check_vscode_extensions(self):

        def get_vscode_extensions():
            cmd = "code --list-extensions --show-versions"

            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Error al ejecutar el comando: {result.stderr}")
                    return [], []
                
                output = result.stdout.strip()
                extensions = output.split('\n')
                
                user_settings_path = get_vscode_settings_path()
                disabled_extensions = get_disabled_extensions(user_settings_path)
                
                active_extensions = []
                inactive_extensions = []
                
                for ext in extensions:
                    if ext:
                        ext_id = ext.split('@')[0] if '@' in ext else ext
                        if ext_id in disabled_extensions:
                            inactive_extensions.append(ext)
                        else:
                            active_extensions.append(ext)
                
                return active_extensions, inactive_extensions

            except Exception as e:
                print(f"Error: {e}")
                return [], []

        def get_vscode_settings_path():
            if platform.system() == "Windows":
                return os.path.join(os.environ['APPDATA'], 'Code', 'User', 'settings.json')
            elif platform.system() == "Darwin":
                return os.path.expanduser('~/Library/Application Support/Code/User/settings.json')
            else:
                return os.path.expanduser('~/.config/Code/User/settings.json')

        def get_disabled_extensions(settings_path):
            disabled_extensions = []

            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)

                    extensions = settings.get('extensions', {})
                    for ext_id, config in extensions.items():
                        if isinstance(config, dict) and config.get('enabled') is False:
                            disabled_extensions.append(ext_id)

                    disabled = settings.get('extensions.ignoreRecommendations', [])
                    if isinstance(disabled, list):
                        disabled_extensions.extend(disabled)
                except Exception as e:
                    print(f"Error al leer settings.json: {e}")
            
            return disabled_extensions

        def is_ai_extension(extension_id):
            keywords = ['ai', 'gpt', 'copilot', 'intellicode', 'genai', 'codium', 'codewhisperer']
            ext_id_lower = extension_id.lower()
            return any(kw in ext_id_lower for kw in keywords)


        try:
            vscode_processes = [
                proc for proc in psutil.process_iter(['name']) 
                if proc.info['name'] and 'code' in proc.info['name'].lower()
            ]
            if not vscode_processes:
                return False, ""

            active, inactive = get_vscode_extensions()

            print("\nExtensiones Activas:")
            if active:
                for ext in active:
                    print(f"✓ {ext}")
            else:
                print("No se encontraron extensiones activas.")

            print("\nExtensiones Inactivas:")
            if inactive:
                for ext in inactive:
                    print(f"✗ {ext}")
            else:
                print("No se encontraron extensiones inactivas.")
            
            all_extensions = active + inactive
            ai_extensions = [ext for ext in all_extensions if is_ai_extension(ext)]
            ai_extension_ids = [ext.split('@')[0] if '@' in ext else ext for ext in ai_extensions]

            print("\nExtensiones relacionadas con IA:")
            if ai_extensions:
                for ext in ai_extensions:
                    print(f"🤖 {ext}")
            else:
                print("No se detectaron extensiones de IA.")

            if ai_extension_ids:
                return True, "IA Extension Detected"

            return False, ""
        
        except Exception as e:
            print(f"Error al verificar extensiones de VSCode: {e}")
            return False, ""

    
    def detection_loop(self):
        while self.running:
            try:
                time.sleep(2)
                if self.running and not self.blocking:
                    windows = Desktop(backend="uia").windows()
                    for win in windows:
                        if win.window_text(): 
                            for i in self.ia_references:
                                if i in win.window_text().lower():
                                    detected_ai = i
                                    self.text_block = f"BLOCKED - {detected_ai}"
                                    self.label.config(text=self.text_block)
                                    print(f"Sitio de IA detectado: {win}")
                                    self.root.after(0, lambda: self.block_input(True))
                                    break
                    
                    has_ai_extension, extension_name = self.check_vscode_extensions()
                    if has_ai_extension:
                        self.text_block = f"BLOCKED - VSCode: {extension_name}"
                        self.label.config(text=self.text_block)
                        print(f"Extensión AI de VSCode detectada: {extension_name}")
                        self.root.after(0, lambda: self.block_input(True))
                        
            except Exception as e:
                print(f"Error en detección: {e}")
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
                self.text_block = "BLOCKED"
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