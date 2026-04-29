/* ─── CONFIG ──────────────────────────────────────────────────── */
const API = 'http://localhost:5000/api';

/* ─── CHARTS INSTANCES ────────────────────────────────────────── */
let chartFaturamento = null;
let chartStatus      = null;

/* ─── UTILS ───────────────────────────────────────────────────── */

function fmt(val) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0);
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function toast(msg, type = 'info') {
  const icons = { ok: '✓', err: '✕', info: 'ℹ' };
  const div = document.createElement('div');
  div.className = `toast toast-${type}`;
  div.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
  document.getElementById('toastContainer').appendChild(div);
  setTimeout(() => div.remove(), 3800);
}

async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  return res.json();
}

function setStatusIndicator(ok) {
  const dot  = document.querySelector('.dot');
  const text = document.getElementById('statusText');
  dot.className  = `dot ${ok ? 'dot-ok' : 'dot-err'}`;
  text.textContent = ok ? 'API Conectada' : 'API Offline';
}

/* ─── NAVIGATION ──────────────────────────────────────────────── */

function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
  document.getElementById(`nav-${page}`).classList.add('active');

  const titles = {
    dashboard: 'Dashboard',
    clientes: 'Clientes',
    veiculos: 'Veículos',
    os: 'Ordens de Serviço'
  };
  document.getElementById('topbarTitle').textContent = titles[page] || page;

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }

  switch (page) {
    case 'dashboard': loadDashboard(); break;
    case 'clientes':  loadClientes();  break;
    case 'veiculos':  loadVeiculos();  break;
    case 'os':        loadOS();        break;
  }
}

/* ─── MODAL ───────────────────────────────────────────────────── */

function openModal(title, bodyHTML, footerHTML) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = bodyHTML;
  document.getElementById('modalFooter').innerHTML = footerHTML || '';
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

function openOsDetail(os_id) {
  document.getElementById('osDetailOverlay').classList.add('open');
  document.getElementById('osDetailTitle').textContent = `OS #${os_id}`;
  document.getElementById('osDetailBody').innerHTML = '<div class="loading-row">Carregando...</div>';
  loadOsDetail(os_id);
}

function closeOsDetail() {
  document.getElementById('osDetailOverlay').classList.remove('open');
}

/* ─── DASHBOARD ───────────────────────────────────────────────── */

async function loadDashboard() {
  try {
    const [kpi, mensal, clientes, servicos] = await Promise.all([
      api('/dashboard'),
      api('/dashboard/faturamento-mensal'),
      api('/dashboard/top-clientes'),
      api('/dashboard/servicos')
    ]);

    if (!kpi.success) { toast('Erro ao carregar dashboard', 'err'); return; }

    const d = kpi.data;
    document.getElementById('kpiFaturamento').textContent = fmt(d.faturamento_total);
    document.getElementById('kpiClientes').textContent    = d.clientes_total;
    document.getElementById('kpiVeiculos').textContent    = d.veiculos_total;
    document.getElementById('kpiOsAbertas').textContent   = d.os_abertas;
    document.getElementById('kpiOsAndamento').textContent = d.os_andamento;
    document.getElementById('kpiOsFinalizadas').textContent = d.os_finalizadas;

    renderChartFaturamento(mensal.data || []);
    renderChartStatus(d);
    renderTopClientes(clientes.data || []);
    renderTopServicos(servicos.data || []);

    setStatusIndicator(true);
  } catch (e) {
    setStatusIndicator(false);
    toast('Não foi possível conectar à API', 'err');
  }
}

function renderChartFaturamento(data) {
  const ctx = document.getElementById('chartFaturamento').getContext('2d');
  const labels = data.map(r => r.mes);
  const values = data.map(r => parseFloat(r.total));

  if (chartFaturamento) chartFaturamento.destroy();

  chartFaturamento = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Sem dados'],
      datasets: [{
        label: 'Faturamento (R$)',
        data: values.length ? values : [0],
        backgroundColor: 'rgba(79,142,247,.65)',
        borderColor: '#4f8ef7',
        borderWidth: 1.5,
        borderRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#23273a' }, ticks: { color: '#6b7399' } },
        y: {
          grid: { color: '#23273a' }, ticks: { color: '#6b7399',
          callback: v => 'R$ ' + v.toLocaleString('pt-BR') }
        }
      }
    }
  });
}

