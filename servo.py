import websocket
import json
import threading
import time

# Variables globales
cortex_token = None
session_id = None
headset_id = None
esp32_ip = "10.96.23.117"  # Reemplaza con la IP de tu ESP32
esp32_port = 8080  # Puerto que configuraste en el ESP32
ws_app = None  # Instancia de WebSocketApp


def enviar_comando_al_esp32(comando):
    """
    Envía un comando al ESP32 a través de un socket.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # La librería socket de python es la que permite la conexión.
            s.connect((esp32_ip, esp32_port))
            s.sendall(comando.encode() + b'\n')  # Asegúrate de enviar con salto de línea
            print(f"Comando '{comando}' enviado al ESP32.")
    except ConnectionRefusedError:
        print(
            f"Error: No se pudo conectar al ESP32 en {esp32_ip}:{esp32_port}. Asegúrate de que el ESP32 esté encendido y conectado a la red, y que el socket esté abierto."
        )
    except socket.timeout:
        print(f"Error: Tiempo de espera agotado al conectar al ESP32.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def process_command(accion, potencia):
    """
    Procesa la señal mental y envía el comando correspondiente al ESP32.
    """
    # Categorizar la potencia (opcional, para propósitos de registro o lógica adicional)
    categoria = "Bajo"
    if potencia > 0.30:
        categoria = "Medio"
    if potencia > 0.70:
        categoria = "Alto"

    # Enviar comando al ESP32 según la acción y la potencia
    if accion == "left" and potencia >= 0.30:
        print(f"Mover servo a la izquierda. Potencia: {potencia * 100:.2f}%")
        enviar_comando_al_esp32("izq")  # Envía el comando "izq" al ESP32
    elif accion == "right" and potencia >= 0.10:
        print(f"Mover servo a la derecha. Potencia: {potencia * 100:.2f}%")
        enviar_comando_al_esp32("der")  # Envía el comando "der" al ESP32
    elif accion == "neutral":
        print(f"Accion neutral. Potencia: {potencia * 100:.2f}%")

def on_message(ws, message):
    """
    Maneja los mensajes recibidos del Emotiv Cortex.
    """
    global cortex_token, session_id, headset_id
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
            "id": 2,
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
                    "status": "active",
                },
                "id": 3,
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
                "streams": ["com"],
            },
            "id": 4,
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



def on_error(ws, error):
    print("Error:", error)


def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada")



def on_open(ws):
    """
    Maneja la conexión WebSocket abierta.  Aquí es donde se envían las solicitudes de autorización, queryHeadsets, etc.
    """
    # Enviar solicitud de autorización
    auth_request = {
        "jsonrpc": "2.0",
        "method": "authorize",
        "params": {
            "clientId": "RxcaORHl6m1MYTi3tYB1bBA4sWxjqdcMDynGuWlL",  # Reemplaza con tu Client ID
            "clientSecret": "v1AmcuvPeDRGwNYHhC3R5ycWf9MSTs6hvy4Na6RrJIXFouwLQCWqyRua7lKrEjn3C6a10g6yGoRXBEGgf5SzuXUGgBZTgkvu4J8qYhzQKZZczw5cTPdsHapGV9CZWFGJ",  # Reemplaza con tu Client Secret
            "debit": 0,
        },
        "id": 1,
    }
    ws.send(json.dumps(auth_request))



def run_ws():
    """
    Función para ejecutar el WebSocket en un hilo separado.
    """
    global ws_app
    ws_url = "wss://127.0.0.1:6868"  # Verifica que este endpoint sea correcto
    ws_app = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws_app.run_forever()



if __name__ == "__main__":
    import socket # Importar la librería socket
    print("GAAF")
    # Iniciar el WebSocket en un hilo separado
    ws_thread = threading.Thread(target=run_ws)
    ws_thread.start()

    # Esperar un momento para que el WebSocket se conecte
    time.sleep(2)  # Ajusta este tiempo si es necesario

    # Esperar a que el usuario presione Enter para comenzar el control
    input("Presiona Enter para comenzar a enviar comandos al ESP32...\n")

    # Bucle principal para enviar comandos al ESP32
    try:
        while True:
            comando = input("Ingrese el comando ('izq', 'der', 'salir'): ").lower()
            if comando == "salir":
                break
            elif comando in ["izq", "der"]:
                # Enviar comando al ESP32 a través del WebSocket
                if ws_app and ws_app.sock: # Verificar que el socket esté conectado.
                    if comando == "izq":
                        # Enviar el comando "izq" a través del websocket para que lo procese el on_message
                        mensaje_cortex = {"com": ["left", 0.5]}  # Ejemplo, la potencia 0.5
                        ws_app.send(json.dumps(mensaje_cortex))
                    elif comando == "der":
                         # Enviar el comando "der" a través del websocket para que lo procese el on_message
                        mensaje_cortex = {"com": ["right", 0.5]} # Ejemplo, la potencia 0.5
                        ws_app.send(json.dumps(mensaje_cortex))
                else:
                    print("Error: El WebSocket no está conectado.")
            else:
                print("Comando inválido. Use 'izq', 'der' o 'salir'.")
    except KeyboardInterrupt: # Manejar la interrupción del teclado (Ctrl+C)
        print("\nCerrando conexión...")
    finally:
        # Cerrar la conexión WebSocket
        if ws_app:
            ws_app.close()
        ws_thread.join()  # Esperar a que el hilo del WebSocket termine
        print("Conexión cerrada.")