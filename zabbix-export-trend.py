#!/usr/bin/env python
# -*- coding: utf-8 -*-
#filename            : zabbix-export-trends.py
#description         : Script for extracting historical trends of selected Host's CPU, Memory, Disk and Network In/Out items 
#author              : Luis Amaral
#email               : luisguilhermester at live dot com
#date                : 2021/10/13
#version             : 0.1.0
#usage               : $ python zabbix-export-trends.py -u Admin -p zabbix -s http://localhost/zabbix -h 'Zabbix Server' -f 01/01/2021 -f 02/01/2021
#notes               : All parameters are required
#license             : Apache-2.0
#python_version      : 3.9.2
#==============================================================================

from pyzabbix import ZabbixAPI
from tqdm import tqdm
from datetime import datetime
import time, csv, sys, argparse

# INITIALIZE ARGUMENTS

parser = argparse.ArgumentParser(description="Extract trend from select host")
parser.add_argument("-u", "--user", required=True, help="Zabbix user")
parser.add_argument("-p", "--password", required=True, help="Zabbix user password")
parser.add_argument("-s", "--server", required=True, help="Zabbix frontend URL")
parser.add_argument("-n", "--name", required=True, help="Name of host")
parser.add_argument("-f", "--from", required=True, help="Time from")
parser.add_argument("-t", "--till", required=True, help="Time till")
args = vars(parser.parse_args())

# VARIAVEIS DE CONFIGURAÇÃO DO RELATÓRIO
URL=args['server']
LOGIN=args['user']
SENHA=args['password']
SERVIDOR=args['name']
INICIO=f"{args['from']}"
FIM=f"{args['till']} 23:59:59"




# CONECTANDO AO ZABBIX
app = ZabbixAPI(URL)
if "https" in URL:
    import requests
    requests.packages.urllib3.disable_warnings()
    app.session.verify = False
app.login(LOGIN,SENHA)
print(f"[{datetime.now()}] Connected to Zabbix!\n")

LIST_HOSTS = app.host.get(output=["hostid","name"],filter={"host": SERVIDOR},limit=1)

# Função para coleta dos ids dos items de CPU, Memória e Disco

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

# Função para converter data em Timestamp aceito pelo Zabbix

def date_to_timestamp(data):
    try:
        data == datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m/%Y")
        DATA_INICIO = time.mktime(time.strptime("{} 00:00:00".format(data), "%d/%m/%Y %H:%M:%S"))

        return DATA_INICIO
    except:
        data == datetime.strptime(data, "%d/%m/%Y %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        DATA_INICIO = time.mktime(time.strptime(data, "%d/%m/%Y %H:%M:%S"))

        return DATA_INICIO

# Função para converter Timestamp do Zabbix para data legivel

def timestamp_to_date(tm):
    return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(int(tm)))



def main():
    with open(f'ZABBIX-{SERVIDOR}-TREND-EXPORT_{sys.argv[4]}.csv', mode='w', newline='') as csv_file:
        trend_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        trend_writer.writerow(['HOST','DATA','METRICA','VALUE AVG'])
        for host in LIST_HOSTS:
            trend = app.trend.get(output=["itemid","clock","value_avg"], itemids=get_metrics(host['hostid']), time_from=date_to_timestamp(INICIO), time_till=date_to_timestamp(FIM))
            for t in tqdm(trend, ascii=True, desc=f"[{datetime.now()}] Extract trends from {SERVIDOR}"):
                item_name = app.item.get(output=["itemid","name"],itemids=t['itemid'])
                trend_writer.writerow([host['name'],timestamp_to_date(t['clock']),item_name[0]['name'],t['value_avg']])

    app.user.logout()
    print(f"[{datetime.now()}] Close connection!")


if __name__ == '__main__':
    main()
