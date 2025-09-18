#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zabbix Trend Export Tool - Versão Melhorada
Descrição: Script para extrair tendências históricas de itens selecionados de CPU, Memória, Disco e Rede
Autor: Luis Amaral (versão original) - Melhorado por Manus
Data: 2025-09-18
Versão: 0.2.0
Licença: Apache-2.0
"""

import os
import csv
import time
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

try:
    from pyzabbix import ZabbixAPI
    from tqdm import tqdm
    from colorama import init, Fore
    import requests
except ImportError as e:
    print(f"Erro: Dependência não encontrada - {e}")
    print("Execute: pip install -r requirements.txt")
    exit(1)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zabbix_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar colorama
init(autoreset=True)


class ZabbixTrendExporter:
    """Classe principal para exportação de tendências do Zabbix"""
    
    def __init__(self, url: str, username: str, password: str):
        """
        Inicializa o exportador de tendências
        
        Args:
            url: URL do frontend do Zabbix
            username: Nome de usuário do Zabbix
            password: Senha do usuário
        """
        self.url = url
        self.username = username
        self.password = password
        self.api = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Conecta à API do Zabbix
        
        Returns:
            bool: True se conectado com sucesso, False caso contrário
        """
        try:
            self.api = ZabbixAPI(self.url)
            
            # Desabilitar verificação SSL se HTTPS
            if "https" in self.url:
                requests.packages.urllib3.disable_warnings()
                self.api.session.verify = False
                
            self.api.login(self.username, self.password)
            self.connected = True
            logger.info(f"Conectado ao Zabbix em {self.url}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Zabbix: {e}")
            return False
    
    def disconnect(self):
        """Desconecta da API do Zabbix"""
        if self.api and self.connected:
            try:
                self.api.user.logout()
                self.connected = False
                logger.info("Desconectado do Zabbix")
            except Exception as e:
                logger.warning(f"Erro ao desconectar: {e}")
    
    def get_host_by_name(self, hostname: str) -> Optional[Dict]:
        """
        Busca um host pelo nome
        
        Args:
            hostname: Nome do host
            
        Returns:
            Dict com informações do host ou None se não encontrado
        """
        try:
            hosts = self.api.host.get(
                output=["hostid", "name", "host"],
                filter={"host": hostname},
                limit=1
            )
            
            if not hosts:
                logger.error(f"Host '{hostname}' não encontrado")
                return None
                
            return hosts[0]
            
        except Exception as e:
            logger.error(f"Erro ao buscar host: {e}")
            return None
    
    def get_metrics_by_type(self, hostid: str, metric_type: str) -> List[Dict]:
        """
        Busca métricas por tipo
        
        Args:
            hostid: ID do host
            metric_type: Tipo de métrica (cpu, memory, disk, network_in, network_out)
            
        Returns:
            Lista de métricas encontradas
        """
        try:
            search_params = {
                'cpu': {"key_": "system.cpu.util"},
                'memory': {"key_": "memory", "units": "%", "name": "use"},
                'disk': {"key_": "vfs.fs.size", "units": "%", "name": "Free"},
                'network_in': {"key_": "net.if.in", "units": "bps"},
                'network_out': {"key_": "net.if.out", "units": "bps"}
            }
            
            if metric_type not in search_params:
                logger.warning(f"Tipo de métrica '{metric_type}' não suportado")
                return []
            
            items = self.api.item.get(
                output=["itemid", "name", "key_", "units"],
                hostids=hostid,
                search=search_params[metric_type]
            )
            
            return items
            
        except Exception as e:
            logger.error(f"Erro ao buscar métricas do tipo {metric_type}: {e}")
            return []
    
    def get_all_metrics(self, hostid: str, selected_types: List[str] = None) -> List[str]:
        """
        Coleta IDs de todas as métricas selecionadas
        
        Args:
            hostid: ID do host
            selected_types: Lista de tipos de métricas a coletar
            
        Returns:
            Lista de IDs das métricas
        """
        if selected_types is None:
            selected_types = ['cpu', 'memory', 'disk', 'network_in', 'network_out']
        
        metric_ids = []
        
        for metric_type in selected_types:
            items = self.get_metrics_by_type(hostid, metric_type)
            
            if metric_type in ['cpu', 'memory'] and items:
                # Para CPU e memória, pegar apenas o primeiro item
                metric_ids.append(items[0]['itemid'])
                logger.info(f"Adicionada métrica {metric_type}: {items[0]['name']}")
            else:
                # Para disco e rede, pegar todos os itens
                for item in items:
                    metric_ids.append(item['itemid'])
                    logger.info(f"Adicionada métrica {metric_type}: {item['name']}")
        
        return metric_ids
    
    @staticmethod
    def date_to_timestamp(date_str: str) -> float:
        """
        Converte data em timestamp
        
        Args:
            date_str: Data no formato DD/MM/YYYY ou DD/MM/YYYY HH:MM:SS
            
        Returns:
            Timestamp Unix
        """
        try:
            # Tentar primeiro com hora
            if len(date_str.split()) > 1:
                dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            else:
                dt = datetime.strptime(f"{date_str} 00:00:00", "%d/%m/%Y %H:%M:%S")
            
            return time.mktime(dt.timetuple())
            
        except ValueError as e:
            logger.error(f"Erro ao converter data '{date_str}': {e}")
            raise
    
    @staticmethod
    def timestamp_to_date(timestamp: int) -> str:
        """
        Converte timestamp para data legível
        
        Args:
            timestamp: Timestamp Unix
            
        Returns:
            Data formatada
        """
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timestamp))
    
    def export_trends(self, hostname: str, date_from: str, date_till: str, 
                     output_file: str = None, selected_metrics: List[str] = None) -> bool:
        """
        Exporta tendências para CSV
        
        Args:
            hostname: Nome do host
            date_from: Data inicial
            date_till: Data final
            output_file: Nome do arquivo de saída
            selected_metrics: Tipos de métricas a exportar
            
        Returns:
            bool: True se exportação bem-sucedida
        """
        if not self.connected:
            logger.error("Não conectado ao Zabbix")
            return False
        
        try:
            # Buscar host
            host = self.get_host_by_name(hostname)
            if not host:
                return False
            
            # Obter métricas
            metric_ids = self.get_all_metrics(host['hostid'], selected_metrics)
            if not metric_ids:
                logger.error("Nenhuma métrica encontrada")
                return False
            
            # Converter datas
            timestamp_from = self.date_to_timestamp(date_from)
            timestamp_till = self.date_to_timestamp(date_till)
            
            # Nome do arquivo de saída
            if not output_file:
                output_file = f'ZABBIX-{hostname}-TREND-EXPORT-{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            # Buscar tendências
            logger.info("Buscando dados de tendências...")
            trends = self.api.trend.get(
                output=["itemid", "clock", "value_avg", "value_min", "value_max"],
                itemids=metric_ids,
                time_from=int(timestamp_from),
                time_till=int(timestamp_till)
            )
            
            if not trends:
                logger.warning("Nenhuma tendência encontrada no período especificado")
                return False
            
            # Exportar para CSV
            logger.info(f"Exportando {len(trends)} registros para {output_file}")
            
            with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['HOST', 'DATE', 'METRIC', 'VALUE_AVG', 'VALUE_MIN', 'VALUE_MAX'])
                
                for trend in tqdm(trends, ascii=True, desc="Exportando tendências"):
                    try:
                        # Buscar nome do item
                        item = self.api.item.get(
                            output=["itemid", "name"],
                            itemids=trend['itemid']
                        )
                        
                        if item:
                            item_name = item[0]['name']
                        else:
                            item_name = f"Item ID: {trend['itemid']}"
                        
                        writer.writerow([
                            host['name'],
                            self.timestamp_to_date(int(trend['clock'])),
                            item_name,
                            trend['value_avg'],
                            trend['value_min'],
                            trend['value_max']
                        ])
                        
                    except Exception as e:
                        logger.warning(f"Erro ao processar tendência: {e}")
                        continue
            
            logger.info(f"Exportação concluída: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro durante exportação: {e}")
            return False


