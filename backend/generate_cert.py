from OpenSSL import crypto
import os

def generate_self_signed_cert():
    # Create certificates directory if it doesn't exist
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    
    # Generate key
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().OU = "Organizational Unit"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Write certificate
    cert_path = os.path.join(cert_dir, 'localhost.crt')
    key_path = os.path.join(cert_dir, 'localhost.key')
    
    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == "__main__":
    generate_self_signed_cert()