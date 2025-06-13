import websocket
import json
import threading
import os
import time
import win32gui
import win32con

# =============================
# Configuración de control por teclas con Win32
# =============================

VK_CODES = {
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'W': 0x57,
    'SPACE': 0x20
}

lastMove = 'D'  # ← asegúrate de que esté antes de cualquier función que lo use

# Cambia esto por el nombre exacto de tu ventana
hwnd = win32gui.FindWindow(None, 'Juega al juego original de Super Mario Bros en línea GRATIS - Google Chrome') # Aqui cambiamos la pestaña donde queremos ejecutar los comandos Juega al juego original de Super Mario Bros en línea GRATIS - Google Chrome 

if hwnd == 0:
    print("❌ No se encontró la ventana del emulador. Verifica el nombre.")
else:
    print("✅ Emulador encontrado.")
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)

def presionar_tecla(tecla, mantener=0.05):
    """Presiona y suelta una tecla usando Win32"""
    if tecla not in VK_CODES:
        print(f"❌ Tecla {tecla} no reconocida.")
        return
    keycode = VK_CODES[tecla]
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, keycode, 0)
    time.sleep(mantener)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, keycode, 0)

# =============================
# WebSocket + Emotiv BCI
# =============================

cortex_token = None
session_id = None
headset_id = None
ws_app = None

def control(tecla,mantener=0.05):
    """Ejecuta la acción usando presionar_tecla"""
    print(f"Ejecutando control para {tecla}")
    presionar_tecla(tecla, mantener)

def process_command(accion, potencia):
    """Procesa el comando mental"""
    global lastMove 
    categoria = "Bajo"
    if potencia > 0.30:
        categoria = "Medio"
    if potencia > 0.70:
        categoria = "Alto"

    if accion == "left" and potencia >= .80:
        print("<-- Potencia:", potencia * 100, '%')
        control('A')
        lastMove = 'A'
    elif accion == "right" and potencia >= .00:
        print("--> Potencia:", potencia * 100, '%')
        control('D', 0.2)
        lastMove = 'D'
    elif accion == "lift" and potencia >= .00:
        print("^ Potencia:", potencia * 100, '%')
        control('SPACE', 0.45)
        control(lastMove, 0.02)
        

def on_message(ws, message):
    global cortex_token, session_id, headset_id
    data = json.loads(message)

    if data.get("id") == 1 and "result" in data:
        cortex_token = data["result"]["cortexToken"]
        print("Cortex Token obtenido:", cortex_token)
        query_headset_request = {
            "jsonrpc": "2.0",
            "method": "queryHeadsets",
            "params": {},
            "id": 2
        }
        ws.send(json.dumps(query_headset_request))

    elif data.get("id") == 2 and "result" in data:
        if data["result"]:
            headset_id = data["result"][0]["id"]
            print("Headset encontrado:", headset_id)
            create_session_request = {
                "jsonrpc": "2.0",
                "method": "createSession",
                "params": {
                    "cortexToken": cortex_token,
                    "headset": headset_id,
                    "status": "active"
                },
                "id": 3
            }
            ws.send(json.dumps(create_session_request))
        else:
            print("No se encontraron headsets disponibles.")

    elif data.get("id") == 3 and "result" in data:
        session_id = data["result"]["id"]
        print("Sesión creada con ID:", session_id)
        subscribe_request = {
            "jsonrpc": "2.0",
            "method": "subscribe",
            "params": {
                "cortexToken": cortex_token,
                "session": session_id,
                "streams": ["com"]
            },
            "id": 4
        }
        ws.send(json.dumps(subscribe_request))

    elif data.get("id") == 4 and "result" in data:
        print("Suscripción a comandos mentales completada.")

    if "com" in data:
        accion = data["com"][0]
        potencia = data["com"][1]
        #print("La accion es: " ,accion, " y la potencia es de: " ,potencia)
        process_command(accion, potencia)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada")

def on_open(ws):
    auth_request = {
        "jsonrpc": "2.0",
        "method": "authorize",
        "params": {
            "clientId": "RxcaORHl6m1MYTi3tYB1bBA4sWxjqdcMDynGuWlL",
            "clientSecret": "v1AmcuvPeDRGwNYHhC3R5ycWf9MSTs6hvy4Na6RrJIXFouwLQCWqyRua7lKrEjn3C6a10g6yGoRXBEGgf5SzuXUGgBZTgkvu4J8qYhzQKZZczw5cTPdsHapGV9CZWFGJ",
            "debit": 0
        },
        "id": 1
    }
    ws.send(json.dumps(auth_request))

def run_ws():
    global ws_app
    ws_url = "wss://127.0.0.1:6868"
    ws_app = websocket.WebSocketApp(ws_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws_app.run_forever()

if __name__ == "__main__":
    ws_thread = threading.Thread(target=run_ws)
    ws_thread.start()

    input("Presiona Enter para cerrar la conexión...\n")

    print("Cerrando conexión...")
    if ws_app:
        ws_app.close()
    ws_thread.join()
