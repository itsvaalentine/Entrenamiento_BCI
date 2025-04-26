import win32gui

def listar_ventanas():
    def mostrar(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            print(hex(hwnd), win32gui.GetWindowText(hwnd))

    win32gui.EnumWindows(mostrar, None)

listar_ventanas()