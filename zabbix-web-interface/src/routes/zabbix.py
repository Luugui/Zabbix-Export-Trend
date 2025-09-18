from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
import threading
import time
from datetime import datetime
import logging

# Importar a classe do script melhorado
from src.zabbix_export_improved import ZabbixTrendExporter

zabbix_bp = Blueprint('zabbix', __name__)

# Dicionário para armazenar status das exportações
export_status = {}

@zabbix_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Testa a conexão com o Zabbix"""
    try:
        data = request.get_json()
        
        url = data.get('url')
        username = data.get('username')
        password = data.get('password')
        
        if not all([url, username, password]):
            return jsonify({'success': False, 'message': 'Parâmetros obrigatórios: url, username, password'}), 400
        
        exporter = ZabbixTrendExporter(url, username, password)
        
        if exporter.connect():
            exporter.disconnect()
            return jsonify({'success': True, 'message': 'Conexão estabelecida com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Falha ao conectar com o Zabbix'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@zabbix_bp.route('/get-hosts', methods=['POST'])
def get_hosts():
    """Busca hosts disponíveis no Zabbix"""
    try:
        data = request.get_json()
        
        url = data.get('url')
        username = data.get('username')
        password = data.get('password')
        search_term = data.get('search', '')
        
        if not all([url, username, password]):
            return jsonify({'success': False, 'message': 'Parâmetros obrigatórios: url, username, password'}), 400
        
        exporter = ZabbixTrendExporter(url, username, password)
        
        if exporter.connect():
            try:
                # Buscar hosts
                search_filter = {}
                if search_term:
                    search_filter = {"host": search_term}
                
                hosts = exporter.api.host.get(
                    output=["hostid", "name", "host"],
                    filter=search_filter,
                    limit=50
                )
                
                exporter.disconnect()
                
                return jsonify({
                    'success': True, 
                    'hosts': [{'id': h['hostid'], 'name': h['name'], 'host': h['host']} for h in hosts]
                })
                
            except Exception as e:
                exporter.disconnect()
                return jsonify({'success': False, 'message': f'Erro ao buscar hosts: {str(e)}'}), 500
        else:
            return jsonify({'success': False, 'message': 'Falha ao conectar com o Zabbix'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

def export_trends_async(export_id, url, username, password, hostname, date_from, date_till, selected_metrics):
    """Função para executar exportação em background"""
    try:
        export_status[export_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Iniciando exportação...',
            'file_path': None
        }
        
        exporter = ZabbixTrendExporter(url, username, password)
        
        if exporter.connect():
            export_status[export_id]['message'] = 'Conectado ao Zabbix'
            export_status[export_id]['progress'] = 10
            
            # Criar arquivo temporário
            temp_dir = tempfile.gettempdir()
            output_file = os.path.join(temp_dir, f'zabbix-export-{export_id}.csv')
            
            export_status[export_id]['message'] = 'Exportando dados...'
            export_status[export_id]['progress'] = 30
            
            success = exporter.export_trends(
                hostname=hostname,
                date_from=date_from,
                date_till=date_till,
                output_file=output_file,
                selected_metrics=selected_metrics
            )
            
            exporter.disconnect()
            
            if success:
                export_status[export_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Exportação concluída com sucesso!',
                    'file_path': output_file
                }
            else:
                export_status[export_id] = {
                    'status': 'error',
                    'progress': 0,
                    'message': 'Falha na exportação',
                    'file_path': None
                }
        else:
            export_status[export_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Falha ao conectar com o Zabbix',
                'file_path': None
            }
            
    except Exception as e:
        export_status[export_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Erro durante exportação: {str(e)}',
            'file_path': None
        }

@zabbix_bp.route('/start-export', methods=['POST'])
def start_export():
    """Inicia uma exportação em background"""
    try:
        data = request.get_json()
        
        url = data.get('url')
        username = data.get('username')
        password = data.get('password')
        hostname = data.get('hostname')
        date_from = data.get('date_from')
        date_till = data.get('date_till')
        selected_metrics = data.get('selected_metrics', ['cpu', 'memory', 'disk', 'network_in', 'network_out'])
        
        if not all([url, username, password, hostname, date_from, date_till]):
            return jsonify({'success': False, 'message': 'Parâmetros obrigatórios faltando'}), 400
        
        # Gerar ID único para a exportação
        export_id = f"{int(time.time())}_{hash(hostname)}"
        
        # Iniciar thread para exportação
        thread = threading.Thread(
            target=export_trends_async,
            args=(export_id, url, username, password, hostname, date_from, date_till, selected_metrics)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'export_id': export_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@zabbix_bp.route('/export-status/<export_id>', methods=['GET'])
def get_export_status(export_id):
    """Retorna o status de uma exportação"""
    if export_id in export_status:
        return jsonify({'success': True, 'status': export_status[export_id]})
    else:
        return jsonify({'success': False, 'message': 'Exportação não encontrada'}), 404

@zabbix_bp.route('/download/<export_id>', methods=['GET'])
def download_export(export_id):
    """Faz download do arquivo exportado"""
    if export_id in export_status and export_status[export_id]['file_path']:
        file_path = export_status[export_id]['file_path']
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'zabbix-export-{export_id}.csv',
                mimetype='text/csv'
            )
        else:
            return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404
    else:
        return jsonify({'success': False, 'message': 'Exportação não encontrada'}), 404

@zabbix_bp.route('/cleanup/<export_id>', methods=['DELETE'])
def cleanup_export(export_id):
    """Remove arquivos temporários da exportação"""
    if export_id in export_status:
        if export_status[export_id]['file_path'] and os.path.exists(export_status[export_id]['file_path']):
            try:
                os.remove(export_status[export_id]['file_path'])
            except:
                pass
        
        del export_status[export_id]
        return jsonify({'success': True, 'message': 'Limpeza concluída'})
    else:
        return jsonify({'success': False, 'message': 'Exportação não encontrada'}), 404

