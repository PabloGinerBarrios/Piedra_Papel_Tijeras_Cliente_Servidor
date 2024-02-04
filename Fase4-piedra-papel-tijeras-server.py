"""Programa servidor del juego Piedra, papel, tijeras con comunicación encriptada asimétricamente."""

#Imports necesarios para el programa.
import socket
import sys
import threading
import random

#Imports para la codificación de la comunicación.
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP


class Player(threading.Thread):
    """Declaración de la clase player para gestionar a los clientes que se conecten."""
    #Constructor de la clase player. Recibo
    def __init__(self, socket_player, addr_player, player_name):
        super().__init__()
        self.socket_player = socket_player #El socket generado en la función accept
        self.address = addr_player #El adres generao en la función accept
        self.player_name = player_name #El nombre de jugador generado en la función generadora player_name
        self.cerrar = False #La condición para cerrar el socket
        self.games_summary = [] #La  lista de partidas para poder ver después el summary
        self.opened_public_key_client = None #Variable que almacenará el archivo abierto de la clave pública del cliente.
        self.opened_private_key_server = None #Variable que almacenará el archivo abierto de la clave privada del servidor.
    
    #Método que se ejecuta al iniciar el hilo(player/jugador).
    def run(self):
        self.open_keys()
        option = None #Variable que representa la elección del jugador en el menú principal
        with self.socket_player: #Bloque with para el uso del socket.
            print(f"Conexión exitosa con el cliente {self.address} con nombre {self.player_name}")
            while not self.cerrar:
                option = int(self.recieve_data()) #El serviddor recibe la opción escogida por el jugador
                #Condicional para saber qué hacer dependiendo de la opción escogida
                if option == 1:
                    self.send_data('Opción recibida')
                    print(f"{self.player_name} a escogido iniciar una nueva partida.") #Mensaje de info en la consola del server
                    self.play_game() #Se inicia una partida
                elif option == 2:
                    print(f"{self.player_name} a escogido ver el resumen de las partidas.") #Mensaje de info en la consola del server
                    self.send_data(self.show_summary()) #Se envía el sumario de las partidas al usuario.
                elif option == 0:
                    print(f'Desconexión de {self.player_name}') #Mensaje de info en la consola del server
                    self.cerrar = True #Se activa la condición para salir del bucle del menú inicial.
            #En teoría, el cierre del socket lo hace implícitamente la terminación  del bloque with.
            #Sin embargo, he decidido pornerlo porque he leído que es una práctica habitual para hacer más legible el código.
            self.socket_player.close()
    
    def open_keys(self):
        """Función para abrir los archivos de las claves"""
        
        file_public_key_client = Path(__file__).parent / "public_key_client.pem"
        file_private_key_server = Path(__file__).parent / "private_key_server.pem"
        
        try:
            if not file_public_key_client.exists():
                raise FileNotFoundError("No se encontró la clave pública del servidor.")
            if not file_private_key_server.exists():
                raise FileNotFoundError("No se encontró la clave privada del cliente.")
            self.opened_public_key_client = open(file_public_key_client, 'rb').read()
            self.opened_private_key_server = open(file_private_key_server, 'rb').read()
        except FileNotFoundError as fnfe:
            print(f"Error: {fnfe}")
            sys.exit()
           
    def play_game(self):
        """Método para gestionar cada partida."""
        winers = [] #Lista para guardar los resultados de cada  ronda de una partida.
        player_score = 0 #Inicio la puntuación del jugadoren 0 para iniciar la partida.
        computer_score = 0 #Inicio la puntuación del ordenador en 0 para iniciar la partida.
        while player_score < 3 and computer_score < 3: #Bucle para gestionar las rondas necesarias para la partida.
            computer_option = random.choice([1, 2, 3]) #Generación de la opción escogida por el usuario.
            player_option = int(self.recieve_data()) #Recepción de la opción del usuario ya validada por el cliente.
            
            #Info en el servidor sobre qué juega cada jugador.
            if player_option == 1:
                print(f"{self.player_name} ha jugado Piedra")
            elif player_option == 2:
                print(f"{self.player_name} ha jugado Papel")
            elif player_option == 3:
                print(f"{self.player_name} ha jugado Tijeras")
            
            #Se calcula el resultado de la ronda y se añade a la lista winers.    
            result = self.check_round_winner(player_option, computer_option)
            winers.append(result)
            
            #Modificación de la puntuación del jugador o del ordenador dependiendo de quién haya ganado.
            if "WINNER -> PLAYER" in result:
                player_score += 1
            elif "WINNER -> COMPUTER" in result:
                computer_score += 1

            #Envío la información de la puntuación del jugador, la puntuación del ordenador y el resultado de la ronda.
            self.send_data(f"{player_score},{computer_score},{result}")
        
        #Recibo mensaje de confirmación
        self.recieve_data()
        #Método para enviar el sumario de la partida con los resultados de todas las rondas. 
        self.show_game_summary(winers, player_score, computer_score)
 
    def check_round_winner(self, player_option, computer_option):
        """Método para calcular el resultado de una ronda."""
        
        options = ["Piedra", "Papel", "Tijeras"] #Lista que almacena las posibles opciones.
        #Matriz para calcular los posibles resultados.
        result_matrix = {
            (1, 1): "EMPATE",
            (1, 2): "WINNER -> COMPUTER",
            (1, 3): "WINNER -> PLAYER",
            (2, 1): "WINNER -> PLAYER",
            (2, 2): "EMPATE",
            (2, 3): "WINNER -> COMPUTER",
            (3, 1): "WINNER -> COMPUTER",
            (3, 2): "WINNER -> PLAYER",
            (3, 3): "EMPATE",
        }

        #Opción en texto del número enviado por el usuario.
        player_choice = options[player_option - 1]
        computer_choice = options[computer_option - 1]
        result_key = (player_option, computer_option)

        #Retorno del resultado.
        return f"PLAYER -> {player_choice} -- COMPUTER -> {computer_choice} -- {result_matrix[result_key]}"
    
    def show_game_summary(self, winers, player_score, computer_score):
        """Método para enviar el resumen de una partida con el resultado de todas las rondas."""
        data = "\nGAME SUMMARY\n" #Inicio el mensaje
        #Recorro la lista de rondas y añado el resultado al mensaje.
        for i, round_result in enumerate(winers):
            data +=(f"Round {i+1}: {round_result}\n")
        
        #Añado, al final del resumen, quién ha sido el ganador final de la partida.
        if player_score == 3:
            self.games_summary.append("WINER -> PLAYER")
            data += "\nWINER -> PLAYER"
        elif computer_score == 3:
            self.games_summary.append("WINER -> COMPUTER")
            data += "\nWINER -> COMPUTER"
        
        #Envío el mensaje al cliente.   
        self.send_data(data)
    
    def show_summary(self):
        """Método para crear el mensaje correspondiente al resumen de partidas jugadas."""
        data = "\nGAMES SUMMARY\n" #Inicio el mensaje.
        #Si no se ha jugador ninguna partida envío un mensaje informativo.
        if len(self.games_summary) < 1:
            return "\nNo hay partidas almacenadas." #Retorno el mensaje informativo.
        else:
            #Si hay alguna partida jugada, recorro la lista de partidas  y añado al mensaje el resultado.
            for i, game in enumerate(self.games_summary):
                data += f"GAME {i+1}: {game}\n"
        return data #Retorno el mensaje.
    
    def decrypt_data(self, data):
        """Función para desencriptar la información recibida como parámetro con RSA y AES."""
        #Leo la clave privada del servidor.
        private_key = RSA.import_key(self.opened_private_key_server)
        
        #Leo los bytes de la información y selecciono por su tamaño lo pedazo de info.
        key_size = private_key.size_in_bytes()
        enc_session_key = data[:key_size]
        nonce = data[key_size:key_size+16]
        tag = data[key_size+16:key_size+32]
        cipher_texto = data[key_size+32:]
        
        #Desencripto la clave simétrica que estaba codificada asimétricamente.
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)
        
        #Desencripto la información.
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        decrypted_data = cipher_aes.decrypt_and_verify(cipher_texto,tag)
        
        return decrypted_data
    
    def recieve_data(self):
        """Método que recibe información del cliente y la decodifica."""
        data = self.socket_player.recv(1024)
        return self.decrypt_data(data).decode("utf-8")
    
    def encrypt_data(self, msg):
        """Función para encriptar la información recibida como parámetro con AES y RSA."""
        #Paso el mensaje a binario
        data = msg.encode("utf-8")
        
        #Genero la clave aleatoriamente
        session_key = get_random_bytes(16)
        
        #Cifro simétricamente los datos.
        cipher_aes = AES.new(session_key,AES.MODE_EAX)
        cipher_text, tag = cipher_aes.encrypt_and_digest(data)
        
        #Leo la clave pública del servidor.
        recipient_key = RSA.import_key(self.opened_public_key_client)
        
        #Cifro asimétriamente la clave.
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        enc_session_key = cipher_rsa.encrypt(session_key)
        
        encrypted_data = enc_session_key+cipher_aes.nonce+tag+cipher_text
        
        return encrypted_data
    
    def send_data(self, msg):
        """Método para enviar información el cliente codificada en binario."""
        self.socket_player.sendall(self.encrypt_data(msg))

