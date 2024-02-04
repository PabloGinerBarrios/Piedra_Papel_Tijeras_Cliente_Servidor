from Crypto.PublicKey import RSA
from pathlib import Path

def generate_keys():
    key = RSA.generate(2048)
    private_key = key.exportKey()
    fichero_path = Path(__file__).parent / "private_key_server.pem"
    
    file_out = open(fichero_path, 'wb')
    file_out.write(private_key)
    file_out.close()
    
    public_key = key.publickey().exportKey()
    
    fichero_path = Path(__file__).parent / "public_key_server.pem"
    
    file_out = open(fichero_path, 'wb')
    file_out.write(public_key)
    file_out.close()
    
if __name__ == "__main__":
    generate_keys()