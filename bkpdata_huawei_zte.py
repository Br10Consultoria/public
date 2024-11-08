import telnetlib
import paramiko
import time
from datetime import datetime

# Lista das OLTs
olts = {
    # OLTs Datacom
    "1": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "2": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "3": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "4": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "5": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "6": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "7": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "8": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "9": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },
    "10": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },

    # OLT ZTE (agora via Telnet)
    "ZTE": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    },

    # OLT Huawei
    "OLT_HUAWEI": {
        "ip": "",
        "user": "",
        "password": "",
        "type": "",
        "port": 
    }
}

# Configurações do TFTP Server DATACOM
tftp_ip = ""  # IP do servidor FTP

# Configurações do FTP Server HUAWEI ZTE
ftp_ip = ""  # IP do servidor FTP

# Função para enviar comandos via Telnet
def send_command(tn, command, wait_time=2):
    print(f"Enviando comando: {command}")
    tn.write(command.encode('ascii') + b"\n")
    time.sleep(wait_time)
    response = tn.read_very_eager().decode('ascii')
    print(f"Resposta: {response.strip()}")
    return response

# Função para realizar o backup das OLTs Datacom via Telnet
def backup_olt_datacom(olt_name, olt_info):
    try:
        print(f"Conectando à OLT {olt_name} ({olt_info['ip']}) via Telnet...")

        tn = telnetlib.Telnet(olt_info["ip"], olt_info["port"])

        # Login Telnet
        tn.read_until(b"login:", timeout=10)
        tn.write(olt_info["user"].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=10)
        tn.write(olt_info["password"].encode('ascii') + b"\n")

        # Receber a mensagem de boas-vindas e conexão
        tn.read_until(b"Welcome to the DmOS CLI", timeout=10)
        print(f"Conexão estabelecida na OLT {olt_name}")

        # Entrar no modo de configuração
        send_command(tn, "config")

        # Gerar o nome do arquivo de backup com base na OLT e na data/hora
        current_date_time = datetime.now().strftime("%d%m%y_%H%M")  # Formato ddmma hhmm
        backup_filename = f"backupolt{olt_name.lower()}{current_date_time}.txt"

        # Comando para salvar o backup (sem aspas duplas)
        send_command(tn, f'save {backup_filename}')

        # Aguardar 60 segundos antes de enviar para o TFTP server
        print(f"Aguardando 60 segundos para garantir que o backup foi salvo...")
        time.sleep(60)

        # Enviar o arquivo salvo para o servidor TFTP (sem aspas duplas)
        backup_command = f'copy file {backup_filename} tftp://{tftp_ip}'
        send_command(tn, backup_command)

        # Aguardar pela mensagem de "Transfer complete"
        tn.read_until(b"Transfer complete.", timeout=30)
        print(f"Backup da OLT {olt_name} transferido com sucesso para o TFTP.")

        # Fechar a conexão Telnet
        tn.write(b"exit\n")
        tn.close()
        print(f"Backup da OLT {olt_name} concluído.")

    except Exception as e:
        print(f"Erro ao fazer backup da OLT {olt_name}: {e}")

# Função para realizar o backup das OLTs ZTE via Telnet
def backup_zte_olt(olt_name, olt_info):
    try:
        print(f"Conectando à OLT {olt_name} ({olt_info['ip']}) via Telnet...")

        tn = telnetlib.Telnet(olt_info["ip"], olt_info["port"])

        # Login Telnet
        tn.read_until(b"login:", timeout=10)
        tn.write(olt_info["user"].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=10)
        tn.write(olt_info["password"].encode('ascii') + b"\n")

        # Entrar no modo de configuração
        send_command(tn, "configure terminal")

        # Configurar o servidor FTP para backup ZTE
        ftp_command = f"file-server manual-backup cfg server-index 1 ftp ipaddress {ftp_ip} user bkpoltztehuawei password 25342586"
        send_command(tn, ftp_command)

        # Fazer o backup
        send_command(tn, "manual-backup all")

        # Fechar a conexão Telnet
        tn.write(b"exit\n")
        tn.close()
        print(f"Backup da OLT {olt_name} via Telnet concluído.")

    except Exception as e:
        print(f"Erro ao fazer backup da OLT {olt_name}: {e}")

# Função para realizar o backup das OLTs Huawei via Telnet
def backup_olt_huawei(olt_name, olt_info):
    try:
        print(f"Conectando à OLT Huawei {olt_name} ({olt_info['ip']}) via Telnet...")

        tn = telnetlib.Telnet(olt_info["ip"], olt_info["port"])

        # Login Telnet
        tn.read_until(b"username:", timeout=10)
        tn.write(olt_info["user"].encode('ascii') + b"\n")
        tn.read_until(b"password:", timeout=10)
        tn.write(olt_info["password"].encode('ascii') + b"\n")

        # Entrar no modo "enable"
        tn.write(b"enable\n")
        tn.read_until(b"#", timeout=10)

        # Gerar o nome do arquivo de backup com base na OLT e na data/hora
        current_date_time = datetime.now().strftime("%d%m%y_%H%M")  # Formato ddmma hhmm
        backup_filename = f"backup_{olt_name.lower()}_{current_date_time}.txt"

        # Executar o comando de backup via FTP HUAWEI
        backup_command = f"backup configuration ftp {ftp_ip} {backup_filename}"
        send_command(tn, backup_command)
        
        # Pressionar Enter após o comando de backup (resposta para o prompt { <cr>|format<K> }:)
        tn.write(b"\n")

        # Aguardar a pergunta "Are you sure to continue? (y/n)" e responder "y"
        tn.read_until(b"Are you sure to continue? (y/n)", timeout=10)
        tn.write(b"y\n")  # Responder "y"

        # Aguardar 30 segundos antes de encerrar
        print(f"Aguardando 30 segundos para a conclusão do backup da OLT Huawei...")
        time.sleep(60)

        # Fechar a conexão Telnet
        tn.write(b"exit\n")
        tn.close()
        print(f"Backup da OLT {olt_name} concluído com sucesso.")

    except Exception as e:
        print(f"Erro ao fazer backup da OLT Huawei {olt_name}: {e}")

# Função principal que itera sobre todas as OLTs
def run_backups():
    print("Iniciando backups de todas as OLTs...\n")

    # Backup Datacom, ZTE e Huawei
    for olt_name, olt_info in olts.items():
        if olt_info["type"] == "telnet":
            if "HUAWEI" in olt_name.upper():
                backup_olt_huawei(olt_name, olt_info)
            else:
                backup_olt_datacom(olt_name, olt_info)
        elif olt_info["type"] == "telnet" and "ZTE" in olt_name.upper():
            backup_zte_olt(olt_name, olt_info)

# Executar o backup para todas as OLTs
run_backups()