def player_name():
    """Función para generar un nombre de jugador para mostrar la info en la consola del servidor."""
    i = 1
    while True:
        yield f"Player{i}"
        i+=1
           
if __name__=="__main__":
    HOST = '127.0.0.1'
    PORT = 5000
    
    try:
        private_key_server = Path(__file__).parent / "private_key_server.pem"
        if not private_key_server.exists():
            raise FileNotFoundError("No se encontró la clave privada del servidor.")
        socket_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Creo el socket.
        print("Socket servidor creado.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit()
    except socket.error:
        print("Error en la creación del socket servidor.")
        sys.exit()
    
    try:
        socket_listen.bind((HOST, PORT)) #Relaciono el socket a la ip y el número de puerto elegidos.
    except socket.error as e:
        print(f"Error socket: {e}")
        sys.exit()
    
    socket_listen.listen(5) #El servidor se queda esperando que algún cliente se conecte. 
    player_name_generator = player_name() #Llamada a la función generadora de nombres de jugadores.
    
    while True:
        socket_player, addr_player = socket_listen.accept() #El servidor acepta un jugador.
        
        #Creo un hilo que ejecutará la función del servidor con un cliente en paralelo con el resto de hilos.
        player_thread = Player(socket_player, addr_player, next(player_name_generator))
        player_thread.start() #Inicio el hilo.