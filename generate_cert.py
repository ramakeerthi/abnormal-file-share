import os
from OpenSSL import crypto

def generate_self_signed_cert():
    # Certificate directory
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    
    cert_path = os.path.join(cert_dir, 'localhost.crt')
    key_path = os.path.join(cert_dir, 'localhost.key')
    
    # If certificates already exist, return
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("Certificates already exist")
        return
    
    # Generate key
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Write certificate and private key to files
    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print("Generated new certificates")

if __name__ == "__main__":
    generate_self_signed_cert()