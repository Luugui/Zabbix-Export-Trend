#!/usr/bin/env python
# -*- coding: utf-8 -*-
#filename            : zabbix-export-trends.py
#description         : Script for extracting historical trends of selected Host's CPU, Memory, Disk and Network In/Out items 
#author              : Luis Amaral
#email               : luisguilhermester at live dot com
#date                : 2021/10/13
#version             : 0.1.1
#usage               : $ python zabbix-export-trends.py -u Admin -p zabbix -s http://localhost/zabbix -n 'Zabbix Server' -f 01/01/2021 -t 02/01/2021
#notes               : All parameters are required
#license             : Apache-2.0
#python_version      : 3.9.2
#==============================================================================

from pyzabbix import ZabbixAPI
from tqdm import tqdm
from datetime import datetime
from colorama import init, Fore
import time, csv, os, argparse

# Configurando os argumentos // Configuring the arguments

init(autoreset=True)

parser = argparse.ArgumentParser(description="Extract trend from select host")
parser.add_argument("-u", "--user", required=True, help="Zabbix user")
parser.add_argument("-p", "--password", required=True, help="Zabbix user password")
parser.add_argument("-s", "--server", required=True, help="Zabbix frontend URL")
parser.add_argument("-n", "--name", required=True, help="Name of host")
parser.add_argument("-f", "--from", required=True, help="Time from")
parser.add_argument("-t", "--till", required=True, help="Time till")
args = vars(parser.parse_args())

# VARIAVEIS DE CONFIGURAÇÃO DO RELATÓRIO //  REPORT'S VARIABLES 
URL=args['server']
LOGIN=args['user']
SENHA=args['password']
SERVIDOR=args['name']
INICIO=f"{args['from']}"
FIM=f"{args['till']} 23:59:59"
REPORT_NAME = f'ZABBIX-{SERVIDOR}-TREND-EXPORT.csv'




# CONECTANDO AO ZABBIX // CONNECT TO ZABBIX
os.system('cls') if os.name == 'nt' else os.system('clear')
app = ZabbixAPI(URL)
if "https" in URL:
    import requests
    requests.packages.urllib3.disable_warnings()
    app.session.verify = False
app.login(LOGIN,SENHA)
print(f"[{Fore.GREEN}{datetime.now()}{Fore.WHITE}] Connected to Zabbix!")

LIST_HOSTS = app.host.get(output=["hostid","name"],filter={"host": SERVIDOR},limit=1)

# Função para coleta dos ids dos items de CPU, Memória, Disco e Rede // Function to collect ids from items (CPU, Mem, Disk and Interfaces)

def get_metrics(host):
    try:
        cpu = app.item.get(output=["itemid","name"],hostids=host,search={"key_": "system.cpu.util"})
        mem = app.item.get(output=["itemid","name"],hostids=host,search={"key_": "memory", "units": "%", "name": "use"})
        disk = app.item.get(output=["itemid","name"],hostids=host,search={"key_": "vfs.fs.size", "units": "%", "name": "Free"})
        net_in = app.item.get(output=["itemd","name"],hostids=host,search={"key_": "net.if.in", "units": "bps"})
        net_out = app.item.get(output=["itemd","name"],hostids=host,search={"key_": "net.if.out", "units": "bps"})
        metrics = [dk['itemid'] for dk in disk]
        for ntin in net_in:
            metrics.append(ntin['itemid'])
        for ntout in net_out:
            metrics.append(ntout['itemid'])
        metrics.append(cpu[0]['itemid'])
        metrics.append(mem[0]['itemid'])

        
        return metrics
    except:
        return 0

# Função para converter data em Timestamp aceito pelo Zabbix // Function to convert human date to timestam accepted by Zabbix

def date_to_timestamp(data):
    try:
        data == datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m/%Y")
        DATA_INICIO = time.mktime(time.strptime("{} 00:00:00".format(data), "%d/%m/%Y %H:%M:%S"))

        return DATA_INICIO
    except:
        data == datetime.strptime(data, "%d/%m/%Y %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        DATA_INICIO = time.mktime(time.strptime(data, "%d/%m/%Y %H:%M:%S"))

        return DATA_INICIO

# Função para converter Timestamp do Zabbix para data legivel // Function to convert timestamp to human date

def timestamp_to_date(tm):
    return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(int(tm)))



def main():
    
    with open(REPORT_NAME, mode='w', newline='') as csv_file:
        trend_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        trend_writer.writerow(['HOST','DATE','METRIC','VALUE AVG'])
        for host in LIST_HOSTS:
            trend = app.trend.get(output=["itemid","clock","value_avg"], itemids=get_metrics(host['hostid']), time_from=date_to_timestamp(INICIO), time_till=date_to_timestamp(FIM))
            for t in tqdm(trend, ascii=True, desc=f"[{Fore.GREEN}{datetime.now()}{Fore.WHITE}] Extract trends from {SERVIDOR}"):
                item_name = app.item.get(output=["itemid","name"],itemids=t['itemid'])
                trend_writer.writerow([host['name'],timestamp_to_date(t['clock']),item_name[0]['name'],t['value_avg']])

    app.user.logout()
    print(f"[{Fore.GREEN}{datetime.now()}{Fore.WHITE}] Close connection!")


if __name__ == '__main__':
    main()
