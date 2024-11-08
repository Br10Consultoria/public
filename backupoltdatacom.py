import telnetlib
import time
from datetime import datetime
import os
import requests

# Informações da OLT Datacom
olts = {
    "datacom": {
        "ip": "",  # IP da OLT Datacom
        "user": "",  # Usuário da OLT
        "password": ""  # Senha da OLT
    }
}

# Configurações do FTP Server
ftp_ip = ""  # IP do servidor FTP
ftp_directory = r"C:\Users\EMSCIANET\Desktop\olts"  # Diretório onde os backups serão salvos

# Dados do Telegram
telegram_token = ""  # Substitua pelo token do bot
chat_id = ""  # Substitua pelo seu chat ID ou grupo

# Função para enviar comandos via Telnet para a OLT Datacom
def send_command(tn, command, wait_time=2):
    tn.write(command.encode('ascii') + b"\n")
    time.sleep(wait_time)
    response = tn.read_very_eager().decode('ascii')
    return response

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

# Função para realizar o backup da OLT Datacom e enviar para o FTP Server
def backup_olt(olt_name, olt_info):
    try:
        print(f"Conectando à OLT {olt_name} ({olt_info['ip']})...")

        # Iniciar a conexão Telnet com a OLT Datacom
        tn = telnetlib.Telnet(olt_info["ip"])

        # Ler a solicitação de login e enviar o nome de usuário
        tn.read_until(b"username:", timeout=10)
        tn.write(olt_info["user"].encode('ascii') + b"\n")

        # Aguardar a solicitação de senha
        tn.read_until(b"password:", timeout=10)
        tn.write(olt_info["password"].encode('ascii') + b"\n")

        # Entrar no modo de configuração
        send_command(tn, "config")

        # Gerar o nome do arquivo de backup com base na OLT e na data/hora
        current_date_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        backup_filename = f"backup_{olt_name}_{current_date_time}.txt"

        # Comando para salvar o arquivo na OLT
        send_command(tn, f"save {backup_filename}")

        # Enviar o arquivo salvo para o servidor FTP
        backup_command = f'copy file "{backup_filename}" tftp://{ftp_ip}/{backup_filename}'
        send_command(tn, backup_command)

        # Aguardar até que o backup seja concluído
        time.sleep(30)  # Espera de 30 segundos para o backup concluir

        # Fechar a conexão Telnet
        tn.write(b"exit\n")
        tn.close()
        print(f"Backup da OLT {olt_name} concluído.")

        # Verificar se o arquivo foi salvo no diretório local do FTP
        local_backup_file = os.path.join(ftp_directory, backup_filename)
        if os.path.exists(local_backup_file):
            # Enviar o arquivo de backup via Telegram
            send_file_telegram(local_backup_file)
        else:
            print(f"Arquivo de backup {local_backup_file} não encontrado no FTP Server.")

    except Exception as e:
        print(f"Erro ao fazer backup da OLT {olt_name}: {e}")

# Executar o backup para todas as OLTs
for olt_name, olt_info in olts.items():
    backup_olt(olt_name, olt_info)
