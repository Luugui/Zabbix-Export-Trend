# Zabbix Trend Exporter - Versão Melhorada

Uma ferramenta moderna e completa para exportação de tendências históricas do Zabbix, com interface web intuitiva e funcionalidades avançadas.

## 🚀 Características Principais

- **Interface Web Moderna**: Interface gráfica intuitiva com design responsivo
- **API REST**: Endpoints para integração com outros sistemas
- **Processamento Assíncrono**: Exportações em background com feedback visual
- **Múltiplas Métricas**: CPU, Memória, Disco, Rede (entrada/saída)
- **Configuração Flexível**: Arquivo JSON ou variáveis de ambiente
- **Logging Avançado**: Sistema completo de logs para auditoria
- **Tratamento Robusto de Erros**: Recuperação graceful de falhas
- **Linha de Comando**: Mantém compatibilidade com automação

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Servidor Zabbix acessível
- Credenciais com permissões de leitura no Zabbix

## 🛠️ Instalação

### Método 1: Interface Web (Recomendado)

```bash
# Clonar o repositório
git clone <repositório>
cd zabbix-web-interface

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor web
python src/main.py
```

Acesse `http://localhost:5000` no navegador.

### Método 2: Linha de Comando

```bash
# Instalar dependências
pip install pyzabbix tqdm colorama

# Usar script melhorado
python zabbix_export_improved.py --help
```

## 🖥️ Interface Web

### Funcionalidades

1. **Configuração do Servidor**
   - URL do Zabbix
   - Credenciais de acesso
   - Teste de conectividade

2. **Seleção de Host**
   - Busca automática de hosts
   - Filtro por nome
   - Seleção por clique

3. **Período de Exportação**
   - Seletores de data
   - Validação de período
   - Valores padrão

4. **Métricas**
   - Seleção individual
   - Ícones visuais
   - Validação de seleção

5. **Progresso**
   - Barra de progresso visual
   - Status em tempo real
   - Opção de cancelamento

6. **Resultados**
   - Download direto
   - Mensagens de erro claras
   - Opção de nova exportação

### Screenshots

![Interface Principal](screenshots/interface-principal.png)
![Progresso](screenshots/progresso.png)
![Resultados](screenshots/resultados.png)

## 💻 Linha de Comando

### Uso Básico

```bash
python zabbix_export_improved.py \
  -u Admin \
  -p zabbix \
  -s http://localhost/zabbix \
  -n "Zabbix Server" \
  -f 01/01/2025 \
  -t 31/01/2025
```

### Configuração via Arquivo

```bash
# Criar arquivo de configuração
python zabbix_export_improved.py --create-config

# Editar zabbix_config.json conforme necessário

# Usar configuração
python zabbix_export_improved.py \
  --config zabbix_config.json \
  -n "Zabbix Server" \
  -f 01/01/2025 \
  -t 31/01/2025
```

### Seleção de Métricas

```bash
# Exportar apenas CPU e memória
python zabbix_export_improved.py \
  --config zabbix_config.json \
  -n "Zabbix Server" \
  -f 01/01/2025 \
  -t 31/01/2025 \
  --metrics cpu memory
```

### Parâmetros Disponíveis

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `-u, --user` | Usuário do Zabbix | `Admin` |
| `-p, --password` | Senha do usuário | `zabbix` |
| `-s, --server` | URL do Zabbix | `http://localhost/zabbix` |
| `-n, --name` | Nome do host | `Zabbix Server` |
| `-f, --from` | Data inicial | `01/01/2025` |
| `-t, --till` | Data final | `31/01/2025` |
| `-o, --output` | Arquivo de saída | `export.csv` |
| `-c, --config` | Arquivo de configuração | `config.json` |
| `-m, --metrics` | Métricas a exportar | `cpu memory disk` |
| `-v, --verbose` | Modo verboso | - |
| `--create-config` | Criar configuração | - |

## 📊 API REST

### Endpoints Disponíveis

#### Testar Conexão
```http
POST /api/zabbix/test-connection
Content-Type: application/json

{
  "url": "http://localhost/zabbix",
  "username": "Admin",
  "password": "zabbix"
}
```

#### Buscar Hosts
```http
POST /api/zabbix/get-hosts
Content-Type: application/json

{
  "url": "http://localhost/zabbix",
  "username": "Admin",
  "password": "zabbix",
  "search": "server"
}
```

