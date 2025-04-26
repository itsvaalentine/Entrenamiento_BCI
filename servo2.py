import socket

# Configuración
servo_ip = '192.168.0.33'
servo_port = 8080  # Cambia este puerto si sabes que tu servo usa otro

# Crear socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Conectarse al servo
    sock.connect((servo_ip, servo_port))
    
    # Mensaje que quieres enviar
    mensaje = "Izquierda"
    sock.sendall(mensaje.encode('utf-8'))
    
    # Opcional: recibir respuesta
    respuesta = sock.recv(1024)
    print("Respuesta del servo:", respuesta.decode('utf-8'))

finally:
    sock.close()