function renderChartStatus(d) {
  const ctx = document.getElementById('chartStatus').getContext('2d');
  if (chartStatus) chartStatus.destroy();

  chartStatus = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Abertas', 'Em Andamento', 'Finalizadas', 'Canceladas'],
      datasets: [{
        data: [d.os_abertas, d.os_andamento, d.os_finalizadas, d.os_canceladas],
        backgroundColor: ['#4f8ef7', '#f7b84f', '#36c98e', '#f74f4f'],
        borderWidth: 0,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#6b7399', boxWidth: 10, padding: 14, font: { size: 11 } }
        }
      }
    }
  });
}

function renderTopClientes(data) {
  const el = document.getElementById('topClientes');
  if (!data.length) { el.innerHTML = '<div class="loading-row">Nenhum dado</div>'; return; }
  el.innerHTML = data.map((r, i) => `
    <div class="table-mini-row">
      <span class="table-mini-label">${i + 1}. ${r.nome}</span>
      <span class="table-mini-value">${fmt(r.total)}</span>
    </div>
  `).join('');
}

function renderTopServicos(data) {
  const el = document.getElementById('topServicos');
  if (!data.length) { el.innerHTML = '<div class="loading-row">Nenhum dado</div>'; return; }
  el.innerHTML = data.map(r => `
    <div class="table-mini-row">
      <span class="table-mini-label">${r.descricao}</span>
      <span class="table-mini-badge">${r.quantidade}×</span>
    </div>
  `).join('');
}

/* ─── CLIENTES ────────────────────────────────────────────────── */

