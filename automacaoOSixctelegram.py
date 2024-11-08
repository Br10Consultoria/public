import requests
import base64
import json
import time
from datetime import datetime

# Configurações de acesso à API
host = ''  # Insira o domínio correto aqui
url_consulta_os = f"https://{host}/webservice/v1/su_oss_chamado"
token = "".encode('utf-8')

# Configurações do Telegram
telegram_token = ""
chat_id = ""

def gerar_headers():
    """Gera o cabeçalho de autorização atualizado para cada requisição."""
    headers = {
        'ixcsoft': 'listar',
        'Authorization': 'Basic {}'.format(base64.b64encode(token).decode('utf-8')),
        'Content-Type': 'application/json'
    }
    return headers

# Momento de início do script para filtrar chamados
inicio_script = datetime.now()
# Conjunto de IDs de OS já enviadas
os_enviadas = set()

def consulta_os(status):
    """Consulta a API para obter todas as OS com o status especificado."""
    payload = json.dumps({
        "qtype": "su_oss_chamado.status",
        "query": status,
        "oper": "=",
        "page": "1",
        "rp": "1000",
        "sortname": "su_oss_chamado.id",
        "sortorder": "desc"
    })
    
    response = requests.post(url_consulta_os, headers=gerar_headers(), data=payload)
    if response.status_code == 200:
        ordens = response.json().get("registros", [])
        return ordens
    else:
        print(f"Erro ao consultar API: Status {response.status_code} - {response.text}")
    return []

def consulta_cliente(id_cliente):
    """Consulta a API para obter a razão social do cliente usando o id_cliente."""
    url = f"https://{host}/webservice/v1/cliente"
    payload = json.dumps({
        "qtype": "cliente.id",
        "query": id_cliente,
        "oper": "=",
        "page": "1",
        "rp": "1",
        "sortname": "cliente.id",
        "sortorder": "asc"
    })
    
    response = requests.post(url, headers=gerar_headers(), data=payload)
    if response.status_code == 200:
        cliente = response.json().get("registros", [])
        if cliente:
            return cliente[0].get("razao", "N/A")
    return "N/A"

def consulta_funcionario(id_tecnico):
    """Consulta a API para obter o nome do técnico usando o id_tecnico."""
    url = f"https://{host}/webservice/v1/funcionarios"
    payload = json.dumps({
        "qtype": "funcionarios.id",
        "query": id_tecnico,
        "oper": "=",
        "page": "1",
        "rp": "1",
        "sortname": "funcionarios.id",
        "sortorder": "asc"
    })
    
    response = requests.post(url, headers=gerar_headers(), data=payload)
    if response.status_code == 200:
        funcionario = response.json().get("registros", [])
        if funcionario:
            return funcionario[0].get("funcionarios", "N/A")
    return "N/A"

def enviar_telegram(mensagem):
    """Envia uma mensagem formatada para o Telegram."""
    url_telegram = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    response = requests.post(url_telegram, json=payload)
    return response.status_code == 200

def main():
    print(f"Iniciando a consulta à API a partir de {inicio_script}...")  # Log do início
    while True:
        now = datetime.now()
        
        # Processar chamados finalizados
        ordens_finalizadas = consulta_os("F")
        for ordem in ordens_finalizadas:
            id_ticket = ordem.get("id", "N/A")
            if id_ticket in os_enviadas:
                continue  # Ignora se a OS já foi enviada
            
            # Extraindo informações do chamado
            tecnico_id = ordem.get("id_tecnico", "N/A")
            cliente_id = ordem.get("id_cliente", "N/A")
            endereco = ordem.get("endereco", "N/A")
            data_abertura = ordem.get("data_abertura", "N/A")
            data_inicio = ordem.get("data_inicio", "N/A")
            data_hora_encaminhado = ordem.get("data_hora_encaminhado", "N/A")
            data_hora_assumido = ordem.get("data_hora_assumido", "N/A")
            data_hora_execucao = ordem.get("data_hora_execucao", "N/A")
            data_final = ordem.get("data_final", "N/A")
            data_fechamento = ordem.get("data_fechamento", "N/A")
            latitude = ordem.get("latitude", "N/A")
            longitude = ordem.get("longitude", "N/A")
            mensagem_resposta = ordem.get("mensagem_resposta", "N/A")

            # Consulta nomes do técnico e do cliente
            nome_tecnico = consulta_funcionario(tecnico_id)
            nome_cliente = consulta_cliente(cliente_id)

            # Formatar e enviar mensagem para OS finalizada
            mensagem = (
                f"🔔 <b>Ordem de Serviço Finalizada</b> 🔔\n"
                f"<b>Ordem de Serviço:</b> {id_ticket}\n"
                f"<b>Cliente:</b> {nome_cliente} (ID: {cliente_id})\n"
                f"<b>Técnico:</b> {nome_tecnico} (ID: {tecnico_id})\n"
                f"<b>Endereço:</b> {endereco}\n"
                f"<b>Data de Abertura:</b> {data_abertura}\n"
                f"<b>Data de Início:</b> {data_inicio}\n"
                f"<b>Data e Hora Encaminhado:</b> {data_hora_encaminhado}\n"
                f"<b>Data e Hora Assumido:</b> {data_hora_assumido}\n"
                f"<b>Data e Hora Execução:</b> {data_hora_execucao}\n"
                f"<b>Data Final:</b> {data_final}\n"
                f"<b>Data de Fechamento:</b> {data_fechamento}\n"
                f"<b>Latitude:</b> {latitude}\n"
                f"<b>Longitude:</b> {longitude}\n"
                f"<b>Descrição:</b> {mensagem_resposta}\n"
            )
            if enviar_telegram(mensagem):
                print(f"Mensagem enviada para o Telegram com sucesso para OS {id_ticket}.")
                os_enviadas.add(id_ticket)
        
        # Processar novos chamados abertos
        ordens_abertas = consulta_os("A")
        for ordem in ordens_abertas:
            id_ticket = ordem.get("id", "N/A")
            if id_ticket in os_enviadas:
                continue
            
            # Extraindo informações do chamado
            tecnico_id = ordem.get("id_tecnico", "N/A")
            cliente_id = ordem.get("id_cliente", "N/A")
            endereco = ordem.get("endereco", "N/A")
            data_abertura = ordem.get("data_abertura", "N/A")
            latitude = ordem.get("latitude", "N/A")
            longitude = ordem.get("longitude", "N/A")

            # Consulta nomes do técnico e do cliente
            nome_tecnico = consulta_funcionario(tecnico_id)
            nome_cliente = consulta_cliente(cliente_id)

            # Formatar e enviar mensagem para OS aberta
            mensagem = (
                f"📂 <b>Novo Chamado Aberto</b> 📂\n"
                f"<b>Ordem de Serviço:</b> {id_ticket}\n"
                f"<b>Cliente:</b> {nome_cliente} (ID: {cliente_id})\n"
                f"<b>Técnico:</b> {nome_tecnico} (ID: {tecnico_id})\n"
                f"<b>Endereço:</b> {endereco}\n"
                f"<b>Data de Abertura:</b> {data_abertura}\n"
                f"<b>Latitude:</b> {latitude}\n"
                f"<b>Longitude:</b> {longitude}\n"
            )
            if enviar_telegram(mensagem):
                print(f"Mensagem de abertura enviada para OS {id_ticket}.")
                os_enviadas.add(id_ticket)
        
        # Aguarda 1 minuto antes da próxima consulta
        print("Aguardando 1 minuto para a próxima consulta...")
        time.sleep(60)

if __name__ == "__main__":
    main()