#### Iniciar Exportação
```http
POST /api/zabbix/start-export
Content-Type: application/json

{
  "url": "http://localhost/zabbix",
  "username": "Admin",
  "password": "zabbix",
  "hostname": "Zabbix Server",
  "date_from": "01/01/2025",
  "date_till": "31/01/2025",
  "selected_metrics": ["cpu", "memory", "disk"]
}
```

#### Verificar Status
```http
GET /api/zabbix/export-status/{export_id}
```

#### Download
```http
GET /api/zabbix/download/{export_id}
```

## ⚙️ Configuração

### Arquivo de Configuração (zabbix_config.json)

```json
{
    "url": "http://localhost/zabbix",
    "username": "Admin",
    "password": "zabbix",
    "default_metrics": ["cpu", "memory", "disk", "network_in", "network_out"]
}
```

### Variáveis de Ambiente

```bash
export ZABBIX_URL="http://localhost/zabbix"
export ZABBIX_USER="Admin"
export ZABBIX_PASS="zabbix"
```

## 📈 Métricas Suportadas

| Métrica | Descrição | Chave Zabbix |
|---------|-----------|--------------|
| CPU | Utilização de CPU | `system.cpu.util` |
| Memória | Uso de memória (%) | `memory` + `%` + `use` |
| Disco | Espaço livre (%) | `vfs.fs.size` + `%` + `Free` |
| Rede (In) | Tráfego de entrada | `net.if.in` + `bps` |
| Rede (Out) | Tráfego de saída | `net.if.out` + `bps` |

## 📁 Formato de Saída

O arquivo CSV gerado contém as seguintes colunas:

```csv
HOST,DATE,METRIC,VALUE_AVG,VALUE_MIN,VALUE_MAX
Zabbix Server,18/09/2025 10:30:00,CPU utilization,15.5,10.2,25.8
Zabbix Server,18/09/2025 10:30:00,Memory utilization,45.2,40.1,50.3
```

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "src/main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  zabbix-exporter:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ZABBIX_URL=http://zabbix-server/zabbix
      - ZABBIX_USER=Admin
      - ZABBIX_PASS=zabbix
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
zabbix-web-interface/
├── src/
│   ├── main.py                 # Aplicação Flask
│   ├── routes/
│   │   └── zabbix.py          # Rotas da API
│   ├── static/
│   │   ├── index.html         # Interface web
│   │   ├── style.css          # Estilos
│   │   └── script.js          # JavaScript
│   └── zabbix_export_improved.py  # Script melhorado
├── venv/                      # Ambiente virtual
├── requirements.txt           # Dependências
└── README.md                  # Documentação
```

### Executar em Modo Debug

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python src/main.py
```

### Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-cov

# Executar testes
pytest tests/

# Cobertura de código
pytest --cov=src tests/
```

## 🚨 Troubleshooting

### Problemas Comuns

**Erro de Conexão SSL:**
```bash
# Desabilitar verificação SSL (desenvolvimento apenas)
export PYTHONHTTPSVERIFY=0
```

**Timeout de Conexão:**
- Verificar URL do Zabbix
- Confirmar conectividade de rede
- Validar credenciais

**Erro de Permissões:**
- Verificar permissões do usuário no Zabbix
- Confirmar acesso aos hosts desejados

### Logs

Os logs são salvos em:
- Console: Saída padrão
- Arquivo: `zabbix_export.log`

Nível de log configurável via parâmetro `--verbose`.

## 📝 Changelog

### v0.2.0 (Atual)
- ✅ Interface web moderna
- ✅ API REST completa
- ✅ Processamento assíncrono
- ✅ Sistema de logging
- ✅ Configuração flexível
- ✅ Tratamento robusto de erros

### v0.1.1 (Original)
- ✅ Exportação básica via linha de comando
- ✅ Métricas fixas (CPU, Memória, Disco, Rede)
- ✅ Saída em CSV

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença Apache 2.0 - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Luis Amaral** - Versão original
- **Manus AI** - Melhorias e interface web

## 🙏 Agradecimentos

- Comunidade Zabbix
- Desenvolvedores do pyzabbix
- Contribuidores do projeto original

