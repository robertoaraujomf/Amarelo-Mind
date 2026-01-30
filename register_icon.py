import os
import sys
import winreg
import ctypes

def register_icon():
    # Base directory
    cwd = os.getcwd()
    # Correct icon name found in directory
    icon_rel_path = os.path.join("assets", "icons", "files_amind_icon.png")
    icon_path = os.path.join(cwd, icon_rel_path)
    
    if not os.path.exists(icon_path):
        print(f"Erro: Ícone não encontrado em {icon_path}")
        return

    try:
        # Register .amind extension in HKCU
        key_ext = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.amind")
        winreg.SetValue(key_ext, "", winreg.REG_SZ, "AmareloMind.Project")
        winreg.CloseKey(key_ext)

        # Register ProgID
        key_prog = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\AmareloMind.Project")
        winreg.SetValue(key_prog, "", winreg.REG_SZ, "Projeto Amarelo Mind")
        
        # Register DefaultIcon
        # Note: Windows typically requires .ico, but we register the path requested.
        key_icon = winreg.CreateKey(key_prog, r"DefaultIcon")
        winreg.SetValue(key_icon, "", winreg.REG_SZ, icon_path)
        winreg.CloseKey(key_icon)

        print(f"Registro efetuado com sucesso para o usuário atual.")
        print(f"Ícone definido: {icon_path}")
        
        # Notify Explorer of changes
        try:
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
        except Exception as e:
            print(f"Aviso ao notificar Explorer: {e}")

    except Exception as e:
        print(f"Erro ao registrar: {e}")

if __name__ == "__main__":
    register_icon()
