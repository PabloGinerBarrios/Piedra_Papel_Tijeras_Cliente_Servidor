# Piedra Papel Tijeras
## The classic rock-paper-scissors game created in a client-server format with encrypted information
Client and server are set up to operate with a pair of keys (public and private) for each party.

You can use the "Keys_generator" program to generate the two files containing the keys. This program use RSA algorithm to generate them.

You just have to change the next lines corresponding to the name you want for the keys, although the default one is the one the client and server programs will look for. Although you could also change it in these programs.

fichero_path = Path(__file__).parent / "private_key_server.pem"

fichero_path = Path(__file__).parent / "public_key_server.pem"
