import telnetlib
import ftplib
import requests
import os
from datetime import datetime

# Informações da OLT e do FTP
olt_host = ""  # IP da OLT
olt_name = "OLT01"  # Nome da OLT para ser incluído no nome do arquivo
olt_user = ""
olt_password = ""
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

def download_backup():
    try:
        # Conectar ao servidor FTP para baixar o arquivo
        ftp = ftplib.FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)

        with open(local_file, 'wb') as f:
            ftp.retrbinary(f"RETR {ftp_file}", f.write)
        
        ftp.quit()
        print("Backup baixado com sucesso do FTP.")
    except Exception as e:
        print(f"Erro durante o download do backup: {e}")

def send_to_telegram():
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
        files = {'document': open(local_file, 'rb')}
        data = {'chat_id': telegram_chat_id, 'caption': f'Backup da {olt_name} realizado com sucesso em {timestamp}.'}
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print("Backup enviado com sucesso para o Telegram.")
        else:
            print(f"Erro ao enviar o backup para o Telegram: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Erro durante o envio para o Telegram: {e}")

def cleanup():
    try:
        os.remove(local_file)
        print("Arquivo temporário excluído.")
    except OSError as e:
        print(f"Erro ao excluir o arquivo temporário: {e}")

if __name__ == "__main__":
    telnet_backup()        # Passo 1: Acessa a OLT e faz o backup
    download_backup()      # Passo 2: Baixa o arquivo do FTP
    send_to_telegram()     # Passo 3: Envia o arquivo para o Telegram
    cleanup()              # Passo 4: Limpa os arquivos temporários