async function loadClientes(q = '') {
  const tbody = document.getElementById('tbodyClientes');
  tbody.innerHTML = '<tr><td colspan="6" class="loading-row">Carregando...</td></tr>';
  const path = q ? `/clientes?q=${encodeURIComponent(q)}` : '/clientes';
  const res  = await api(path);
  if (!res.success) { toast('Erro ao carregar clientes', 'err'); return; }

  const rows = res.data;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-row">Nenhum cliente encontrado.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${c.nome}</td>
      <td>${c.telefone}</td>
      <td>${c.cpf || '—'}</td>
      <td>${fmtDate(c.criado_em)}</td>
      <td>
        <div class="actions">
          <button class="btn btn-ghost btn-sm" onclick="editCliente(${c.id}, '${esc(c.nome)}', '${esc(c.telefone)}', '${esc(c.cpf || '')}')">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteCliente(${c.id}, '${esc(c.nome)}')">Excluir</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function esc(s) { return String(s).replace(/'/g, "\\'"); }

function modalNovoCliente() {
  openModal('Novo Cliente', `
    <div class="form-group">
      <label>Nome *</label>
      <input type="text" id="fNome" placeholder="Nome completo" />
    </div>
    <div class="form-group">
      <label>Telefone *</label>
      <input type="text" id="fTelefone" placeholder="(11) 99999-9999" />
    </div>
    <div class="form-group">
      <label>CPF</label>
      <input type="text" id="fCpf" placeholder="000.000.000-00 (opcional)" />
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitNovoCliente()">Cadastrar</button>
  `);
}

async function submitNovoCliente() {
  const nome     = document.getElementById('fNome').value.trim();
  const telefone = document.getElementById('fTelefone').value.trim();
  const cpf      = document.getElementById('fCpf').value.trim();
  if (!nome || !telefone) { toast('Nome e telefone são obrigatórios', 'err'); return; }

  const res = await api('/clientes', 'POST', { nome, telefone, cpf: cpf || null });
  if (res.success) {
    toast('Cliente cadastrado!', 'ok');
    closeModal();
    loadClientes();
  } else {
    toast(res.message || 'Erro ao cadastrar', 'err');
  }
}

function editCliente(id, nome, telefone, cpf) {
  openModal('Editar Cliente', `
    <div class="form-group">
      <label>Nome *</label>
      <input type="text" id="fNome" value="${nome}" />
    </div>
    <div class="form-group">
      <label>Telefone *</label>
      <input type="text" id="fTelefone" value="${telefone}" />
    </div>
    <div class="form-group">
      <label>CPF</label>
      <input type="text" id="fCpf" value="${cpf}" />
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitEditCliente(${id})">Salvar</button>
  `);
}

async function submitEditCliente(id) {
  const nome     = document.getElementById('fNome').value.trim();
  const telefone = document.getElementById('fTelefone').value.trim();
  const cpf      = document.getElementById('fCpf').value.trim();
  if (!nome || !telefone) { toast('Nome e telefone são obrigatórios', 'err'); return; }

  const res = await api(`/clientes/${id}`, 'PUT', { nome, telefone, cpf: cpf || null });
  if (res.success) {
    toast('Cliente atualizado!', 'ok');
    closeModal();
    loadClientes();
  } else {
    toast(res.message || 'Erro ao atualizar', 'err');
  }
}

function deleteCliente(id, nome) {
  openModal(`Excluir Cliente`, `
    <p>Tem certeza que deseja excluir <strong>${nome}</strong>?</p>
    <p style="margin-top:8px;color:var(--danger);font-size:.85rem;">⚠ Todos os veículos e OS deste cliente serão removidos.</p>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-danger" onclick="confirmDeleteCliente(${id})">Excluir</button>
  `);
}

async function confirmDeleteCliente(id) {
  const res = await api(`/clientes/${id}`, 'DELETE');
  if (res.success) {
    toast('Cliente removido', 'ok');
    closeModal();
    loadClientes();
  } else {
    toast(res.message || 'Erro ao excluir', 'err');
  }
}

/* ─── VEÍCULOS ────────────────────────────────────────────────── */

async function loadVeiculos(q = '') {
  const tbody = document.getElementById('tbodyVeiculos');
  tbody.innerHTML = '<tr><td colspan="7" class="loading-row">Carregando...</td></tr>';
  const path = q ? `/veiculos?q=${encodeURIComponent(q)}` : '/veiculos';
  const res  = await api(path);
  if (!res.success) { toast('Erro ao carregar veículos', 'err'); return; }

  const rows = res.data;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-row">Nenhum veículo encontrado.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(v => `
    <tr>
      <td>${v.id}</td>
      <td><strong>${v.placa}</strong></td>
      <td>${v.marca || '—'}</td>
      <td>${v.modelo || '—'}</td>
      <td>${v.ano || '—'}</td>
      <td>${v.cliente || '—'}</td>
      <td>
        <div class="actions">
          <button class="btn btn-ghost btn-sm" onclick="editVeiculo(${v.id}, '${esc(v.placa)}', '${esc(v.marca || '')}', '${esc(v.modelo || '')}', '${v.ano || ''}')">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteVeiculo(${v.id}, '${esc(v.placa)}')">Excluir</button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function modalNovoVeiculo() {
  // Carrega lista de clientes para o select
  const res = await api('/clientes');
  const options = (res.data || []).map(c => `<option value="${c.id}">${c.nome} — ${c.telefone}</option>`).join('');

  openModal('Novo Veículo', `
    <div class="form-group">
      <label>Cliente *</label>
      <select id="fClienteId">
        <option value="">Selecione um cliente</option>
        ${options}
      </select>
    </div>
    <div class="form-group">
      <label>Placa *</label>
      <input type="text" id="fPlaca" placeholder="ABC1D23" maxlength="10" style="text-transform:uppercase" />
    </div>
    <div class="form-group">
      <label>Marca</label>
      <input type="text" id="fMarca" placeholder="Toyota, Honda, VW..." />
    </div>
    <div class="form-group">
      <label>Modelo</label>
      <input type="text" id="fModelo" placeholder="Corolla, Civic, Gol..." />
    </div>
    <div class="form-group">
      <label>Ano</label>
      <input type="number" id="fAno" placeholder="2024" min="1900" max="2030" />
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitNovoVeiculo()">Cadastrar</button>
  `);
}

async function submitNovoVeiculo() {
  const cliente_id = document.getElementById('fClienteId').value;
  const placa      = document.getElementById('fPlaca').value.trim().toUpperCase();
  const marca      = document.getElementById('fMarca').value.trim();
  const modelo     = document.getElementById('fModelo').value.trim();
  const ano        = parseInt(document.getElementById('fAno').value) || null;

  if (!cliente_id) { toast('Selecione um cliente', 'err'); return; }
  if (!placa)      { toast('Placa é obrigatória', 'err'); return; }

  const res = await api('/veiculos', 'POST', { cliente_id: parseInt(cliente_id), placa, marca, modelo, ano });
  if (res.success) {
    toast('Veículo cadastrado!', 'ok');
    closeModal();
    loadVeiculos();
  } else {
    toast(res.message || 'Erro ao cadastrar', 'err');
  }
}

function editVeiculo(id, placa, marca, modelo, ano) {
  openModal('Editar Veículo', `
    <div class="form-group">
      <label>Placa *</label>
      <input type="text" id="fPlaca" value="${placa}" style="text-transform:uppercase" />
    </div>
    <div class="form-group">
      <label>Marca</label>
      <input type="text" id="fMarca" value="${marca}" />
    </div>
    <div class="form-group">
      <label>Modelo</label>
      <input type="text" id="fModelo" value="${modelo}" />
    </div>
    <div class="form-group">
      <label>Ano</label>
      <input type="number" id="fAno" value="${ano}" />
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitEditVeiculo(${id})">Salvar</button>
  `);
}

async function submitEditVeiculo(id) {
  const placa  = document.getElementById('fPlaca').value.trim().toUpperCase();
  const marca  = document.getElementById('fMarca').value.trim();
  const modelo = document.getElementById('fModelo').value.trim();
  const ano    = parseInt(document.getElementById('fAno').value) || null;
  if (!placa) { toast('Placa é obrigatória', 'err'); return; }

  const res = await api(`/veiculos/${id}`, 'PUT', { placa, marca, modelo, ano });
  if (res.success) {
    toast('Veículo atualizado!', 'ok');
    closeModal();
    loadVeiculos();
  } else {
    toast(res.message || 'Erro ao atualizar', 'err');
  }
}

function deleteVeiculo(id, placa) {
  openModal('Excluir Veículo', `
    <p>Excluir o veículo de placa <strong>${placa}</strong>?</p>
    <p style="color:var(--danger);font-size:.85rem;margin-top:8px;">⚠ As ordens de serviço vinculadas também serão removidas.</p>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-danger" onclick="confirmDeleteVeiculo(${id})">Excluir</button>
  `);
}

async function confirmDeleteVeiculo(id) {
  const res = await api(`/veiculos/${id}`, 'DELETE');
  if (res.success) {
    toast('Veículo removido', 'ok');
    closeModal();
    loadVeiculos();
  } else {
    toast(res.message || 'Erro ao excluir', 'err');
  }
}

/* ─── ORDENS DE SERVIÇO ───────────────────────────────────────── */

let currentStatusFilter = '';

async function loadOS(status = currentStatusFilter) {
  currentStatusFilter = status;
  const tbody = document.getElementById('tbodyOS');
  tbody.innerHTML = '<tr><td colspan="7" class="loading-row">Carregando...</td></tr>';
  const path = status ? `/os?status=${status}` : '/os';
  const res  = await api(path);
  if (!res.success) { toast('Erro ao carregar OS', 'err'); return; }

  const rows = res.data;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-row">Nenhuma OS encontrada.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(o => `
    <tr>
      <td><strong>#${o.id}</strong></td>
      <td>${o.cliente}</td>
      <td>${o.placa} ${o.modelo ? `<span style="color:var(--text-muted);font-size:.8rem">(${o.modelo})</span>` : ''}</td>
      <td>${badgeStatus(o.status)}</td>
      <td>${fmt(o.total)}</td>
      <td>${fmtDate(o.data_abertura)}</td>
      <td>
        <div class="actions">
          <button class="btn btn-ghost btn-sm" onclick="openOsDetail(${o.id})">Ver</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function badgeStatus(status) {
  const map = {
    aberta:       ['badge-aberta',    'Aberta'],
    em_andamento: ['badge-andamento', 'Em Andamento'],
    finalizada:   ['badge-finalizada','Finalizada'],
    cancelada:    ['badge-cancelada', 'Cancelada'],
  };
  const [cls, label] = map[status] || ['', status];
  return `<span class="badge ${cls}">${label}</span>`;
}

async function modalNovaOS() {
  const [cRes] = await Promise.all([api('/clientes')]);
  const clienteOptions = (cRes.data || []).map(c => `<option value="${c.id}">${c.nome} — ${c.telefone}</option>`).join('');

  openModal('Nova Ordem de Serviço', `
    <div class="form-group">
      <label>Cliente *</label>
      <select id="fOsCliente" onchange="loadVeiculosCliente()">
        <option value="">Selecione um cliente</option>
        ${clienteOptions}
      </select>
    </div>
    <div class="form-group">
      <label>Veículo *</label>
      <select id="fOsVeiculo">
        <option value="">Selecione o cliente primeiro</option>
      </select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitNovaOS()">Abrir OS</button>
  `);
}

async function loadVeiculosCliente() {
  const clienteId = document.getElementById('fOsCliente').value;
  const sel = document.getElementById('fOsVeiculo');
  if (!clienteId) { sel.innerHTML = '<option value="">Selecione o cliente primeiro</option>'; return; }

  const res = await api(`/veiculos?cliente_id=${clienteId}`);
  const veiculos = res.data || [];
  if (!veiculos.length) {
    sel.innerHTML = '<option value="">Nenhum veículo cadastrado</option>';
    return;
  }
  sel.innerHTML = veiculos.map(v => `<option value="${v.id}">${v.placa} — ${v.modelo || v.marca || ''}</option>`).join('');
}

async function submitNovaOS() {
  const cliente_id = document.getElementById('fOsCliente').value;
  const veiculo_id = document.getElementById('fOsVeiculo').value;
  if (!cliente_id || !veiculo_id) { toast('Selecione cliente e veículo', 'err'); return; }

  const res = await api('/os', 'POST', { cliente_id: parseInt(cliente_id), veiculo_id: parseInt(veiculo_id) });
  if (res.success) {
    toast(`OS #${res.data.id} aberta!`, 'ok');
    closeModal();
    loadOS();
    openOsDetail(res.data.id);
  } else {
    toast(res.message || 'Erro ao abrir OS', 'err');
  }
}

async function loadOsDetail(os_id) {
  const res = await api(`/os/${os_id}`);
  if (!res.success) { document.getElementById('osDetailBody').innerHTML = '<p style="color:var(--danger)">Erro ao carregar OS.</p>'; return; }

  const os = res.data;
  const itens = os.itens || [];

  const itensHtml = itens.length ? itens.map(i => `
    <tr>
      <td>${i.tipo === 'servico' ? '🔧' : '🔩'} ${i.descricao}</td>
      <td>${i.quantidade}</td>
      <td>${fmt(i.valor_unitario)}</td>
      <td>${fmt(i.subtotal)}</td>
      <td><button class="btn btn-danger btn-sm" onclick="removeItem(${i.id}, ${os_id})">✕</button></td>
    </tr>
  `).join('') : `<tr><td colspan="5" class="loading-row">Nenhum item adicionado.</td></tr>`;

  const canAddItem = ['aberta', 'em_andamento'].includes(os.status);
  const statusAtual = os.status;

  // Botões de ação de status
  let statusActions = '';
  if (statusAtual === 'aberta') {
    statusActions = `
      <button class="btn btn-ghost btn-sm" onclick="mudarStatus(${os_id},'em_andamento')">▶ Iniciar</button>
      <button class="btn btn-danger btn-sm" onclick="mudarStatus(${os_id},'cancelada')">✕ Cancelar</button>
    `;
  } else if (statusAtual === 'em_andamento') {
    statusActions = `
      <button class="btn btn-success btn-sm" onclick="mudarStatus(${os_id},'finalizada')">✓ Finalizar</button>
      <button class="btn btn-danger btn-sm" onclick="mudarStatus(${os_id},'cancelada')">✕ Cancelar</button>
    `;
  }

  document.getElementById('osDetailBody').innerHTML = `
    <div class="os-detail-grid">
      <div class="os-detail-field">
        <span class="label">Cliente</span>
        <span class="val">${os.cliente}</span>
      </div>
      <div class="os-detail-field">
        <span class="label">Telefone</span>
        <span class="val">${os.telefone}</span>
      </div>
      <div class="os-detail-field">
        <span class="label">Veículo</span>
        <span class="val">${os.placa} ${os.modelo ? `— ${os.modelo}` : ''}</span>
      </div>
      <div class="os-detail-field">
        <span class="label">Status</span>
        <span class="val">${badgeStatus(os.status)}</span>
      </div>
      <div class="os-detail-field">
        <span class="label">Abertura</span>
        <span class="val">${fmtDate(os.data_abertura)}</span>
      </div>
      <div class="os-detail-field">
        <span class="label">Fechamento</span>
        <span class="val">${fmtDate(os.data_fechamento)}</span>
      </div>
    </div>

    <div class="os-items-header">
      <h3>Itens da OS</h3>
      ${canAddItem ? `<button class="btn btn-primary btn-sm" onclick="modalAddItem(${os_id})">+ Adicionar Item</button>` : ''}
    </div>

    <table class="os-items-table">
      <thead>
        <tr>
          <th>Descrição</th>
          <th>Qtd</th>
          <th>Unit.</th>
          <th>Subtotal</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="osItemsTbody">
        ${itensHtml}
      </tbody>
    </table>

    <div class="os-total-row">
      <span>Total:</span>
      <span class="os-total-value">${fmt(os.total)}</span>
    </div>

    <div class="os-actions">
      ${statusActions}
    </div>
  `;
}

function modalAddItem(os_id) {
  openModal('Adicionar Item', `
    <div class="form-group">
      <label>Tipo *</label>
      <select id="fItemTipo">
        <option value="servico">🔧 Serviço</option>
        <option value="peca">🔩 Peça</option>
      </select>
    </div>
    <div class="form-group">
      <label>Descrição *</label>
      <input type="text" id="fItemDesc" placeholder="Ex: Troca de óleo, Pastilha de freio..." />
    </div>
    <div class="form-group">
      <label>Quantidade</label>
      <input type="number" id="fItemQtd" value="1" min="1" />
    </div>
    <div class="form-group">
      <label>Valor Unitário (R$) *</label>
      <input type="number" id="fItemValor" placeholder="0.00" min="0" step="0.01" />
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
    <button class="btn btn-primary" onclick="submitAddItem(${os_id})">Adicionar</button>
  `);
}

async function submitAddItem(os_id) {
  const tipo          = document.getElementById('fItemTipo').value;
  const descricao     = document.getElementById('fItemDesc').value.trim();
  const quantidade    = parseInt(document.getElementById('fItemQtd').value) || 1;
  const valor_unitario = parseFloat(document.getElementById('fItemValor').value);

  if (!descricao) { toast('Descrição é obrigatória', 'err'); return; }
  if (isNaN(valor_unitario) || valor_unitario < 0) { toast('Valor inválido', 'err'); return; }

  const res = await api(`/os/${os_id}/itens`, 'POST', { tipo, descricao, quantidade, valor_unitario });
  if (res.success) {
    toast('Item adicionado!', 'ok');
    closeModal();
    loadOsDetail(os_id);
    // Atualiza linha da tabela
    loadOS();
  } else {
    toast(res.message || 'Erro ao adicionar item', 'err');
  }
}

async function removeItem(item_id, os_id) {
  const res = await api(`/itens/${item_id}`, 'DELETE');
  if (res.success) {
    toast('Item removido', 'ok');
    loadOsDetail(os_id);
    loadOS();
  } else {
    toast(res.message || 'Erro', 'err');
  }
}

async function mudarStatus(os_id, status) {
  const res = await api(`/os/${os_id}/status`, 'PATCH', { status });
  if (res.success) {
    toast(res.message, 'ok');
    loadOsDetail(os_id);
    loadOS();
  } else {
    toast(res.message || 'Erro ao mudar status', 'err');
  }
}

/* ─── SETUP & EVENTS ──────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  // Nav
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.page));
  });

  // Botões de ação das páginas
  document.getElementById('btnNovoCliente').addEventListener('click', modalNovoCliente);
  document.getElementById('btnNovoVeiculo').addEventListener('click', modalNovoVeiculo);
  document.getElementById('btnNovaOS').addEventListener('click', modalNovaOS);

  // Fechar modais
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('osDetailClose').addEventListener('click', closeOsDetail);
  document.getElementById('modalOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('modalOverlay')) closeModal();
  });
  document.getElementById('osDetailOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('osDetailOverlay')) closeOsDetail();
  });

  // Search com debounce
  let searchTimeout;
  document.getElementById('searchClientes').addEventListener('input', e => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => loadClientes(e.target.value), 420);
  });

  document.getElementById('searchVeiculos').addEventListener('input', e => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => loadVeiculos(e.target.value), 420);
  });

  // Filtros de OS
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadOS(btn.dataset.status);
    });
  });

  // Sidebar toggle (mobile)
  document.getElementById('hamburger').addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('open');
  });
  document.getElementById('sidebarToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('open');
  });

  // ESC fecha modais
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeModal(); closeOsDetail(); }
  });

  // Inicia no dashboard
  navigate('dashboard');
});
