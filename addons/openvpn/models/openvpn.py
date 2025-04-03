import logging
import os
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenVpn():
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenVpn, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.certs = self.get_existing()
        self.base_dir = "/etc/openvpn"
        self.easyrsa_dir = f"{self.base_dir}/easy-rsa"
        self.public_cert_dir = f"{self.easyrsa_dir}/pki/issued"
        self.private_cert_dir = f"{self.easyrsa_dir}/pki/private"
        self.client_config_dir = f"{self.base_dir}/client-configs"
        self.ca_cert_path = f"{self.easyrsa_dir}/pki/ca.crt"
        self.tls_crypt_path = f"{self.base_dir}/tls-crypt.key"
        self.client_template_path = f"{self.base_dir}/client-template.txt"
        self.easyrsa_script = f"{self.easyrsa_dir}/easyrsa"
        self._initialized = True
        
    def create_client(self, filename):
        if not self.validate_name(filename):
            logger.error(f"Invalid client name: {filename}")
            raise ValueError(f"Invalid client name: {filename}")
            
        if self.exists(filename):
            logger.warning(f"Client {filename} already exists")
            return False
            
        if not Path(self.easyrsa_dir).exists():
            logger.error("EasyRSA directory does not exist")
            raise FileNotFoundError("EasyRSA directory does not exist")
            
        # Ensure client config directory exists
        os.makedirs(self.client_config_dir, exist_ok=True)
            
        res = subprocess.Popen(
            args=['sudo', '-S', './easyrsa', '--batch', 'build-client-full', filename, 'nopass'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.easyrsa_dir
        )
        stdout, stderr = res.communicate(input=os.getenv('ServerPassword') + "\n")
        if res.returncode != 0:
            logger.warning(f"Failed to create client. Easyrsa command exited with return code {res.returncode}")
            logger.warning(f"Standard Output: {stdout}")
            logger.warning(f"Standard Error: {stderr}")
            raise RuntimeError(f"Failed to create client. Easyrsa command exited with return code {res.returncode}")
            
        client_ovpn_path = self.get_client_config_path(filename)
        subprocess.run(['sudo', '-S', 'cp', self.client_template_path, client_ovpn_path], 
                      input=os.getenv('ServerPassword') + "\n", 
                      text=True, 
                      capture_output=True)
        
        with open(client_ovpn_path, 'a') as f:
            f.write("<ca>\n")
            ca_content = self._sudo_read(self.ca_cert_path)
            if ca_content is None:
                raise FileNotFoundError("CA certificate not found.")
            f.write(ca_content)
            f.write("</ca>\n\n")
            
            f.write("<cert>\n")
            cert_content = self._sudo_read(f"{self.public_cert_dir}/{filename}.crt")
            if cert_content is None:
                raise FileNotFoundError(f"Certificate file for client {filename} not found.")
            cert_block = "\n".join(re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', cert_content, re.DOTALL))
            f.write(cert_block)
            f.write("\n</cert>\n\n")
            
            f.write("<key>\n")
            key_content = self._sudo_read(f"{self.private_cert_dir}/{filename}.key")
            if key_content is None:
                raise FileNotFoundError(f"Key file for client {filename} not found.")
            f.write(key_content)
            f.write("</key>\n\n")
            
            f.write("<tls-crypt>\n")
            tls_crypt_content = self._sudo_read(self.tls_crypt_path)
            if tls_crypt_content is None:
                raise FileNotFoundError("TLS crypt key file not found.")
            f.write(tls_crypt_content)
            f.write("</tls-crypt>\n")
        
        # Set appropriate permissions
        subprocess.run(['sudo', 'chmod', '644', client_ovpn_path], 
                      input=os.getenv('ServerPassword') + "\n", 
                      text=True, 
                      capture_output=True)
        
        # Update the certs list
        self.certs = self.get_existing()
        return True
        
    def delete_client(self, filename):
        """Delete a client certificate by revoking it"""
        if not self.validate_name(filename):
            logger.error(f"Invalid client name: {filename}")
            raise ValueError(f"Invalid client name: {filename}")
            
        if not self.exists(filename):
            logger.warning(f"Client {filename} does not exist")
            return False
            
        res = subprocess.Popen(
            args=['sudo', '-S', './easyrsa', 'revoke', filename],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.easyrsa_dir
        )
        stdout, stderr = res.communicate(input=os.getenv('ServerPassword') + "\n")
        
        if res.returncode != 0:
            logger.warning(f"Failed to revoke client. Easyrsa command exited with return code {res.returncode}")
            logger.warning(f"Standard Output: {stdout}")
            logger.warning(f"Standard Error: {stderr}")
            raise RuntimeError(f"Failed to revoke client. Easyrsa command exited with return code {res.returncode}")
            
        # Update CRL
        res = subprocess.Popen(
            args=['sudo', '-S', './easyrsa', 'gen-crl'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.easyrsa_dir
        )
        stdout, stderr = res.communicate(input=os.getenv('ServerPassword') + "\n")
        
        if res.returncode != 0:
            logger.warning(f"Failed to generate CRL. Easyrsa command exited with return code {res.returncode}")
            logger.warning(f"Standard Output: {stdout}")
            logger.warning(f"Standard Error: {stderr}")
            raise RuntimeError(f"Failed to generate CRL. Easyrsa command exited with return code {res.returncode}")
            
        # Remove the client OVPN file if it exists
        client_ovpn_path = self.get_client_config_path(filename)
        if os.path.exists(client_ovpn_path):
            subprocess.run(['sudo', 'rm', client_ovpn_path], 
                          input=os.getenv('ServerPassword') + "\n", 
                          text=True, 
                          capture_output=True)
            
        # Update the certs list
        self.certs = self.get_existing()
        return True
        
    def exists(self, filename):
        """Check if a client certificate exists"""
        cert_path = os.path.join(self.public_cert_dir, f"{filename}.crt")
        return self._sudo_file_exists(cert_path)
        
    def get_existing(self):
        """Get a list of existing client certificates"""
        try:
            res = subprocess.Popen(
                args=['sudo', '-S', 'ls', self.public_cert_dir],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = res.communicate(input=os.getenv('ServerPassword') + "\n")
            
            if res.returncode != 0:
                logger.warning(f"Failed to list certificates. Command exited with return code {res.returncode}")
                logger.warning(f"Standard Error: {stderr}")
                return []
                
            # Filter out server.crt and extract client names
            client_certs = []
            for cert in stdout.strip().split('\n'):
                if cert and cert != "server.crt" and cert.endswith('.crt'):
                    client_name = cert[:-4]  # Remove .crt extension
                    client_certs.append(client_name)
                    
            return client_certs
        except Exception as e:
            logger.error(f"Error getting existing certificates: {str(e)}")
            return []
            
    def validate_name(self, filename):
        """Validate the client name to prevent command injection"""
        # Only allow alphanumeric characters, underscores, and hyphens
        pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        return bool(pattern.match(filename))
        
    def _sudo_read(self, filepath):
        """Read a file with sudo privileges"""
        try:
            res = subprocess.Popen(
                args=['sudo', '-S', 'cat', filepath],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = res.communicate(input=os.getenv('ServerPassword') + "\n")
            
            if res.returncode != 0:
                logger.warning(f"Failed to read file {filepath}. Command exited with return code {res.returncode}")
                logger.warning(f"Standard Error: {stderr}")
                return None
                
            return stdout
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return None
            
    def _sudo_file_exists(self, filepath):
        """Check if a file exists with sudo privileges"""
        try:
            res = subprocess.Popen(
                args=['sudo', '-S', 'test', '-f', filepath],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            _, _ = res.communicate(input=os.getenv('ServerPassword') + "\n")
            
            # test command returns 0 if file exists, non-zero otherwise
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Error checking if file {filepath} exists: {str(e)}")
            return False

# Singleton instance
openVpn = OpenVpn()