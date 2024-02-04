"""Programa cliente del juego Piedra, papel, tijeras con comunicación encriptada asimétricamente."""

#Imports necesarios para el programa
import socket
import sys

#Imports necesarios para la codificación asimétrica de la comunicación.
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from pathlib import Path


#Declaración de variables globales.
socket_client = None #Socket que después crearé.
HOST = '127.0.0.1' #IP
PORT = 5000 #Número de puerto.
opened_public_key_server = None #Variable que almacenará el archivo abierto de la clave pública del servidor.
opened_private_key_client = None #Variable que almacenará el archivo abierto de la clave privada del cliente.

def init_client():
    """Función para al creación del socket."""
    global socket_client
    try:
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Creación del socket.
        print("Socket cliente creado.")
    except socket.error:
        print("Error al crear el socket cliente.")
        sys.exit()
        
    socket_client.connect((HOST, PORT)) #Conexión del socket con una dirección ip y un número de puerto (el servidor.)

def decrypt_data(data):
    """Función para decodificar la información recibida como parámetro coin RSA y AES."""
    
    private_key = RSA.import_key(opened_private_key_client)
    key_size = private_key.size_in_bytes()
    enc_session_key = data[:key_size]
    nonce = data[key_size:key_size+16] #leemos el número generado aleatoriamente para un sólo uso para esta operación de cifrado
    tag = data[key_size+16:key_size+32] #leemos el Hash del texto cifrado
    cipherTexto = data[key_size+32:]
    
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)
    
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    decrypted_data = cipher_aes.decrypt_and_verify(cipherTexto,tag)
    
    return decrypted_data

def recieve_data():
    """Función para recibir información del servidor y decodificarla."""
    data = socket_client.recv(1024)
    return decrypt_data(data).decode("utf-8")

def encrypt_data(msg):
    """Función para encriptar la información recibida como parámetro con AES y RSA."""
    
    #Paso el mensaje a binario
    data = msg.encode("utf-8")
    
    #Genero la clave aleatoriamente
    session_key = get_random_bytes(16)
    
    #Cifro simétricamente los datos.
    cipher_aes = AES.new(session_key,AES.MODE_EAX)
    cipher_text, tag = cipher_aes.encrypt_and_digest(data)
    
    #Leo la clave pública del servidor.
    recipient_key = RSA.import_key(opened_public_key_server)
    
    #Cifro asimétriamente la clave.
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(session_key)
    
    encrypted_data = enc_session_key+cipher_aes.nonce+tag+cipher_text
    
    return encrypted_data

def send_data(msg):
    """Función para enviar información al servidor ya codificada a binario."""
    socket_client.sendall(encrypt_data(msg))


def start_menu():
    """Función para mostrar el menú de inicio y gestionar las distintas opciones que puede elegir el usuario."""
    #Declaración de variables.
    salir = False
    option = -1
    #Bucle para seguir con el juego hasta que el usuario decida salir del programa. 
    while not salir:
        print("""
    MENÚ DE JUEGO
======================================
    1 - Jugar una partida
    2 - Ver resumen de partidas
    0 - Salir
======================================
            """)
        option = check_option(0, 2) #Recibo la opción desde la función de comprobación.
        if option == 1:
            send_data(str(option)) #Envío la opción escogida por el usuario.
            recieve_data()
            play_game() #Me muevo a la función play_game para mostrar al usuario el menú con las opciones para las rondas. 
        elif option == 2:
            send_data(str(option)) #Envío al servidor la opción escogida por el jugador
            print(recieve_data()) #Recibo e imprimo la respuesta del servidor.
        elif option == 0:
            print("\nAdiós!!!!\n") 
            send_data(str(option)) #Envío al servidor la opción del usuario.
            salir = True #Activo la condición de salida del bucle.
    socket_client.close() #Cierro el socket.

def check_option(min, max):
    """Método para pedir al usuario la opción escogida y comprobar que es válida."""
    while True:
        try:
            option = int(input("Introduce el número de la opción deseada: -->"))
            if min <= option <= max:
                return option
            else:
                print(f"\nOpción no válida. Por favor, introduce un número entre {min} y {max}\n") 
        except ValueError:
            print(f"\nPor favor, introduce un entero entre {min} y {max}.\n")

def play_game():
    """Método para gestionar la partida"""
    end_game = False #Condición de salida de la partida.
    while not end_game:
        show_game_menu() #Muestro el menú de las opciones de cada ronda.
        send_data(str(check_option(1,3))) #Envío la opción (ya validada) escogida por el usuario al servidor.
        #Recibo el mensaje con las puntuaciones y el resultado de la ronda y lo espliteo.
        player_score, computer_score, round_result = recieve_data().split(',') 
        print(f"\n{round_result}\n") #Muestro el resultado de la ronda.
        #Condicional para, dependiendo de las puntuaciones, salir de la partida y volver al menú inicial del juego.
        if int(player_score) == 3 or int(computer_score) == 3:
            end_game = True
        #Muestro el resultado de la ronda.
        print(f"PLAYER SCORE: {player_score}\nCOMPUTER SCORE: {computer_score}\n")
        #Si las dos puntuaciones son menores de 3 le pido al usuario que pulser ENTER para continuar.
        #De este modo el usuario puede ver mejor el resultado de la ronda.
        if int(player_score) < 3 and int(computer_score) < 3:
            input("\nPress ENTER to continue.\n")
    
    #Imprimo el resumen de la partida enviada por el servidor. 
    send_data('Recibido')   
    #Recibo el resumen de partida  
    print(recieve_data())
    input("\nPress ENTER to continue.\n")

def show_game_menu():
    """Método para mostrar el menú de opciones de juego dentro de una partida."""
    print("""
  ¿¿QUÉ JUGARÁS??
===============================
1 - Piedra
2 - Papel
3 - Tijeras
===============================
          """)

def open_keys():
    """Función para abrir los archivos de las claves"""
    global opened_public_key_server, opened_private_key_client
    
    file_public_key_server = Path(__file__).parent / "public_key_server.pem"
    file_private_key_client = Path(__file__).parent / "private_key_client.pem"
    
    try:
        if not file_public_key_server.exists():
            raise FileNotFoundError("No se encontró la clave pública del servidor.")
        if not file_private_key_client.exists():
            raise FileNotFoundError("No se encontró la clave privada del cliente.")
        opened_public_key_server = open(file_public_key_server, 'rb').read()
        opened_private_key_client = open(file_private_key_client, 'rb').read()
    except FileNotFoundError as fnfe:
        print(f"Error: {fnfe}")
        sys.exit()

if __name__ == "__main__":
    init_client()
    open_keys()
    print("\nBienvenido a...\n¡¡¡¡¡PIEDRA, PAPEL O TIJERAS!!!!!")
    start_menu()