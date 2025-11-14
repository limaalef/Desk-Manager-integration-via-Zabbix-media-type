#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script interativo para gerenciar chamados e consultas na API Desk Manager
"""

import requests
import json
import os
import shutil
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime

# Tentar carregar python-dotenv se disponível
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Colors:
    """Classe para formatação de cores no terminal"""
    
    RESET = "\033[0m"
    PRIMARY_TEXT_COLOR = "\033[38;2;255;255;255m"
    SECONDARY_TEXT_COLOR = "\033[38;2;2;55;255m"
    SUCCESS_COLOR = "\033[38;2;141;191;141m"
    ERROR_COLOR = "\033[38;2;212;122;130m"
    WARNING_COLOR = "\033[38;2;238;234;190m"
    INFO_COLOR = "\033[38;2;116;151;228m"
    HIGHLIGHTED_COLOR = "\033[38;2;205;214;244m"
    UNHIGHLIGHTED_COLOR = "\033[38;2;162;169;193m"
    LINE_COLOR = "\033[38;2;54;54;84m"
    
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '╭'
    TOP_RIGHT = '╮'
    BOTTOM_LEFT = '╰'
    BOTTOM_RIGHT = '╯'
    
    MARGIN_LEFT = 4

    @staticmethod
    def clear_screen():
        """Limpa a tela"""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def print_banner(title="Desk Manager API", subtitle="Sistema de Gerenciamento de Chamados"):
        """Exibe banner do programa"""
        Colors.clear_screen()
        cols = shutil.get_terminal_size().columns
        
        print(f"\n{Colors.SECONDARY_TEXT_COLOR}{title.center(cols)}{Colors.PRIMARY_TEXT_COLOR}")
        if subtitle:
            print(f"{Colors.HIGHLIGHTED_COLOR}{subtitle.center(cols)}{Colors.PRIMARY_TEXT_COLOR}\n")

    @staticmethod
    def error(message, title="Erro"):
        Colors._box(title, message, Colors.ERROR_COLOR)

    @staticmethod
    def warning(message, title="Atenção"):
        Colors._box(title, message, Colors.WARNING_COLOR)

    @staticmethod
    def info(message, title="Info"):
        Colors._box(title, message, Colors.INFO_COLOR)

    @staticmethod
    def success(message, title="Sucesso"):
        Colors._box(title, message, Colors.SUCCESS_COLOR)

    @staticmethod
    def item(title: str = "", subtitle: Optional[str] = "", index: Optional[str] = ""):
        left_margin = Colors.MARGIN_LEFT
        padding = " " * left_margin

        if subtitle:
            line = f"{Colors.PRIMARY_TEXT_COLOR}{title}: {Colors.SECONDARY_TEXT_COLOR}{subtitle}{Colors.PRIMARY_TEXT_COLOR}"
        else:
            line = f"{Colors.PRIMARY_TEXT_COLOR}{title}{Colors.PRIMARY_TEXT_COLOR}"

        if index:
            line = f"{Colors.HIGHLIGHTED_COLOR}{index}. {line}"
    
        line = f"{padding}{line}"
        print(line)

    @staticmethod
    def _wrap_text(text, max_width):
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(word) > max_width:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = ""
                for i in range(0, len(word), max_width):
                    lines.append(word[i:i+max_width])
            elif len(current_line) + len(word) + 1 > max_width:
                lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "
        
        if current_line.strip():
            lines.append(current_line.strip())
        
        return lines if lines else [""]

    @staticmethod
    def _box(title, message, box_color=PRIMARY_TEXT_COLOR, text_color=PRIMARY_TEXT_COLOR):
        left_margin = Colors.MARGIN_LEFT
        message = str(message)
        title = str(title)

        total_width = shutil.get_terminal_size().columns
        max_width = total_width - 2 - 2 - left_margin*2
        
        all_lines = []
        for line in message.split('\n'):
            all_lines.extend(Colors._wrap_text(line, max_width))
        
        left_space = ' ' * left_margin
        top_table = Colors.HORIZONTAL * (max_width + 2)
        top_table = Colors.HORIZONTAL + f" {title} " + top_table[len(title) + 3:]
        top_line = f"{left_space}{box_color}{Colors.TOP_LEFT}{top_table}{Colors.TOP_RIGHT}"
        print(top_line)
        
        for line in all_lines:
            padding = ' ' * (max_width - len(line))
            content_line = f"{left_space}{box_color}{Colors.VERTICAL} {text_color}{line}{padding} {box_color}{Colors.VERTICAL}{text_color}"
            print(content_line)
        
        bottom_line = f"{left_space}{box_color}{Colors.BOTTOM_LEFT}{Colors.HORIZONTAL * (max_width + 2)}{Colors.BOTTOM_RIGHT}{text_color}"
        print(bottom_line)


class DeskManagerAPI:
    """Classe para interagir com a API do Desk Manager"""
    
    def __init__(self, api_url: str = "https://api.desk.ms"):
        self.api_url = api_url.rstrip('/')
        self.token = None
    
    def autenticar(self, chave_operador: str, chave_ambiente: str) -> bool:
        """Autentica na API do Desk Manager"""
        url = f"{self.api_url}/Login/autenticar"
        headers = {"Authorization": chave_operador}
        payload = {"PublicKey": chave_ambiente}

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if 'erro' not in data:
                    self.token = response.text.strip('"')
                    return True
                else:
                    Colors.error(f"Erro na autenticação: {data['erro']}")
                    return False
            else:
                Colors.error(f"Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            Colors.error(f"Erro ao autenticar: {str(e)}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        return {
            'Content-Type': 'application/json',
            'Authorization': self.token
        }
    
    def _fazer_requisicao(self, endpoint: str, payload: Dict) -> Optional[List[Dict]]:
        """Método genérico para fazer requisições à API"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if 'erro' in data:
                Colors.error(f"Erro na API: {data['erro']}")
                return []
            
            return data.get("root", data)
            
        except Exception as e:
            Colors.error(f"Erro na requisição para {endpoint}: {str(e)}")
            return []
    
    def listar_solicitantes(self, pesquisa: str = "") -> List[Dict]:
        """Lista solicitantes disponíveis"""
        payload = {
            "Pesquisa": pesquisa,
            "Ativo": "S",
            "Colunas": {
                "Chave": "on",
                "CodigoCliente": "on",
                "Cliente": "on",
                "Email": "on",
                "Nome": "on",
                "Sobrenome": "on"
            },
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Usuarios/lista", payload)
    
    def listar_auto_categorias(self) -> List[Dict]:
        """Lista auto-categorias disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "S",
            "Colunas": {
                "Chave": "on",
                "Assunto": "on",
                "NomeGrupo": "on",
                "Portal": "on"
            },
            "Ordem": [{"Coluna": "Assunto", "Direcao": "true"}]
        }
        return self._fazer_requisicao("AutoCategorias/lista", payload)
    
    def listar_categorias(self) -> List[Dict]:
        """Lista categorias disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "S",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Categorias/lista", payload)
    
    def listar_subcategorias(self) -> List[Dict]:
        """Lista subcategorias disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "S",
            "Ordem": [{"Coluna": "SubCategoria", "Direcao": "true"}]
        }
        return self._fazer_requisicao("SubCategorias/lista", payload)
    
    def listar_solicitacoes(self) -> List[Dict]:
        """Lista tipos de solicitação disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "S",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Solicitacoes/lista", payload)
    
    def listar_tipos_ocorrencia(self) -> List[Dict]:
        """Lista tipos de ocorrência disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "S",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("TipoOcorrencias/lista", payload)

    def listar_grupos(self) -> List[Dict]:
        """Lista grupos disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "1",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Grupos/lista", payload)

    def listar_forma_atendimento(self) -> List[Dict]:
        """Lista formas de atendimento disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "1",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("FormaAtendimento/lista", payload)
    
    def listar_status(self) -> List[Dict]:
        """Lista status disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "1",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Status/lista", payload)
    
    def listar_causa(self) -> List[Dict]:
        """Lista causas disponíveis"""
        payload = {
            "Pesquisa": "",
            "Ativo": "1",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("Causas/lista", payload)
    
    def listar_operadores(self) -> List[Dict]:
        """Lista operadores disponíveis"""
        payload = {
            "Colunas": {
                "Chave": "on",
                "Nome": "on",
                "Sobrenome": "on",
                "Email": "on",
                "OnOff": "on",
                "GrupoPrincipal": "on",
                "EmailGrupo": "on",
                "CodGrupo": "on"
            },  
            "Pesquisa": "",
            "Ativo": "S",
            "Ordem": [{"Coluna": "Nome", "Direcao": "true"}]
        }
        return self._fazer_requisicao("GerenteOperador/lista", payload)
    
    def abrir_chamado(self, dados_chamado: Dict) -> Optional[str]:
        """Abre um novo chamado"""
        url = f"{self.api_url}/ChamadosSuporte"
        
        try:
            response = requests.put(url, json=dados_chamado, headers=self._get_headers())
            response.raise_for_status()
            resultado = response.json()
            
            if 'erro' in resultado:
                Colors.error(f"Erro ao abrir chamado: {resultado['erro']}")
                return None
                
            return resultado
            
        except Exception as e:
            Colors.error(f"Erro ao abrir chamado: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                Colors.error(f"Detalhes: {e.response.text}")
            return None
    
    def interagir_chamado(self, dados_interacao: Dict) -> Optional[str]:
        """Adiciona interação a um chamado"""
        url = f"{self.api_url}/ChamadosSuporte/interagir"
        
        try:
            response = requests.put(url, json=dados_interacao, headers=self._get_headers())
            response.raise_for_status()
            resultado = response.json()
            
            if 'erro' in resultado:
                Colors.error(f"Erro ao interagir com chamado: {resultado['erro']}")
                return None
                
            return resultado
            
        except Exception as e:
            Colors.error(f"Erro ao interagir com chamado: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                Colors.error(f"Detalhes: {e.response.text}")
            return None


def exibir_menu_principal():
    """Exibe o menu principal"""
    print()
    Colors.item("OPERAÇÕES", index="")
    Colors.item("Abrir novo chamado", index="1")
    Colors.item("Interagir com chamado existente", index="2")
    print()
    Colors.item("CONSULTAS", index="")
    Colors.item("Listar solicitantes", index="3")
    Colors.item("Listar auto-categorias", index="4")
    Colors.item("Listar categorias", index="5")
    Colors.item("Listar subcategorias", index="6")
    Colors.item("Listar tipos de solicitação", index="7")
    Colors.item("Listar tipos de ocorrência", index="8")
    Colors.item("Listar grupos", index="9")
    Colors.item("Listar formas de atendimento", index="10")
    Colors.item("Listar status", index="11")
    Colors.item("Listar causas", index="12")
    Colors.item("Listar operadores", index="13")
    print()
    Colors.item("Sair", index="0")
    print()


def selecionar_opcao(lista: List[Dict], campo_exibicao: str, titulo: str, campo_codigo: str = "Chave") -> Optional[Dict]:
    """Exibe uma lista e permite selecionar uma opção"""
    if not lista:
        Colors.warning(f"Nenhum(a) {titulo.lower()} disponível.")
        return None
    
    print()
    Colors.item(titulo.upper())
    print()
    
    for i, item in enumerate(lista, 1):
        valor = item.get(campo_exibicao, "N/A")
        codigo = item.get(campo_codigo, "N/A")
        Colors.item(f"{valor}", subtitle=f"Código: {codigo}", index=str(i))
    
    Colors.item("Pular esta seleção", index="0")
    print()
    
    while True:
        try:
            opcao_input = input(f"{Colors.HIGHLIGHTED_COLOR}    Escolha uma opção: {Colors.PRIMARY_TEXT_COLOR}")
            opcao = int(opcao_input)
            
            if opcao == 0:
                return None
            if 1 <= opcao <= len(lista):
                return lista[opcao - 1]
            Colors.warning("Opção inválida!")
        except ValueError:
            Colors.warning("Digite um número válido!")
        except KeyboardInterrupt:
            print()
            return None


def exibir_lista(lista: List[Dict], titulo: str, campos: List[str]):
    """Exibe uma lista formatada"""
    if not lista:
        Colors.warning(f"Nenhum(a) {titulo.lower()} encontrado(a).")
        return
    
    Colors.print_banner(titulo, f"Total: {len(lista)} registro(s)")
    print()
    
    for i, item in enumerate(lista, 1):
        print(f"{Colors.HIGHLIGHTED_COLOR}    [{i}]{Colors.PRIMARY_TEXT_COLOR}")
        for campo in campos:
            valor = item.get(campo, "N/A")
            Colors.item(index=campo, title=str(valor))
        print()


def abrir_chamado_interativo(api: DeskManagerAPI):
    """Fluxo interativo para abrir um novo chamado"""
    Colors.print_banner("ABERTURA DE CHAMADO", "Preencha os dados do chamado")
    
    # 1. Solicitante
    print()
    solicitantes = api.listar_solicitantes()
    solicitante = selecionar_opcao(solicitantes, "Nome", "Selecione o Solicitante")
    
    if not solicitante:
        Colors.error("Solicitante é obrigatório!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 2. Auto-categoria (opcional)
    auto_categorias = api.listar_auto_categorias()
    auto_categoria = selecionar_opcao(auto_categorias, "Assunto", "Selecione a Auto-Categoria (opcional)")
    
    # 3. Assunto (se não usar auto-categoria)
    assunto = ""
    if not auto_categoria:
        print()
        assunto = input(f"{Colors.HIGHLIGHTED_COLOR}    Digite o Assunto do chamado: {Colors.PRIMARY_TEXT_COLOR}").strip()
        if not assunto:
            Colors.error("Assunto é obrigatório quando não há auto-categoria!")
            input("\nPressione ENTER para continuar...")
            return
    
    # 4. Descrição
    print()
    descricao = input(f"{Colors.HIGHLIGHTED_COLOR}    Digite a Descrição do chamado: {Colors.PRIMARY_TEXT_COLOR}").strip()
    if not descricao:
        Colors.error("Descrição é obrigatória!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 5. Tipo de Solicitação
    solicitacoes = api.listar_solicitacoes()
    solicitacao = selecionar_opcao(solicitacoes, "Nome", "Selecione o Tipo de Solicitação")
    
    if not solicitacao:
        Colors.error("Tipo de Solicitação é obrigatório!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 6. Tipo de Ocorrência
    tipos_ocorrencia = api.listar_tipos_ocorrencia()
    tipo_ocorrencia = selecionar_opcao(tipos_ocorrencia, "Nome", "Selecione o Tipo de Ocorrência", "Sequencia")
    
    if not tipo_ocorrencia:
        Colors.error("Tipo de Ocorrência é obrigatório!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 7. Subcategoria (se não usar auto-categoria)
    subcategoria = None
    if not auto_categoria:
        subcategorias = api.listar_subcategorias()
        subcategoria = selecionar_opcao(subcategorias, "SubCategoria", "Selecione a Subcategoria")
        
        if not subcategoria:
            Colors.error("Subcategoria é obrigatória quando não há auto-categoria!")
            input("\nPressione ENTER para continuar...")
            return
    
    # 8. Impacto e Urgência
    print()
    Colors.item("IMPACTO E URGÊNCIA")
    print()
    Colors.item("Alto", index="1")
    Colors.item("Médio", index="2")
    Colors.item("Baixo", index="3")
    print()
    
    impacto_map = {"1": "000001", "2": "000002", "3": "000003"}
    impacto_opcao = input(f"{Colors.HIGHLIGHTED_COLOR}    Selecione o Impacto: {Colors.PRIMARY_TEXT_COLOR}").strip()
    impacto = impacto_map.get(impacto_opcao, "000003")
    
    urgencia_opcao = input(f"{Colors.HIGHLIGHTED_COLOR}    Selecione a Urgência: {Colors.PRIMARY_TEXT_COLOR}").strip()
    urgencia = impacto_map.get(urgencia_opcao, "000003")
    
    # 9. Grupo (opcional)
    grupos = api.listar_grupos()
    grupo = selecionar_opcao(grupos, "Nome", "Selecione o Grupo para Transferir (opcional)")
    
    # Construir payload
    payload = {
        "TChamado": {
            "Solicitante": str(solicitante["Chave"]),
            "Email": solicitante.get("Email", ""),
            "Descricao": descricao,
            "Solicitacao": str(solicitacao["Chave"]),
            "TipoOcorrencia": str(tipo_ocorrencia["Sequencia"]),
            "Impacto": impacto,
            "Urgencia": urgencia,
            "EnviaEmail": "S"
        }
    }
    
    if auto_categoria:
        payload["TChamado"]["AutoCategoria"] = str(auto_categoria["Chave"])
    else:
        payload["TChamado"]["Assunto"] = assunto
    
    if subcategoria:
        payload["TChamado"]["Categoria"] = str(subcategoria["Chave"])
    
    if grupo:
        payload["TChamado"]["TransfCodGrupo"] = str(grupo["Chave"])
    
    # Exibir resumo
    print()
    Colors.item("RESUMO DO CHAMADO")
    print()
    Colors.item("Solicitante", subtitle=f"{solicitante['Nome']} {solicitante.get('Sobrenome', '')}")
    Colors.item("Email", subtitle=solicitante.get('Email', 'N/A'))
    
    if auto_categoria:
        Colors.item("Auto-Categoria", subtitle=auto_categoria['Assunto'])
    else:
        Colors.item("Assunto", subtitle=assunto)
    
    Colors.item("Tipo de Solicitação", subtitle=solicitacao['Nome'])
    Colors.item("Tipo de Ocorrência", subtitle=tipo_ocorrencia['Nome'])
    Colors.item("Descrição", subtitle=descricao[:50] + "..." if len(descricao) > 50 else descricao)
    
    if subcategoria:
        Colors.item("Subcategoria", subtitle=subcategoria['SubCategoria'])
    
    Colors.item("Impacto", subtitle=['', 'Alto', 'Médio', 'Baixo'][int(impacto[-1])])
    Colors.item("Urgência", subtitle=['', 'Alta', 'Média', 'Baixa'][int(urgencia[-1])])
    
    if grupo:
        Colors.item("Grupo", subtitle=grupo['Nome'])
    
    print()
    confirmar = input(f"{Colors.HIGHLIGHTED_COLOR}    Confirmar abertura do chamado? (S/N): {Colors.PRIMARY_TEXT_COLOR}").strip().upper()
    
    if confirmar == "S":
        print()
        Colors.info("Abrindo chamado...")
        chave_chamado = api.abrir_chamado(payload)
        
        if chave_chamado:
            Colors.success(f"Chamado aberto com sucesso!\nCódigo: {chave_chamado}")
        else:
            Colors.error("Erro ao abrir o chamado.")
    else:
        Colors.warning("Abertura cancelada.")
    
    input("\nPressione ENTER para continuar...")


def interagir_chamado_interativo(api: DeskManagerAPI):
    """Fluxo interativo para adicionar interação a um chamado"""
    Colors.print_banner("INTERAÇÃO COM CHAMADO", "Adicione uma interação ao chamado existente")
    
    # 1. Chave do chamado
    print()
    chave = input(f"{Colors.HIGHLIGHTED_COLOR}    Digite a chave do chamado (ex: 1025-000133): {Colors.PRIMARY_TEXT_COLOR}").strip()
    
    if not chave:
        Colors.error("Chave do chamado é obrigatória!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 2. Forma de atendimento
    formas = api.listar_forma_atendimento()
    forma = selecionar_opcao(formas, "Nome", "Selecione a Forma de Atendimento")
    
    if not forma:
        Colors.error("Forma de atendimento é obrigatória!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 3. Status
    status_list = api.listar_status()
    status = selecionar_opcao(status_list, "Nome", "Selecione o Status")
    
    if not status:
        Colors.error("Status é obrigatório!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 4. Descrição
    print()
    descricao = input(f"{Colors.HIGHLIGHTED_COLOR}    Digite a descrição da interação: {Colors.PRIMARY_TEXT_COLOR}").strip()
    
    if not descricao:
        Colors.error("Descrição é obrigatória!")
        input("\nPressione ENTER para continuar...")
        return
    
    # 5. Operador (opcional)
    operadores = api.listar_operadores()
    operador = selecionar_opcao(operadores, "Nome", "Selecione o Operador (opcional)")
    
    # 6. Grupo (opcional)
    grupos = api.listar_grupos()
    grupo = selecionar_opcao(grupos, "Nome", "Selecione o Grupo (opcional)")
    
    # Gerar data e hora
    now = datetime.now()
    data_interacao = now.strftime("%d-%m-%Y")
    hora_inicial = (now.replace(minute=now.minute-2)).strftime("%H:%M:%S")
    hora_final = now.strftime("%H:%M")
    
    # Construir payload
    payload = {
        "Chave": chave,
        "TChamado": {
            "CodFormaAtendimento": str(forma["Chave"]),
            "CodStatus": str(status["Sequencia"]),
            "Descricao": descricao,
            "EnviarEmail": "N",
            "EnvBase": "N",
            "DataInteracao": data_interacao,
            "HoraInicial": hora_inicial,
            "HoraFinal": hora_final,
            "PrimeiroAtendimento": "N",
            "SegundoAtendimento": "N"
        }
    }
    
    if operador:
        payload["TChamado"]["CodOperador"] = str(operador["Chave"])
    
    if grupo:
        payload["TChamado"]["CodGrupo"] = str(grupo["Chave"])

    print(payload)
    
    # Exibir resumo
    print()
    Colors.item("RESUMO DA INTERAÇÃO")
    print()
    Colors.item("Chamado", subtitle=chave)
    Colors.item("Forma de Atendimento", subtitle=forma['Nome'])
    Colors.item("Status", subtitle=status['Nome'])
    Colors.item("Descrição", subtitle=descricao[:50] + "..." if len(descricao) > 50 else descricao)
    
    if operador:
        Colors.item("Operador", subtitle=operador['Nome'])
    
    if grupo:
        Colors.item("Grupo", subtitle=grupo['Nome'])
    
    Colors.item("Data/Hora", subtitle=f"{data_interacao} {hora_inicial} - {hora_final}")
    
    print()
    confirmar = input(f"{Colors.HIGHLIGHTED_COLOR}    Confirmar interação? (S/N): {Colors.PRIMARY_TEXT_COLOR}").strip().upper()
    
    if confirmar == "S":
        print()
        Colors.info("Adicionando interação...")
        resultado = api.interagir_chamado(payload)
        
        if resultado:
            Colors.success(f"Interação adicionada com sucesso!\nResultado: {resultado}")
        else:
            Colors.error("Erro ao adicionar interação.")
    else:
        Colors.warning("Interação cancelada.")
    
    input("\nPressione ENTER para continuar...")


def main():
    """Função principal"""
    
    # Carregar credenciais do .env
    CHAVE_OPERADOR = os.getenv('CHAVE_OPERADOR')
    CHAVE_AMBIENTE = os.getenv('CHAVE_AMBIENTE')
    
    # Verificar se as credenciais foram configuradas
    if not CHAVE_OPERADOR or not CHAVE_AMBIENTE:
        Colors.clear_screen()
        Colors.error(
            "Credenciais não configuradas!\n\n" +
            "Para configurar:\n" +
            "1. Edite o arquivo .env e preencha suas credenciais\n" +
            "2. Execute o script novamente"
        )
        return
    
    # Inicializa a API
    api = DeskManagerAPI()
    
    # Autenticação
    Colors.print_banner()
    print()
    Colors.info("Autenticando na API...")

    if not api.autenticar(CHAVE_OPERADOR, CHAVE_AMBIENTE):
        Colors.error("Falha na autenticação. Verifique suas credenciais.")
        return
    
    Colors.success("Autenticação realizada com sucesso!")
    
    # Loop principal
    while True:
        Colors.print_banner()
        exibir_menu_principal()
        
        try:
            opcao_input = input(f"{Colors.HIGHLIGHTED_COLOR}    Escolha uma opção: {Colors.PRIMARY_TEXT_COLOR}")
            opcao = int(opcao_input)
        except ValueError:
            Colors.warning("Opção inválida!")
            input("\nPressione ENTER para continuar...")
            continue
        except KeyboardInterrupt:
            print()
            Colors.info("Encerrando o sistema...")
            break
        
        # Abrir novo chamado
        if opcao == 1:
            abrir_chamado_interativo(api)
        
        # Interagir com chamado
        elif opcao == 2:
            interagir_chamado_interativo(api)
        
        # Listar solicitantes
        elif opcao == 3:
            Colors.print_banner("CONSULTA", "Solicitantes")
            solicitantes = api.listar_solicitantes()
            exibir_lista(solicitantes, "Solicitantes", ["Chave", "Nome", "Sobrenome", "Email", "Cliente"])
            input("\nPressione ENTER para continuar...")
        
        # Listar auto-categorias
        elif opcao == 4:
            Colors.print_banner("CONSULTA", "Auto-Categorias")
            auto_categorias = api.listar_auto_categorias()
            exibir_lista(auto_categorias, "Auto-Categorias", ["Chave", "Assunto", "NomeGrupo", "Portal"])
            input("\nPressione ENTER para continuar...")
        
        # Listar categorias
        elif opcao == 5:
            Colors.print_banner("CONSULTA", "Categorias")
            categorias = api.listar_categorias()
            exibir_lista(categorias, "Categorias", ["Chave", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar subcategorias
        elif opcao == 6:
            Colors.print_banner("CONSULTA", "Subcategorias")
            subcategorias = api.listar_subcategorias()
            exibir_lista(subcategorias, "Subcategorias", ["Chave", "SubCategoria"])
            input("\nPressione ENTER para continuar...")
        
        # Listar tipos de solicitação
        elif opcao == 7:
            Colors.print_banner("CONSULTA", "Tipos de Solicitação")
            solicitacoes = api.listar_solicitacoes()
            exibir_lista(solicitacoes, "Tipos de Solicitação", ["Chave", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar tipos de ocorrência
        elif opcao == 8:
            Colors.print_banner("CONSULTA", "Tipos de Ocorrência")
            tipos_ocorrencia = api.listar_tipos_ocorrencia()
            exibir_lista(tipos_ocorrencia, "Tipos de Ocorrência", ["Sequencia", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar grupos
        elif opcao == 9:
            Colors.print_banner("CONSULTA", "Grupos")
            grupos = api.listar_grupos()
            exibir_lista(grupos, "Grupos", ["Chave", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar formas de atendimento
        elif opcao == 10:
            Colors.print_banner("CONSULTA", "Formas de Atendimento")
            formas = api.listar_forma_atendimento()
            exibir_lista(formas, "Formas de Atendimento", ["Chave", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar status
        elif opcao == 11:
            Colors.print_banner("CONSULTA", "Status")
            status_list = api.listar_status()
            exibir_lista(status_list, "Status", ["Sequencia", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar causas
        elif opcao == 12:
            Colors.print_banner("CONSULTA", "Causa")
            causa_list = api.listar_causa()
            exibir_lista(causa_list, "Causa", ["Sequencia", "Nome"])
            input("\nPressione ENTER para continuar...")
        
        # Listar operadores
        elif opcao == 13:
            Colors.print_banner("CONSULTA", "Operadores")
            operadores = api.listar_operadores()
            exibir_lista(operadores, "Operadores", ["Chave", "Nome", "Sobrenome", "Email", "GrupoPrincipal"])
            input("\nPressione ENTER para continuar...")
        
        # Sair
        elif opcao == 0:
            Colors.info("Encerrando o sistema...")
            break
        
        else:
            Colors.warning("Opção inválida!")
            input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    main()