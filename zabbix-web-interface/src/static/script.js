// Variáveis globais
let currentExportId = null;
let progressInterval = null;

// Elementos DOM
const exportForm = document.getElementById('exportForm');
const testConnectionBtn = document.getElementById('testConnection');
const searchHostsBtn = document.getElementById('searchHosts');
const hostsList = document.getElementById('hostsList');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const progressFill = document.getElementById('progressFill');
const progressMessage = document.getElementById('progressMessage');
const successResult = document.getElementById('successResult');
const errorResult = document.getElementById('errorResult');
const errorMessage = document.getElementById('errorMessage');
const downloadFileBtn = document.getElementById('downloadFile');
const newExportBtn = document.getElementById('newExport');
const retryExportBtn = document.getElementById('retryExport');
const cancelExportBtn = document.getElementById('cancelExport');

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Definir data padrão (último mês)
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
    
    document.getElementById('dateFrom').value = formatDate(lastMonth);
    document.getElementById('dateTill').value = formatDate(today);
    
    // Event listeners
    testConnectionBtn.addEventListener('click', testConnection);
    searchHostsBtn.addEventListener('click', searchHosts);
    exportForm.addEventListener('submit', startExport);
    downloadFileBtn.addEventListener('click', downloadFile);
    newExportBtn.addEventListener('click', resetForm);
    retryExportBtn.addEventListener('click', retryExport);
    cancelExportBtn.addEventListener('click', cancelExport);
});

// Funções utilitárias
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.getElementById('notifications').appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function getFormData() {
    return {
        url: document.getElementById('url').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        hostname: document.getElementById('hostname').value,
        date_from: document.getElementById('dateFrom').value,
        date_till: document.getElementById('dateTill').value,
        selected_metrics: Array.from(document.querySelectorAll('input[name="metrics"]:checked')).map(cb => cb.value)
    };
}

function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        const icon = button.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-spinner fa-spin';
        }
    } else {
        button.disabled = false;
        const icon = button.querySelector('i');
        if (icon) {
            // Restaurar ícone original baseado no ID do botão
            const iconMap = {
                'testConnection': 'fas fa-plug',
                'searchHosts': 'fas fa-search',
                'startExport': 'fas fa-download'
            };
            icon.className = iconMap[button.id] || 'fas fa-cog';
        }
    }
}

// Função para testar conexão
async function testConnection() {
    const formData = getFormData();
    
    if (!formData.url || !formData.username || !formData.password) {
        showNotification('Preencha URL, usuário e senha para testar a conexão', 'warning');
        return;
    }
    
    setButtonLoading(testConnectionBtn, true);
    
    try {
        const response = await fetch('/api/zabbix/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: formData.url,
                username: formData.username,
                password: formData.password
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Conexão estabelecida com sucesso!', 'success');
        } else {
            showNotification(`Erro na conexão: ${result.message}`, 'error');
        }
        
    } catch (error) {
        showNotification(`Erro ao testar conexão: ${error.message}`, 'error');
    } finally {
        setButtonLoading(testConnectionBtn, false);
    }
}

// Função para buscar hosts
async function searchHosts() {
    const formData = getFormData();
    
    if (!formData.url || !formData.username || !formData.password) {
        showNotification('Preencha as credenciais antes de buscar hosts', 'warning');
        return;
    }
    
    setButtonLoading(searchHostsBtn, true);
    
    try {
        const response = await fetch('/api/zabbix/get-hosts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: formData.url,
                username: formData.username,
                password: formData.password,
                search: formData.hostname
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayHosts(result.hosts);
            showNotification(`${result.hosts.length} hosts encontrados`, 'success');
        } else {
            showNotification(`Erro ao buscar hosts: ${result.message}`, 'error');
        }
        
    } catch (error) {
        showNotification(`Erro ao buscar hosts: ${error.message}`, 'error');
    } finally {
        setButtonLoading(searchHostsBtn, false);
    }
}

