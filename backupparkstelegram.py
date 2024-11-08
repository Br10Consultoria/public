import telnetlib
import ftplib
import requests
import os
from datetime import datetime

# Informações da OLT e do FTP
olt_host = ""  # IP da OLT
olt_name = "OLT01"  # Nome da OLT para ser incluído no nome do arquivo
olt_user = ""
olt_password = "$"
ftp_user = ""
ftp_password = ""
ftp_host = ""  # IP ou domínio do servidor FTP Mikrotik

# Captura a data e hora atual
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
ftp_file = f"{olt_name}_backup_{timestamp}.bin"  # Nome do arquivo no FTP
local_file = f"C:\\scripts\\{ftp_file}"  # Local temporário para armazenar o backup

# Configurações do Telegram
telegram_bot_token = ""
telegram_chat_id = ""

def telnet_backup():
    try:
        # Conexão Telnet com a OLT
        tn = telnetlib.Telnet(olt_host)
        
        # Aguarda pela mensagem "Press <RETURN> to get started"
        tn.read_until(b"Press <RETURN> to get started")
        
        # Envia <ENTER> para prosseguir
        tn.write(b"\n")
        
        # Aguardar até aparecer o prompt de login
        tn.read_until(b"Username: ")
        tn.write(olt_user.encode('ascii') + b"\n")
        
        # Aguardar até aparecer o prompt de senha
        tn.read_until(b"Password: ")
        tn.write(olt_password.encode('ascii') + b"\n")

        # Executa o comando para realizar o backup na OLT
        backup_command = f"copy startup-config ftp://{ftp_host}/{ftp_file} {ftp_user} {ftp_password}\n"
        tn.write(backup_command.encode('ascii'))
        tn.write(b"exit\n")

        # Aguarda e fecha a conexão Telnet
        tn.read_all()
        tn.close()
        print("Backup realizado com sucesso na OLT.")
    except Exception as e:
        print(f"Erro durante o backup via Telnet: {e}")

# Função para baixar o arquivo de backup do servidor Mikrotik via FTP
def download_from_mikrotik(remote_file, local_file):
    try:
        with ftplib.FTP(ftp_host) as ftp:
            print(f"Conectando ao servidor FTP {ftp_host}...")
            ftp.login(ftp_user, ftp_password)
            print(f"Baixando o arquivo {remote_file} para {local_file}...")
            with open(local_file, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
        print(f"Arquivo {remote_file} baixado com sucesso.")
    except Exception as e:
        print(f"Erro ao baixar arquivo do FTP: {e}")

# Função para enviar arquivo via Telegram
def send_file_telegram(file_path):
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': telegram_chat_id, 'caption': f'Backup {os.path.basename(file_path)}'}
            print(f"Enviando o arquivo {file_path} para o Telegram...")
            response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            print(f"Arquivo {file_path} enviado com sucesso via Telegram.")
        else:
            print(f"Falha ao enviar arquivo via Telegram. Código de status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar arquivo para Telegram: {e}")

# Função principal para realizar o backup, baixar e enviar para o Telegram
def main():
    # Passo 1: Acessa a OLT e faz o backup
    telnet_backup()

    # Passo 2: Baixa o arquivo do FTP
    download_from_mikrotik(ftp_file, local_file)
    
    # Verifica se o arquivo foi baixado corretamente
    if os.path.exists(local_file):
        # Passo 3: Enviar o arquivo baixado para o Telegram
        send_file_telegram(local_file)
    else:
        print(f"Erro: Arquivo {local_file} não foi encontrado após o download.")

    # Passo 4: Limpa os arquivos temporários
    cleanup()

def cleanup():
    try:
        os.remove(local_file)
        print("Arquivo temporário excluído.")
    except OSError as e:
        print(f"Erro ao excluir o arquivo temporário: {e}")

if __name__ == "__main__":
    main()
