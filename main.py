import ctypes
import sys
import os

# Elevar privilegios si no los tiene (necesario para limpiar RAM y servicios)
def require_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join([f'"{a}"' for a in sys.argv]), None, 1
        )
        sys.exit()

if __name__ == "__main__":
    require_admin()

    # Asegurar que los imports funcionen desde cualquier ubicacion
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from ui.main_window import DrxOptiApp
    app = DrxOptiApp()
    app.mainloop()