// Função para exibir lista de hosts
function displayHosts(hosts) {
    hostsList.innerHTML = '';
    
    if (hosts.length === 0) {
        hostsList.innerHTML = '<div class="host-item">Nenhum host encontrado</div>';
    } else {
        hosts.forEach(host => {
            const hostItem = document.createElement('div');
            hostItem.className = 'host-item';
            hostItem.innerHTML = `
                <div class="host-name">${host.name}</div>
                <div class="host-host">${host.host}</div>
            `;
            
            hostItem.addEventListener('click', () => {
                document.getElementById('hostname').value = host.host;
                hostsList.style.display = 'none';
            });
            
            hostsList.appendChild(hostItem);
        });
    }
    
    hostsList.style.display = 'block';
}

// Função para iniciar exportação
async function startExport(event) {
    event.preventDefault();
    
    const formData = getFormData();
    
    // Validações
    if (!formData.url || !formData.username || !formData.password || !formData.hostname || !formData.date_from || !formData.date_till) {
        showNotification('Preencha todos os campos obrigatórios', 'warning');
        return;
    }
    
    if (formData.selected_metrics.length === 0) {
        showNotification('Selecione pelo menos uma métrica para exportar', 'warning');
        return;
    }
    
    // Converter datas para formato DD/MM/YYYY
    const dateFrom = new Date(formData.date_from).toLocaleDateString('pt-BR');
    const dateTill = new Date(formData.date_till).toLocaleDateString('pt-BR');
    
    setButtonLoading(document.getElementById('startExport'), true);
    
    try {
        const response = await fetch('/api/zabbix/start-export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ...formData,
                date_from: dateFrom,
                date_till: dateTill
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentExportId = result.export_id;
            showProgressSection();
            startProgressMonitoring();
            showNotification('Exportação iniciada!', 'success');
        } else {
            showNotification(`Erro ao iniciar exportação: ${result.message}`, 'error');
        }
        
    } catch (error) {
        showNotification(`Erro ao iniciar exportação: ${error.message}`, 'error');
    } finally {
        setButtonLoading(document.getElementById('startExport'), false);
    }
}

// Função para mostrar seção de progresso
function showProgressSection() {
    exportForm.style.display = 'none';
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
}

// Função para monitorar progresso
function startProgressMonitoring() {
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/zabbix/export-status/${currentExportId}`);
            const result = await response.json();
            
            if (result.success) {
                const status = result.status;
                
                progressFill.style.width = `${status.progress}%`;
                progressMessage.textContent = status.message;
                
                if (status.status === 'completed') {
                    clearInterval(progressInterval);
                    showSuccessResult();
                } else if (status.status === 'error') {
                    clearInterval(progressInterval);
                    showErrorResult(status.message);
                }
            }
            
        } catch (error) {
            console.error('Erro ao verificar status:', error);
        }
    }, 2000);
}

// Função para mostrar resultado de sucesso
function showSuccessResult() {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    successResult.style.display = 'block';
    errorResult.style.display = 'none';
}

// Função para mostrar resultado de erro
function showErrorResult(message) {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    successResult.style.display = 'none';
    errorResult.style.display = 'block';
    errorMessage.textContent = message;
}

// Função para fazer download do arquivo
async function downloadFile() {
    if (!currentExportId) return;
    
    try {
        const response = await fetch(`/api/zabbix/download/${currentExportId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `zabbix-export-${currentExportId}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('Download iniciado!', 'success');
        } else {
            showNotification('Erro ao fazer download do arquivo', 'error');
        }
        
    } catch (error) {
        showNotification(`Erro no download: ${error.message}`, 'error');
    }
}

// Função para resetar formulário
function resetForm() {
    exportForm.style.display = 'block';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    if (currentExportId) {
        // Limpar arquivos temporários
        fetch(`/api/zabbix/cleanup/${currentExportId}`, { method: 'DELETE' });
        currentExportId = null;
    }
    
    progressFill.style.width = '0%';
    progressMessage.textContent = 'Iniciando...';
}

// Função para tentar novamente
function retryExport() {
    resetForm();
}

// Função para cancelar exportação
function cancelExport() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    showNotification('Exportação cancelada', 'warning');
    resetForm();
}

// Fechar lista de hosts ao clicar fora
document.addEventListener('click', function(event) {
    if (!event.target.closest('#hostsList') && !event.target.closest('#searchHosts')) {
        hostsList.style.display = 'none';
    }
});