def create_config_file(filename: str = "zabbix_config.json"):
    """Cria arquivo de configuração de exemplo"""
    config = {
        "url": "http://localhost/zabbix",
        "username": "Admin",
        "password": "zabbix",
        "default_metrics": ["cpu", "memory", "disk", "network_in", "network_out"]
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print(f"Arquivo de configuração criado: {filename}")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Exportador de Tendências do Zabbix - Versão Melhorada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s -u Admin -p zabbix -s http://localhost/zabbix -n 'Zabbix Server' -f 01/01/2021 -t 02/01/2021
  %(prog)s --config zabbix_config.json -n 'Zabbix Server' -f 01/01/2021 -t 02/01/2021
  %(prog)s --create-config
        """
    )
    
    # Argumentos principais
    parser.add_argument("-u", "--user", help="Usuário do Zabbix")
    parser.add_argument("-p", "--password", help="Senha do usuário")
    parser.add_argument("-s", "--server", help="URL do frontend do Zabbix")
    parser.add_argument("-n", "--name", help="Nome do host")
    parser.add_argument("-f", "--from", dest="date_from", help="Data inicial (DD/MM/YYYY)")
    parser.add_argument("-t", "--till", dest="date_till", help="Data final (DD/MM/YYYY)")
    
    # Argumentos opcionais
    parser.add_argument("-o", "--output", help="Nome do arquivo de saída")
    parser.add_argument("-c", "--config", help="Arquivo de configuração JSON")
    parser.add_argument("-m", "--metrics", nargs='+', 
                       choices=['cpu', 'memory', 'disk', 'network_in', 'network_out'],
                       help="Tipos de métricas a exportar")
    parser.add_argument("--create-config", action="store_true", 
                       help="Criar arquivo de configuração de exemplo")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verboso")
    
    args = parser.parse_args()
    
    # Configurar nível de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Criar arquivo de configuração
    if args.create_config:
        create_config_file()
        return
    
    # Carregar configuração se especificada
    config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuração carregada de {args.config}")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return
    
    # Obter parâmetros (argumentos têm prioridade sobre configuração)
    url = args.server or config.get('url')
    username = args.user or config.get('username')
    password = args.password or config.get('password')
    hostname = args.name
    date_from = args.date_from
    date_till = args.date_till
    selected_metrics = args.metrics or config.get('default_metrics')
    
    # Validar parâmetros obrigatórios
    if not all([url, username, password, hostname, date_from, date_till]):
        parser.error("Parâmetros obrigatórios: url, username, password, hostname, date_from, date_till")
    
    # Limpar tela
    os.system('cls') if os.name == 'nt' else os.system('clear')
    
    # Executar exportação
    exporter = ZabbixTrendExporter(url, username, password)
    
    try:
        if exporter.connect():
            success = exporter.export_trends(
                hostname=hostname,
                date_from=date_from,
                date_till=date_till,
                output_file=args.output,
                selected_metrics=selected_metrics
            )
            
            if success:
                print(f"{Fore.GREEN}Exportação concluída com sucesso!")
            else:
                print(f"{Fore.RED}Falha na exportação")
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
    finally:
        exporter.disconnect()


if __name__ == '__main__':
    main()

