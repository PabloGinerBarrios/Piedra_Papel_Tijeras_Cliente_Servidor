# Piedra Papel Tijeras
## The classic rock-paper-scissors game created in a client-server format with encrypted information
Client and server are set up to operate with a pair of keys (public and private) for each party.

You can use the "Keys_generator" program to generate the two files containing the keys. This program use RSA algorithm to generate them.

### Change these lines to modify the names of the resulting files.

```python
fichero_path = Path(__file__).parent / "private_key_server.pem"

fichero_path = Path(__file__).parent / "public_key_server.pem"
```

### If you have changed the previous lines, you will need to modify these in the function open_keys from the client program:

```python
file_public_key_server = Path(__file__).parent / "public_key_server.pem"

file_private_key_client = Path(__file__).parent / "private_key_client.pem"
```

### And these lines in the fucntion open_keys from the server program:

```python
file_public_key_client = Path(__file__).parent / "public_key_client.pem"

file_private_key_server = Path(__file__).parent / "private_key_server.pem"
```
