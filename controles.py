import websocket
import json
import threading
import os
import time
from openpyxl import Workbook, load_workbook
import pyautogui

# Variables globales para almacenar token, sesión, headset, workbook, worksheets y la instancia ws
cortex_token = None
session_id = None
headset_id = None


def control_left():
    """
    Ejecuta la acción de control para el comando "left".
    """
    print("Ejecutando control para 'left'")
    pyautogui.press('A', presses=30)

def control_right():
    """
    Ejecuta la acción de control para el comando "right".
    """
    print("Ejecutando control para 'right'")
    pyautogui.press('D', presses=30
    )

def control(tecla):
    """
    Ejecuta la acción de control para el comando "right".
    """
    print(f"Ejecutando control para {tecla}")
    pyautogui.press(tecla, presses=30
    )

def process_command(accion, potencia):
    """
    Procesa la señal mental: categoriza la potencia, la registra en el Excel y ejecuta
    la acción correspondiente llamando a las funciones de control en otro.py.
    """
    # Categorizar la potencia (por ejemplo: thresholds en 0.30 y 0.70)
    categoria = "Bajo"
    if potencia > 0.30:
        categoria = "Medio"
    if potencia > 0.70:
        categoria = "Alto"
    
    # Mostrar la potencia y ejecutar acción según el comando
    
    # if accion == "neutral":
    #     print("<-> Potencia:", potencia * 100, '%')
    if accion == "left" and potencia >= .30:
        print("<-- Potencia:", potencia * 100, '%')
        control('A')  # Llamamos a la función definida en otro.py
    elif accion == "right" and potencia >= .10:
        print("--> Potencia:", potencia * 100, '%')
        control('D')  # Llamamos a la función definida en otro.py
    

def on_message(ws, message):
    global cortex_token, session_id, headset_id, ws_all, ws_nonneutral
    data = json.loads(message)
    
    # 1. Respuesta a la autorización
    if data.get("id") == 1 and "result" in data:
        cortex_token = data["result"]["cortexToken"]
        print("Cortex Token obtenido:", cortex_token)
        
        # Enviar solicitud queryHeadsets
        query_headset_request = {
            "jsonrpc": "2.0",
            "method": "queryHeadsets",
            "params": {},
            "id": 2
        }
        ws.send(json.dumps(query_headset_request))
    
    # 2. Respuesta a queryHeadsets: obtener el headset id
    elif data.get("id") == 2 and "result" in data:
        if data["result"]:
            headset_id = data["result"][0]["id"]
            print("Headset encontrado:", headset_id)
            
            # Crear sesión con el headset
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
    
    # 3. Respuesta a createSession
    elif data.get("id") == 3 and "result" in data:
        session_id = data["result"]["id"]
        print("Sesión creada con ID:", session_id)
        
        # Suscribirse al stream de comandos mentales ("com")
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
    
    # 4. Respuesta a la suscripción
    elif data.get("id") == 4 and "result" in data:
        print("Suscripción a comandos mentales completada.")
    
    # 5. Procesamiento de datos de comandos mentales
    if "com" in data:
        # Suponiendo que data["com"] es una lista: [accion, potencia]
        accion = data["com"][0]
        potencia = data["com"][1]
        process_command(accion, potencia)
    # Procesamiento de datos de expresiones faciales

    # if "fac" in data:
    #     # data["fac"] es una lista donde típicamente el primer elemento es la expresión detectada
    #     expresion = data["fac"][0]
    #     potencia = data["fac"][1] if len(data["fac"]) > 1 else None
    #     print(f"Expresión facial detectada: {expresion}, Potencia: {potencia}")

    #     # Puedes llamar funciones específicas si quieres reaccionar a ciertas expresiones
    #     if expresion == "blink":
    #         print("¡Parpadeo detectado!")
    #     elif expresion == "smile":
    #         print("¡Sonrisa detectada!")


def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada")

def on_open(ws):
    # Enviar solicitud de autorización
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
    ws_url = "wss://127.0.0.1:6868"  # Verifica que este endpoint sea correcto
    ws_app = websocket.WebSocketApp(ws_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws_app.run_forever()

if __name__ == "__main__":
    # Abrir el archivo Excel existente o crearlo si no existe y obtener ambas hojas

    # Iniciar el WebSocket en un hilo separado
    ws_thread = threading.Thread(target=run_ws)
    ws_thread.start()
    # Esperar a que el usuario presione Enter para cerrar la conexión
    input("Presiona Enter para cerrar la conexión...\n")

    print("Cerrando conexión... (por favor, espera a que se ejecute on_close)")
    
    # Cerrar la conexión llamando al método close() del objeto ws_app
    if ws_app:
        ws_app.close()

    # Esperar a que el hilo termine
    ws_thread.join()
