# ZABBIX EXPORT TREND

![](https://img.shields.io/badge/Zabbix-5.0-green) ![](https://img.shields.io/badge/Python-3.9-blue)

---
### Descrição

Script criado para extração de trends historicos de um host selecionado. Neste relatório será gerado um csv com os itens de CPU, Memória, Disco e In/Out das Interfaces de Rede.

---

###  Dependências

- pyzabbix
- tqdm
- argparse

`pip install pyzabbix tqdm argparse`

or

`pip install -r requirements.txt`

---
### Exemplo


`python zabbix-export-trends.py -u Admin -p zabbix -s http://localhost/zabbix -n 'Zabbix Server' -f 01/01/2021 -t 02/01/2021`

- "-u" - Login Zabbix
- "-p" - Senha do Login
- "-s" - URL do Console Zabbix
- "-n" - Nome do Host
- "-f" - Data inicio do relatório
- "-t" - Data final do relatório