import telnetlib
import time
from datetime import datetime
from ftplib import FTP
import requests
import os

# Informações das OLTs
olts = {
    "huawei_1": {
        "ip": "x.x.x.x",
        "user": "xxx",
        "password": "xxxx"
    },
    "fiberhome": {
        "ip": "",
        "user": "",
        "password": ""
    },
    "fiberhome_": {
        "ip": "",
        "user": "",
        "password": ""
    }
}

# Configurações FTP (Mikrotik)
ftp_ip_mikrotik = ""
ftp_user_mikrotik = ""
ftp_password_mikrotik = ""

# Dados do Telegram
telegram_token = "xxxx"  # Substitua pelo token do bot
chat_id = "xxxxx"  # Substitua pelo seu chat ID ou grupo

# Diretório local para armazenar os backups
local_backup_path = r"C:\scripts\bkp"
# Função para enviar comandos via Telnet
def send_command(tn, command, wait_time=2):
    tn.write(command.encode('ascii') + b"\n")
    time.sleep(wait_time)
    response = tn.read_very_eager().decode('ascii')
    return response

# Função para baixar o arquivo de backup do servidor Mikrotik via FTP
def download_from_mikrotik(remote_file, local_file):
    try:
        with FTP(ftp_ip_mikrotik) as ftp:
            ftp.login(ftp_user_mikrotik, ftp_password_mikrotik)
            with open(local_file, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
        print(f"Arquivo {remote_file} baixado com sucesso.")
    except Exception as e:
        print(f"Erro ao baixar arquivo do FTP: {e}")

# Função para enviar arquivo via Telegram
def send_file_telegram(file_path):
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendDocument"
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': chat_id, 'caption': f'Backup {os.path.basename(file_path)}'}
            response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            print(f"Arquivo {file_path} enviado com sucesso via Telegram.")
        else:
            print(f"Falha ao enviar arquivo via Telegram. Código de status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar arquivo para Telegram: {e}")

# Função para realizar o backup de cada OLT
def backup_olt(olt_name, olt_info):
    try:
        print(f"Conectando à OLT {olt_name} ({olt_info['ip']})...")

        # Iniciar a conexão Telnet com a OLT
        tn = telnetlib.Telnet(olt_info["ip"])

        # Ler a solicitação de login e enviar o nome de usuário
        tn.read_until(b"username:", timeout=10)
        tn.write(olt_info["user"].encode('ascii') + b"\n")

        # Aguardar a solicitação de senha
        tn.read_until(b"password:", timeout=10)
        tn.write(olt_info["password"].encode('ascii') + b"\n")

        # Entrar no modo "ENABLE"
        tn.write(b"enable\n")
        tn.read_until(b"#", timeout=10)  # Espera pelo prompt do modo enable

        # Gerar o nome do arquivo de backup com base no nome da OLT e na data/hora
        current_date_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        backup_filename = f"backupolt_{olt_name}_{current_date_time}.txt"

        # Executar o comando de backup via FTP
        backup_command = f"backup configuration ftp {ftp_ip_mikrotik} {backup_filename}"
        send_command(tn, backup_command)

        # Pressionar Enter após o comando de backup (resposta para o prompt { <cr>|format<K> }:)
        tn.write(b"\n")

        # Aguardar a pergunta "Are you sure to continue? (y/n)" e responder "y"
        tn.read_until(b"Are you sure to continue? (y/n)", timeout=10)
        tn.write(b"y\n")  # Responder "y"
        # Aguardar 30 segundos antes de encerrar
        time.sleep(30)

        # Fechar a conexão Telnet
        tn.write(b"exit\n")
        tn.close()
        print(f"Conexão com OLT {olt_name} encerrada")

        # Caminho local para salvar o backup
        local_backup_file = os.path.join(local_backup_path, backup_filename)

        # Baixar o arquivo de backup do servidor Mikrotik
        print(f"Baixando o arquivo {backup_filename} do servidor Mikrotik...")
        download_from_mikrotik(backup_filename, local_backup_file)

        # Enviar o arquivo de backup via Telegram
        print(f"Enviando o arquivo {local_backup_file} via Telegram...")
        send_file_telegram(local_backup_file)

    except Exception as e:
        print(f"Erro ao fazer backup da OLT {olt_name}: {e}")

# Criar o diretório de backup se não existir
if not os.path.exists(local_backup_path):
    os.makedirs(local_backup_path)

# Executar o backup para todas as OLTs
for olt_name, olt_info in olts.items():
    backup_olt(olt_name, olt_info)
