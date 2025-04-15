import win32gui
import win32con
import time

# Diccionario de códigos de teclas
VK_CODES = {
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'W': 0x57,
    'SPACE': 0x20
}

# Buscar la ventana del emulador
hwnd = win32gui.FindWindow(None, 'PokemonQuetzalSpanishAlpha8v2 - VisualBoyAdvance-M 2.1.11')  # Cambia esto por el nombre exacto de tu ventana

if hwnd == 0:
    print("❌ No se encontró la ventana del emulador. Verifica el nombre.")
else:
    print("✅ Emulador encontrado.")

    # Activar la ventana
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)  # Pequeña pausa para asegurarse de que está activa

    def presionar_tecla(tecla, mantener=0.05):
        """Presiona y suelta una tecla, opcionalmente mantenerla presionada cierto tiempo"""
        if tecla not in VK_CODES:
            print(f"❌ Tecla {tecla} no reconocida.")
            return
        keycode = VK_CODES[tecla]

        # Presionar
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, keycode, 0)
        time.sleep(mantener)
        # Soltar
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, keycode, 0)

    # Ejemplos de uso:
    presionar_tecla('A')                # Presionar A
    presionar_tecla('W')                # Presionar W
    presionar_tecla('SPACE', mantener=2)  # Mantener espacio 2 segundos
    presionar_tecla('S')
    presionar_tecla('D')
