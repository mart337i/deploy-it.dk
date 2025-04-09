#!/usr/bin/env python3
import logging
import os
import subprocess

from validators import hostname

from clicx.utils.jinja import render

_logger = logging.getLogger(__name__)

class OpenVpn:

    def __init__(self):
        self.easy_rsa = "/etc/openvpn/easy-rsa/"
        self.issued_dir = f"{self.easy_rsa}pki/issued/"
        self.private_dir = f"{self.easy_rsa}pki/private/"
        self.ca_cert = f"{self.easy_rsa}pki/ca.crt"
        self.tlskey = "/etc/openvpn/tls-crypt.key"
        self.client_template = "client_template.ovpn"


        
        self.tlskey_content = self._read(filepath=self.tlskey)
        self.ca_cert_content = self._read(filepath=self.ca_cert)
    
    def _read(filepath):
        try:
            result = subprocess.run(["sudo", "cat", filepath], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error reading file: {e}")
            return False

    def already_exists(self,client_name):
       if not os.path.exists(f"{self.private_dir}{client_name}.key"):
           return False
       if not os.path.exists(f"{self.issued_dir}{client_name}.crt"):
           return False

    def create_client(self, client_name : str):
        if not hostname(client_name):
            raise ValueError("Invalid Name")
        subprocess.run(["./easyrsa", "--batch", "build-client-full", client_name, "nopass"], check=True)
        key_content = self._read(f"{self.private_dir}{client_name}.key")
        cert_content = self._read(f"{self.issued_dir}{client_name}.crt")
        tls_crypt_content = self.tlskey_content
        
        if not key_content:
            raise FileNotFoundError(f"Certificate file for client {client_name} not found.")
        if not cert_content:
            raise FileNotFoundError(f"Key file for client {client_name} not found.")
        if not tls_crypt_content:
            raise FileNotFoundError("TLS crypt key file not found.")
        
        res = render(
            template_name=self.client_template,
            context={
                "ip" : "83.151.132.162",
                "port": 51719,
                "ca_cert" : self.ca_cert,
                "key_content" : key_content,
                "cert_content" : cert_content,
                "tls_crypt_content": tls_crypt_content
            }
        )

        return res

    def revoke_client(self,client):
        original_dir = os.getcwd()
        os.chdir(f"{self.easy_rsa}") 
        
        try:
            subprocess.run(["sudo", "su"], check=True)
            subprocess.run(["./easyrsa", "--batch", "revoke", client], check=True)
            
            env = os.environ.copy()
            env["EASYRSA_CRL_DAYS"] = "3650"
            subprocess.run(["./easyrsa", "gen-crl"], env=env, check=True)
            
            if os.path.exists("/etc/openvpn/crl.pem"):
                os.remove("/etc/openvpn/crl.pem")
            
            subprocess.run(["cp", f"{self.easy_rsa}pki/crl.pem", "/etc/openvpn/crl.pem"], check=True)
            subprocess.run(["chmod", "644", "/etc/openvpn/crl.pem"], check=True)
            
            with open("/etc/openvpn/ipp.txt", "r") as f:
                lines = f.readlines()
            
            with open("/etc/openvpn/ipp.txt", "w") as f:
                for line in lines:
                    if not line.startswith(f"{client},"):
                        f.write(line)
            
            subprocess.run(["cp", f"{self.easy_rsa}pki/index.txt", f"{self.easy_rsa}pki/index.txt.bk"], check=True)
            
            print(f"\nCertificate for client {client} revoked.")
            
        finally:
            os.chdir(original_dir)

openVpn = OpenVpn()