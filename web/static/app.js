(function () {
  var RISK_COLORS = {
    LOW: '#3fb950',
    MEDIUM: '#d29922',
    HIGH: '#f85149',
    CRITICAL: '#ff4444',
  };

  var RISK_LABELS = {
    LOW: '低风险',
    MEDIUM: '中等风险',
    HIGH: '高风险',
    CRITICAL: '极高风险',
  };

  var RECOMMENDATIONS = {
    LOW: '该地址风险较低，未发现显著威胁。但仍建议保持警惕。',
    MEDIUM: '该地址存在中等风险，交互时请谨慎。',
    HIGH: '该地址存在高风险，建议避免与该地址进行交易。',
    CRITICAL: '该地址存在极高风险，强烈建议避免任何交互。',
  };

  var ADDRESS_REGEX = /^0x[0-9a-fA-F]{40}$/;
  var CIRCUMFERENCE = 2 * Math.PI * 85;
  var lastScanData = null;

  function $(id) {
    return document.getElementById(id);
  }

  function shortenAddress(addr, chars) {
    chars = chars || 6;
    if (!addr || addr.length < chars * 2 + 4) return addr || '';
    return addr.slice(0, chars + 2) + '...' + addr.slice(-chars);
  }

  function getRiskColor(level) {
    return RISK_COLORS[level] || '#8b949e';
  }

  function escHtml(str) {
    var d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
  }

  function initTabs() {
    var btns = document.querySelectorAll('.tab-btn');
    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btns.forEach(function (b) { b.classList.remove('active'); });
        document.querySelectorAll('.tab-content').forEach(function (s) { s.classList.remove('active'); });
        btn.classList.add('active');
        var tab = $('tab-' + btn.dataset.tab);
        if (tab) tab.classList.add('active');

        if (btn.dataset.tab === 'api-status') {
          loadApiStatus();
        }
      });
    });
  }

  function loadChains() {
    fetch('/api/chains')
      .then(function (r) { return r.json(); })
      .then(function (chains) {
        var select = $('chain-select');
        chains.forEach(function (c) {
          var opt = document.createElement('option');
          opt.value = c.key;
          opt.textContent = c.name;
          select.appendChild(opt);
        });
        renderChainCards(chains);
      })
      .catch(function () {});
  }

  function renderChainCards(chains) {
    var container = $('chain-cards');
    container.innerHTML = '';
    chains.forEach(function (c) {
      var card = document.createElement('div');
      card.className = 'chain-card';
      card.innerHTML =
        '<div class="chain-name">' + escHtml(c.name) + '</div>' +
        '<div class="chain-id">Chain ID: ' + c.chain_id + '</div>' +
        '<span class="chain-tag ' + (c.v2_free ? 'free' : 'paid') + '">' +
        (c.v2_free ? '免费' : '需 API Key') + '</span>';
      container.appendChild(card);
    });
  }

  function validateAddress(addr) {
    return ADDRESS_REGEX.test(addr);
  }

  function handleScan() {
    var addr = $('address-input').value.trim();
    var chain = $('chain-select').value;

    if (!addr) {
      showError('请输入钱包地址');
      return;
    }

    if (!validateAddress(addr)) {
      $('address-input').classList.add('invalid');
      showError('地址格式无效，请输入以 0x 开头的 42 位十六进制地址');
      return;
    }

    $('address-input').classList.remove('invalid');
    $('scan-error').classList.add('hidden');
    $('scan-result').classList.add('hidden');
    $('scan-loading').classList.remove('hidden');

    var btn = $('scan-btn');
    btn.disabled = true;
    btn.textContent = '扫描中...';

    fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address: addr, chain: chain }),
    })
      .then(function (r) {
        if (!r.ok) {
          return r.json().then(function (d) {
            throw new Error(d.detail || '扫描失败');
          });
        }
        return r.json();
      })
      .then(function (data) {
        $('scan-loading').classList.add('hidden');
        renderResult(data);
        $('scan-result').classList.remove('hidden');
      })
      .catch(function (err) {
        $('scan-loading').classList.add('hidden');
        showError(err.message || '网络错误，请稍后重试');
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = '开始扫描';
      });
  }

  function showError(msg) {
    $('scan-error').textContent = msg;
    $('scan-error').classList.remove('hidden');
  }

  function renderResult(data) {
    lastScanData = data;

    $('result-address').textContent = data.address;
    $('result-chain').textContent = data.chain + ' (' + data.chain_id + ')';

    var score = (data.risk_score && data.risk_score.score) || 0;
    var level = (data.risk_score && data.risk_score.level) || 'LOW';
    var color = getRiskColor(level);

    animateGauge(score, level, color);

    $('gauge-label').textContent = RISK_LABELS[level] || level;
    $('gauge-label').style.color = color;

    var bs = (data.risk_score && data.risk_score.blacklist_score) || 0;
    var cs = (data.risk_score && data.risk_score.contract_score) || 0;
    var fs = (data.risk_score && data.risk_score.fund_source_score) || 0;

    renderBreakdown('blacklist', bs, 40);
    renderBreakdown('contract', cs, 30);
    renderBreakdown('fund', fs, 30);

    renderBlacklistTable(data.blacklist_hits || []);
    renderContractTable(data.contract_risks || []);
    renderFundTable(data.fund_source_risks || []);

    var rec = $('recommendation');
    rec.style.borderLeftColor = color;
    rec.innerHTML = '<strong>💡 建议：</strong>' + escHtml(RECOMMENDATIONS[level] || '');
  }

  function animateGauge(score, level, color) {
    var fill = document.querySelector('.gauge-fill');
    fill.style.stroke = color;

    requestAnimationFrame(function () {
      var offset = CIRCUMFERENCE - (CIRCUMFERENCE * score / 100);
      fill.style.strokeDashoffset = offset;
    });

    var scoreEl = $('gauge-score');
    scoreEl.style.color = color;
    var current = 0;
    var target = score;
    var duration = 1000;
    var start = null;

    function step(ts) {
      if (!start) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      current = Math.round(eased * target);
      scoreEl.textContent = current;
      if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  function renderBreakdown(key, value, max) {
    var fill = $('breakdown-' + key);
    var label = $('breakdown-' + key + '-score');
    var pct = max > 0 ? (value / max * 100) : 0;

    var color = '#3fb950';
    if (pct > 66) color = '#ff4444';
    else if (pct > 33) color = '#d29922';

    fill.style.background = color;
    requestAnimationFrame(function () {
      fill.style.width = pct + '%';
    });
    label.textContent = '+' + value;
  }

  function renderBlacklistTable(hits) {
    var container = $('blacklist-table');
    if (!hits.length) {
      container.innerHTML = '<p class="no-risk">✓ 未发现黑名单命中</p>';
      return;
    }
    var html = '<table><tr><th>来源</th><th>类型</th><th>风险等级</th><th>描述</th></tr>';
    hits.forEach(function (h) {
      html += '<tr>' +
        '<td>' + escHtml(h.source) + '</td>' +
        '<td>' + escHtml(h.hit_type) + '</td>' +
        '<td class="risk-' + h.risk_level + '">' + h.risk_level + '</td>' +
        '<td>' + escHtml(h.description) + '</td>' +
        '</tr>';
    });
    html += '</table>';
    container.innerHTML = html;
  }

  function renderContractTable(risks) {
    var container = $('contract-table');
    if (!risks.length) {
      container.innerHTML = '<p class="no-risk">✓ 未发现高风险合约交互</p>';
      return;
    }
    var html = '<table><tr><th>合约地址</th><th>风险类型</th><th>风险等级</th><th>来源</th><th>详情</th></tr>';
    risks.forEach(function (r) {
      html += '<tr>' +
        '<td>' + escHtml(shortenAddress(r.address)) + '</td>' +
        '<td>' + escHtml(r.risk_type) + '</td>' +
        '<td class="risk-' + r.risk_level + '">' + r.risk_level + '</td>' +
        '<td>' + escHtml(r.source) + '</td>' +
        '<td>' + escHtml(r.detail) + '</td>' +
        '</tr>';
    });
    html += '</table>';
    container.innerHTML = html;
  }

  function renderFundTable(risks) {
    var container = $('fund-table');
    if (!risks.length) {
      container.innerHTML = '<p class="no-risk">✓ 未发现资金来源风险</p>';
      return;
    }
    var html = '<table><tr><th>来源地址</th><th>风险类型</th><th>风险等级</th><th>金额</th><th>交易哈希</th></tr>';
    risks.forEach(function (r) {
      var txShort = r.tx_hash ? shortenAddress(r.tx_hash, 8) : 'N/A';
      html += '<tr>' +
        '<td>' + escHtml(shortenAddress(r.source_address)) + '</td>' +
        '<td>' + escHtml(r.risk_type) + '</td>' +
        '<td class="risk-' + r.risk_level + '">' + r.risk_level + '</td>' +
        '<td>' + escHtml(r.amount || '-') + '</td>' +
        '<td>' + escHtml(txShort) + '</td>' +
        '</tr>';
    });
    html += '</table>';
    container.innerHTML = html;
  }

  function loadApiStatus() {
    var loading = $('api-status-loading');
    var table = $('api-status-table');
    var tbody = $('api-status-tbody');
    var btn = $('refresh-api-btn');

    loading.classList.remove('hidden');
    table.classList.add('hidden');
    btn.classList.add('hidden');

    fetch('/api/check-api')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        loading.classList.add('hidden');
        table.classList.remove('hidden');
        btn.classList.remove('hidden');

        tbody.innerHTML = '';
        (data.apis || []).forEach(function (api) {
          var tr = document.createElement('tr');

          var tdName = document.createElement('td');
          tdName.textContent = api.name;

          var tdKey = document.createElement('td');
          tdKey.textContent = api.key_configured ? '✓ 是' : '✗ 否';
          tdKey.className = api.key_configured ? 'status-ok' : 'status-fail';

          var tdSuffix = document.createElement('td');
          tdSuffix.textContent = api.key_suffix;

          var tdResult = document.createElement('td');
          if (api.working) {
            tdResult.textContent = '✓ 正常';
            tdResult.className = 'status-ok';
          } else if (api.key_configured) {
            tdResult.textContent = '✗ 不可用';
            tdResult.className = 'status-fail';
          } else {
            tdResult.textContent = '- 未配置';
            tdResult.className = 'status-skip';
          }

          tr.appendChild(tdName);
          tr.appendChild(tdKey);
          tr.appendChild(tdSuffix);
          tr.appendChild(tdResult);
          tbody.appendChild(tr);
        });
      })
      .catch(function () {
        loading.textContent = '加载失败，请重试';
      });

    loadConfig();
  }

  function loadConfig() {
    var form = $('config-form');
    form.innerHTML = '<p class="config-loading">加载中...</p>';

    fetch('/api/config')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        form.innerHTML = '';
        (data.keys || []).forEach(function (key) {
          var item = document.createElement('div');
          item.className = 'config-item';

          var label = document.createElement('label');
          label.setAttribute('for', 'config-' + key.env_name);

          var labelText = document.createElement('span');
          labelText.className = 'config-label-text';
          labelText.textContent = key.label;

          if (key.configured) {
            var badge = document.createElement('span');
            badge.className = 'config-badge configured';
            badge.textContent = '已配置 (' + key.masked_value + ')';
            labelText.appendChild(badge);
          } else {
            var badge = document.createElement('span');
            badge.className = 'config-badge not-configured';
            badge.textContent = '未配置';
            labelText.appendChild(badge);
          }

          label.appendChild(labelText);

          var desc = document.createElement('span');
          desc.className = 'config-desc';
          desc.textContent = key.description;
          label.appendChild(desc);

          var link = document.createElement('a');
          link.className = 'config-link';
          link.href = key.link;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = '获取 API Key →';
          label.appendChild(link);

          var input = document.createElement('input');
          input.type = 'password';
          input.id = 'config-' + key.env_name;
          input.name = key.env_name;
          input.dataset.configured = key.configured ? '1' : '0';
          input.placeholder = key.configured ? '输入新值以替换，留空保持不变' : '输入 API Key';
          input.autocomplete = 'off';
          input.spellcheck = false;

          var toggle = document.createElement('button');
          toggle.type = 'button';
          toggle.className = 'toggle-visibility';
          toggle.textContent = '👁';
          toggle.title = '显示/隐藏';
          toggle.addEventListener('click', function () {
            if (input.type === 'password') {
              input.type = 'text';
              toggle.textContent = '🔒';
            } else {
              input.type = 'password';
              toggle.textContent = '👁';
            }
          });

          var inputWrap = document.createElement('div');
          inputWrap.className = 'config-input-wrap';
          inputWrap.appendChild(input);
          inputWrap.appendChild(toggle);

          if (key.configured) {
            var delBtn = document.createElement('button');
            delBtn.type = 'button';
            delBtn.className = 'delete-key-btn';
            delBtn.textContent = '✕';
            delBtn.title = '删除此 Key';
            delBtn.addEventListener('click', function () {
              if (confirm('确定要删除 ' + key.label + ' 吗？')) {
                input.value = '';
                input.dataset.delete = '1';
                item.classList.add('mark-delete');
              }
            });
            inputWrap.appendChild(delBtn);
          }

          item.appendChild(label);
          item.appendChild(inputWrap);
          form.appendChild(item);
        });
      })
      .catch(function () {
        form.innerHTML = '<p class="config-loading">加载失败</p>';
      });
  }

  function handleSaveConfig() {
    var form = $('config-form');
    var btn = $('save-config-btn');
    var msg = $('config-message');
    var inputs = form.querySelectorAll('input[name]');
    var keys = {};

    inputs.forEach(function (input) {
      var val = input.value.trim();
      if (val) {
        keys[input.name] = val;
      } else if (input.dataset.delete === '1') {
        keys[input.name] = '';
      }
    });

    if (Object.keys(keys).length === 0) {
      showConfigMessage('info', '没有需要保存的更改');
      return;
    }

    btn.disabled = true;
    btn.textContent = '保存中...';
    msg.classList.add('hidden');

    fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keys: keys }),
    })
      .then(function (r) {
        if (!r.ok) {
          return r.json().then(function (d) {
            throw new Error(d.detail || '保存失败');
          });
        }
        return r.json();
      })
      .then(function (data) {
        var parts = [];
        if (data.saved && data.saved.length) {
          parts.push('已保存: ' + data.saved.join(', '));
        }
        if (data.removed && data.removed.length) {
          parts.push('已删除: ' + data.removed.join(', '));
        }
        showConfigMessage('success', parts.join('；') || '配置已更新');
        loadConfig();
        loadApiStatus();
      })
      .catch(function (err) {
        showConfigMessage('error', err.message || '保存失败');
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = '保存配置';
      });
  }

  function showConfigMessage(type, text) {
    var msg = $('config-message');
    msg.textContent = text;
    msg.className = 'config-message ' + type;
    msg.classList.remove('hidden');
    setTimeout(function () {
      msg.classList.add('hidden');
    }, 5000);
  }

  function downloadFile(filename, content, mimeType) {
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function getExportFilename(ext) {
    if (!lastScanData) return 'report.' + ext;
    var addr = (lastScanData.address || 'unknown').slice(0, 10);
    var chain = lastScanData.chain || 'eth';
    var ts = new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
    return 'risk-report_' + chain + '_' + addr + '_' + ts + '.' + ext;
  }

  function exportJSON() {
    if (!lastScanData) return;
    var json = JSON.stringify(lastScanData, null, 2);
    downloadFile(getExportFilename('json'), json, 'application/json;charset=utf-8');
  }

  function exportHTML() {
    if (!lastScanData) return;
    var d = lastScanData;
    var score = (d.risk_score && d.risk_score.score) || 0;
    var level = (d.risk_score && d.risk_score.level) || 'LOW';
    var color = getRiskColor(level);
    var levelLabel = RISK_LABELS[level] || level;
    var rec = RECOMMENDATIONS[level] || '';

    var blRows = buildHTMLRows(d.blacklist_hits || [], function (h) {
      return '<tr><td>' + escHtml(h.source) + '</td><td>' + escHtml(h.hit_type) + '</td>' +
        '<td style="color:' + getRiskColor(h.risk_level) + '">' + h.risk_level + '</td>' +
        '<td>' + escHtml(h.description) + '</td></tr>';
    });

    var crRows = buildHTMLRows(d.contract_risks || [], function (r) {
      return '<tr><td>' + escHtml(r.address) + '</td><td>' + escHtml(r.risk_type) + '</td>' +
        '<td style="color:' + getRiskColor(r.risk_level) + '">' + r.risk_level + '</td>' +
        '<td>' + escHtml(r.source) + '</td><td>' + escHtml(r.detail) + '</td></tr>';
    });

    var frRows = buildHTMLRows(d.fund_source_risks || [], function (r) {
      return '<tr><td>' + escHtml(r.source_address) + '</td><td>' + escHtml(r.risk_type) + '</td>' +
        '<td style="color:' + getRiskColor(r.risk_level) + '">' + r.risk_level + '</td>' +
        '<td>' + escHtml(r.amount || '-') + '</td><td>' + escHtml(r.tx_hash || 'N/A') + '</td></tr>';
    });

    var html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n' +
      '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n' +
      '<title>Wallet Risk Report - ' + escHtml(d.address) + '</title>\n' +
      '<style>\n' +
      '  body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;background:#0d1117;color:#c9d1d9;}\n' +
      '  h1{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:12px;}\n' +
      '  .score-panel{background:#161b22;border:2px solid ' + color + ';border-radius:12px;padding:24px;text-align:center;margin:20px 0;}\n' +
      '  .score-value{font-size:48px;font-weight:bold;color:' + color + ';}\n' +
      '  .score-bar{background:#21262d;border-radius:8px;height:24px;margin:16px 0;overflow:hidden;}\n' +
      '  .score-fill{height:100%;background:' + color + ';border-radius:8px;width:' + score + '%;}\n' +
      '  .score-level{font-size:20px;font-weight:bold;color:' + color + ';}\n' +
      '  table{width:100%;border-collapse:collapse;margin:16px 0;}\n' +
      '  th{background:#161b22;color:#58a6ff;padding:12px;text-align:left;border:1px solid #30363d;}\n' +
      '  td{padding:10px 12px;border:1px solid #30363d;}\n' +
      '  tr:nth-child(even){background:#161b22;}\n' +
      '  .section{margin:24px 0;}\n' +
      '  .section h2{color:#f0883e;}\n' +
      '  .ok{color:#3fb950;}\n' +
      '  .recommendation{background:#161b22;border-left:4px solid ' + color + ';padding:16px;margin:20px 0;border-radius:4px;}\n' +
      '  .info{color:#8b949e;font-size:14px;}\n' +
      '</style>\n</head>\n<body>\n' +
      '<h1>🔍 Wallet Risk Scanner Report</h1>\n' +
      '<p class="info">地址: <strong>' + escHtml(d.address) + '</strong></p>\n' +
      '<p class="info">链: <strong>' + escHtml(d.chain) + ' (' + d.chain_id + ')</strong></p>\n' +
      '<p class="info">扫描时间: <strong>' + new Date().toLocaleString('zh-CN') + '</strong></p>\n' +
      '<div class="score-panel">\n' +
      '  <div class="score-value">' + score + ' / 100</div>\n' +
      '  <div class="score-bar"><div class="score-fill"></div></div>\n' +
      '  <div class="score-level">' + levelLabel + '</div>\n' +
      '</div>\n' +
      '<div class="section">\n  <h2>⚠️ 黑名单命中 (' + (d.blacklist_hits || []).length + ')</h2>\n' +
      (blRows ? '  <table><tr><th>来源</th><th>类型</th><th>风险等级</th><th>描述</th></tr>\n' + blRows + '  </table>\n' : '  <p class="ok">✓ 未发现黑名单命中</p>\n') +
      '</div>\n' +
      '<div class="section">\n  <h2>⚠️ 高风险合约 (' + (d.contract_risks || []).length + ')</h2>\n' +
      (crRows ? '  <table><tr><th>合约地址</th><th>风险类型</th><th>风险等级</th><th>来源</th><th>详情</th></tr>\n' + crRows + '  </table>\n' : '  <p class="ok">✓ 未发现高风险合约交互</p>\n') +
      '</div>\n' +
      '<div class="section">\n  <h2>⚠️ 资金来源风险 (' + (d.fund_source_risks || []).length + ')</h2>\n' +
      (frRows ? '  <table><tr><th>来源地址</th><th>风险类型</th><th>风险等级</th><th>金额</th><th>交易哈希</th></tr>\n' + frRows + '  </table>\n' : '  <p class="ok">✓ 未发现资金来源风险</p>\n') +
      '</div>\n' +
      '<div class="recommendation">\n  <strong>💡 建议：</strong>' + escHtml(rec) + '\n</div>\n' +
      '</body>\n</html>';

    downloadFile(getExportFilename('html'), html, 'text/html;charset=utf-8');
  }

  function buildHTMLRows(items, rowFn) {
    if (!items || !items.length) return '';
    return items.map(rowFn).join('\n');
  }

  function exportCSV() {
    if (!lastScanData) return;
    var d = lastScanData;
    var lines = [];

    lines.push('类型,地址/来源,风险类型,风险等级,描述/详情,金额,交易哈希');

    (d.blacklist_hits || []).forEach(function (h) {
      lines.push(csvRow(['黑名单', h.source, h.hit_type, h.risk_level, h.description, '', '']));
    });

    (d.contract_risks || []).forEach(function (r) {
      lines.push(csvRow(['合约风险', r.address, r.risk_type, r.risk_level, r.detail, '', '']));
    });

    (d.fund_source_risks || []).forEach(function (r) {
      lines.push(csvRow(['资金来源', r.source_address, r.risk_type, r.risk_level, '', r.amount || '', r.tx_hash || '']));
    });

    var csv = '\uFEFF' + lines.join('\n');
    downloadFile(getExportFilename('csv'), csv, 'text/csv;charset=utf-8');
  }

  function csvRow(fields) {
    return fields.map(function (f) {
      var s = String(f || '');
      if (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\n') >= 0) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    }).join(',');
  }

  function bindEvents() {
    $('scan-btn').addEventListener('click', handleScan);

    $('address-input').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') handleScan();
    });

    $('address-input').addEventListener('input', function () {
      var val = this.value.trim();
      if (val && !validateAddress(val)) {
        this.classList.add('invalid');
      } else {
        this.classList.remove('invalid');
      }
    });

    $('refresh-api-btn').addEventListener('click', loadApiStatus);

    $('save-config-btn').addEventListener('click', handleSaveConfig);

    $('export-json').addEventListener('click', exportJSON);
    $('export-html').addEventListener('click', exportHTML);
    $('export-csv').addEventListener('click', exportCSV);
  }

  function resetGauge() {
    var fill = document.querySelector('.gauge-fill');
    fill.style.strokeDashoffset = CIRCUMFERENCE;
    $('gauge-score').textContent = '0';
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTabs();
    loadChains();
    bindEvents();
    resetGauge();
  });
})();
