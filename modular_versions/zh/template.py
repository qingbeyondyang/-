HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>加密货币毫秒级K线图系统</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 20px; min-height: 100vh;
        }
        .container { max-width: 1900px; margin: 0 auto; background: #fff; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); padding: 30px; }
        h1 { text-align: center; color: #1a1a2e; margin-bottom: 8px; font-size: 30px; font-weight: 800; }
        .subtitle { text-align: center; color: #666; margin-bottom: 25px; font-size: 13px; }

        /* TABS */
        .tab-nav { display: flex; gap: 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 25px; }
        .tab-btn { padding: 11px 26px; background: #f5f7fa; border: none; border-bottom: 2px solid transparent;
            cursor: pointer; font-size: 14px; font-weight: 600; color: #666; transition: all .2s;
            border-radius: 8px 8px 0 0; margin-bottom: -2px; }
        .tab-btn.active { background: white; color: #0f3460; border-bottom: 2px solid #0f3460; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* PANELS */
        .config-panel { background: linear-gradient(135deg, #f5f7fa 0%, #dde8ff 100%);
            padding: 22px; border-radius: 12px; margin-bottom: 22px; }
        .config-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 18px; }
        .config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin-bottom: 18px; }
        .control-group { display: flex; flex-direction: column; gap: 6px; }
        label { font-weight: 600; color: #555; font-size: 12px; }
        select, input { padding: 10px 13px; border: 2px solid #dde; border-radius: 8px; font-size: 13px;
            transition: all .3s; background: white; }
        select:focus, input:focus { outline: none; border-color: #0f3460; box-shadow: 0 0 0 3px rgba(15,52,96,.1); }

        .button-group { display: flex; gap: 12px; flex-wrap: wrap; }
        button { padding: 11px 24px; background: linear-gradient(135deg, #0f3460, #533483);
            color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;
            font-size: 13px; transition: all .3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(15,52,96,.4); }
        button:disabled { background: #ccc; cursor: not-allowed; transform: none; box-shadow: none; }
        .btn-success { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .btn-danger  { background: linear-gradient(135deg, #ee0979, #ff6a00); }
        .btn-info    { background: linear-gradient(135deg, #4facfe, #00f2fe); }
        .btn-warn    { background: linear-gradient(135deg, #f7971e, #ffd200); }
        .btn-sm      { padding: 7px 14px; font-size: 12px; }

        /* STATUS */
        .status-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px; margin-bottom: 22px; }
        .status-item { background: white; padding: 14px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,.08); border-left: 4px solid #0f3460; }
        .status-label { font-size: 10px; color: #888; font-weight: 700; text-transform: uppercase;
            letter-spacing: .5px; margin-bottom: 5px; }
        .status-value { font-size: 17px; font-weight: 700; color: #1a1a2e; font-family: Consolas, monospace; }
        .status-running { color: #16c784; }
        .status-stopped { color: #ea3943; }
        .price-up   { color: #16c784; }
        .price-down { color: #ea3943; }

        #chart, #historyChart { width: 100%; height: 640px; border: 1px solid #1f2a44;
            border-radius: 10px; overflow: hidden; background: #0b1220; margin-bottom: 20px; }
        #chart .modebar, #historyChart .modebar { background: rgba(15,21,35,.55) !important; border-radius: 8px; }
        #chart .modebar-btn path, #historyChart .modebar-btn path { fill: #b8c6df !important; }
        #chart .modebar-btn:hover path, #historyChart .modebar-btn:hover path { fill: #ffffff !important; }
        .alert { padding: 13px 18px; border-radius: 8px; margin-bottom: 18px; font-weight: 500;
            display: flex; align-items: center; gap: 10px; animation: slideIn .3s ease-out; font-size: 13px; }
        @keyframes slideIn { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }
        .alert-info    { background:#d1ecf1; color:#0c5460; border-left:4px solid #17a2b8; }
        .alert-success { background:#d4edda; color:#155724; border-left:4px solid #28a745; }
        .alert-warning { background:#fff3cd; color:#856404; border-left:4px solid #ffc107; }
        .alert-error   { background:#f8d7da; color:#721c24; border-left:4px solid #dc3545; }

        .chart-controls { background:#f8f9fa; padding:18px; border-radius:10px; margin-bottom:18px; }

        /* FUNDING TABLE */
        .funding-table { width:100%; border-collapse:collapse; font-size:13px; margin-top:12px; }
        .funding-table th { background:#0f3460; color:white; padding:9px 13px; text-align:left; font-weight:600; font-size:12px; }
        .funding-table td { padding:9px 13px; border-bottom:1px solid #eee; vertical-align:middle; }
        .funding-table tr:hover td { background:#f0f4ff; }
        .funding-table tr.selected td { background:#dde8ff; }
        .rate-positive { color:#ea3943; font-weight:700; }   /* 多付空：做多者不利 */
        .rate-negative { color:#16c784; font-weight:700; }   /* 空付多：做多者有利 */
        .badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:700; }
        .badge-long  { background:#fde8e8; color:#c0392b; }
        .badge-short { background:#e8f8f0; color:#27ae60; }

        /* FUNDING STATUS PANEL */
        .funding-dash { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-bottom:18px; }
        .fd-card { background:white; border-radius:10px; padding:16px; box-shadow:0 2px 10px rgba(0,0,0,.08); }
        .fd-card-title { font-size:11px; color:#888; font-weight:700; text-transform:uppercase; margin-bottom:8px; }
        .fd-card-value { font-size:20px; font-weight:800; color:#1a1a2e; font-family:Consolas,monospace; }
        .fd-card-sub { font-size:11px; color:#888; margin-top:4px; }

        .phase-idle       { color:#888; }
        .phase-pre        { color:#f7971e; font-weight:700; }
        .phase-collecting { color:#16c784; font-weight:700; animation:blink 1s infinite; }
        .phase-post       { color:#4facfe; font-weight:700; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.5} }

        /* 日志 */
        .log-box { background:#1a1a2e; border-radius:8px; padding:14px; height:200px;
            overflow-y:auto; font-family:Consolas,monospace; font-size:12px; color:#a8d8a8; }

        /* 文件浏览器 */
        .file-table { width:100%; border-collapse:collapse; font-size:13px; }
        .file-table th { background:#0f3460; color:white; padding:9px 13px; text-align:left; position:sticky; top:0; z-index:2; }
        .file-table td { padding:9px 13px; border-bottom:1px solid #eee; vertical-align:middle; }
        .file-table tr:hover td { background:#f0f4ff; }
        .file-table tr.selected td { background:#dde8ff; }
        .file-list-scroll { max-height:520px; overflow:auto; border:1px solid #e8ecf4; border-radius:8px; background:white; }
        .file-actions { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:0 0 10px 0; flex-wrap:wrap; }
        .file-actions .left, .file-actions .right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
        .file-select-count { font-size:12px; color:#555; font-weight:600; }
        .file-check-col { width:38px; text-align:center; }
        .file-check-col input { transform:scale(1.1); cursor:pointer; }

        .history-status { background:white; border-radius:8px; padding:12px 20px;
            margin-bottom:12px; display:flex; gap:20px; flex-wrap:wrap;
            box-shadow:0 2px 8px rgba(0,0,0,.08); font-size:12px; }
        .trade-tools-panel { margin-top:12px; background:#fff; border:1px solid #e6ebf5; border-radius:8px; padding:12px; }
        .trade-tools-title { font-size:13px; font-weight:700; margin-bottom:8px; color:#1f2d3d; }
        .trade-result { margin-top:10px; font-size:12px; color:#1f2d3d; line-height:1.8; }
        .funding-panel { margin-top:10px; border:1px solid #e2e9f7; border-radius:8px; padding:10px; background:#f8fbff; }
        .funding-panel.disabled { opacity:.6; }
        .funding-note { font-size:12px; color:#5a6786; margin-top:6px; }

        /* 多选tag */
        .symbol-tags { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
        .symbol-tag { display:flex; align-items:center; gap:4px; background:#0f3460;
            color:white; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:600; }
        .symbol-tag .remove { cursor:pointer; opacity:.7; }
        .symbol-tag .remove:hover { opacity:1; }

        .loading { text-align:center; padding:40px; color:#999; }
        .loading-spinner { border:4px solid #f3f3f3; border-top:4px solid #0f3460; border-radius:50%;
            width:36px; height:36px; animation:spin 1s linear infinite; margin:0 auto 16px; }
        @keyframes spin { 0%{transform:rotate(0)} 100%{transform:rotate(360deg)} }

        hr { border:none; border-top:1px solid #eee; margin:18px 0; }

        /* 倒计时 */
        .countdown-bar { background:#fff3cd; border:1px solid #ffc107; border-radius:8px;
            padding:10px 18px; display:flex; align-items:center; gap:10px; margin-bottom:16px; font-size:13px; }
        .countdown-num { font-size:22px; font-weight:800; color:#e67e22; font-family:Consolas,monospace; min-width:80px; }
    </style>
</head>
<body>
<div class="container">
    <h1>📊 加密货币毫秒级K线图系统 Pro</h1>
    <div class="subtitle">实时采集 · 资费率监控 · 自动窗口采集 · 历史文件查看 | 毫秒级精度</div>

    <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab('live')">🔴 实时采集</button>
        <button class="tab-btn" onclick="switchTab('funding')">💰 资费率自动采集</button>
        <button class="tab-btn" onclick="switchTab('history')">📂 历史文件</button>
    </div>

    <!-- ══════════ TAB: 实时采集 ══════════ -->
    <div id="tab-live" class="tab-content active">
        <div class="config-panel">
            <div class="config-title">⚙️ 数据采集配置</div>
            <div class="config-grid">
                <div class="control-group">
                    <label>🏦 交易所</label>
                    <select id="exchange">
                        <option value="binance">币安 (Binance)</option>
                        <option value="bybit">Bybit</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>💰 币种名称</label>
                    <input type="text" id="symbol" value="BTC" placeholder="如: BTC, ETH" style="text-transform:uppercase" list="symbolList">
                    <datalist id="symbolList">
                        <option value="BTC"><option value="ETH"><option value="SOL">
                        <option value="BNB"><option value="XRP"><option value="DOGE">
                        <option value="PEPE"><option value="WIF"><option value="BONK">
                    </datalist>
                </div>
                <div class="control-group">
                    <label>📁 文件名</label>
                    <input type="text" id="filename" value="price_data">
                </div>
                <div class="control-group">
                    <label>💾 保存文件夹</label>
                    <input type="text" id="saveFolder" value="data">
                </div>
                <div class="control-group">
                    <label>📄 格式</label>
                    <select id="format">
                        <option value="csv">CSV</option>
                        <option value="json">JSON</option>
                    </select>
                </div>
            </div>
            <div class="button-group">
                <button class="btn-success" onclick="startCollection()" id="startBtn">▶️ 开始采集</button>
                <button class="btn-danger"  onclick="stopCollection()"  id="stopBtn" disabled>⏹️ 停止</button>
                <button class="btn-info"    onclick="downloadData()">💾 下载</button>
                <button onclick="clearData()">🗑️ 清空</button>
            </div>
        </div>
        <div id="alertBox"></div>
        <div class="status-bar">
            <div class="status-item"><div class="status-label">状态</div><div class="status-value status-stopped" id="collectionStatus">已停止</div></div>
            <div class="status-item"><div class="status-label">交易所</div><div class="status-value" id="currentExchange">--</div></div>
            <div class="status-item"><div class="status-label">交易对</div><div class="status-value" id="currentSymbol">--</div></div>
            <div class="status-item"><div class="status-label">数据条数</div><div class="status-value" id="dataCount">0</div></div>
            <div class="status-item"><div class="status-label">最新价格</div><div class="status-value" id="latestPrice">--</div></div>
            <div class="status-item"><div class="status-label">K线数量</div><div class="status-value" id="candleCount">0</div></div>
        </div>
        <div class="chart-controls">
            <div class="config-grid">
                <div class="control-group">
                    <label>📈 K线周期 (毫秒)</label>
                    <select id="klineInterval">
                        <option value="10">10ms</option><option value="50">50ms</option>
                        <option value="100">100ms</option><option value="250">250ms</option>
                        <option value="500" selected>500ms</option><option value="1000">1s</option>
                        <option value="2000">2s</option><option value="5000">5s</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>📊 显示K线数</label>
                    <input type="number" id="maxCandles" value="100" min="20" max="1000" step="10">
                </div>
                <div class="control-group">
                    <label>🔄 刷新间隔</label>
                    <select id="refreshInterval">
                        <option value="1">1秒</option><option value="2" selected>2秒</option>
                        <option value="5">5秒</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>&nbsp;</label>
                    <button onclick="toggleAutoRefresh()" id="autoRefreshBtn">▶️ 自动刷新</button>
                </div>
            </div>
        </div>
        <div id="chart"></div>
    </div>

    <!-- ══════════ TAB: 资费率自动采集 ══════════ -->
    <div id="tab-funding" class="tab-content">

        <!-- 监控配置 -->
        <div class="config-panel">
            <div class="config-title">💰 资费率监控 & 自动采集配置</div>
            <div class="config-grid">
                <div class="control-group">
                    <label>🏆 展示TOP N个币种</label>
                    <input type="number" id="topN" value="5" min="1" max="20">
                </div>
                <div class="control-group">
                    <label>⏰ 结算前X分钟开始采集</label>
                    <input type="number" id="preMinutes" value="10" min="1" max="60">
                </div>
                <div class="control-group">
                    <label>⏰ 结算后X分钟停止采集</label>
                    <input type="number" id="postMinutes" value="10" min="1" max="60">
                </div>
                <div class="control-group">
                    <label>💾 保存文件夹</label>
                    <input type="text" id="fundingFolder" value="/opt/trading/app/data/funding">
                </div>
                <div class="control-group">
                    <label>🔥 最低24h成交额(亿U) <span style="color:#e67e22;font-size:10px">过滤极低流动性</span></label>
                    <input type="number" id="minVolumeUsd" value="0.3" min="0" step="0.1"
                           title="低于此24h成交额的币种不纳入采集。0=完全不过滤。建议0.3亿以上保证最基本流动性">
                    <small style="color:#888;font-size:10px;margin-top:2px">0=不过滤 | 0.3=3000万U(推荐) | 5=5亿U(主流币)</small>
                </div>
                <div class="control-group">
                    <label>📄 保存格式</label>
                    <select id="fundingFormat">
                        <option value="csv">CSV</option>
                        <option value="json">JSON</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>⚡ 采集频率（最小间隔）</label>
                    <select id="minIntervalMs">
                        <option value="0">全量逐笔（最高频，约1~10ms）</option>
                        <option value="10">10ms</option>
                        <option value="50">50ms</option>
                        <option value="100">100ms</option>
                        <option value="250">250ms</option>
                        <option value="500" selected>500ms（推荐）</option>
                        <option value="1000">1秒</option>
                        <option value="2000">2秒</option>
                        <option value="5000">5秒</option>
                    </select>
                    <small style="color:#888;font-size:11px;margin-top:3px">节流：每隔X毫秒保存一条，0=全量写入（文件大）</small>
                </div>
            </div>
            <hr>
            <div class="config-title" style="font-size:13px;margin-bottom:10px">🎯 指定采集币种 (空=自动采集资费率最高币种)</div>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                <input type="text" id="addSymbolInput" placeholder="输入币种，如 BTC" style="width:180px;text-transform:uppercase" list="symbolList2">
                <datalist id="symbolList2">
                    <option value="BTC"><option value="ETH"><option value="SOL"><option value="BNB">
                    <option value="XRP"><option value="DOGE"><option value="PEPE"><option value="WIF">
                </datalist>
                <button class="btn-sm btn-info" onclick="addSelectedSymbol()">➕ 添加</button>
                <button class="btn-sm" onclick="clearSelectedSymbols()">🗑 清空</button>
            </div>
            <div class="symbol-tags" id="selectedSymbolTags"></div>
            <hr>
            <div class="button-group" style="margin-top:6px">
                <button class="btn-success" onclick="startFundingMonitor()" id="fundingStartBtn">🚀 启动资费监控</button>
                <button class="btn-danger"  onclick="stopFundingMonitor()"  id="fundingStopBtn" disabled>⏹️ 停止监控</button>
                <button class="btn-info"    onclick="refreshFundingRates()">🔄 立即刷新资费率</button>
            </div>
        </div>

        <div id="fundingAlertBox"></div>

        <!-- 倒计时 -->
        <div class="countdown-bar" id="countdownBar" style="display:none">
            <span>⏰ 距下次结算:</span>
            <span class="countdown-num" id="countdownNum">--:--:--</span>
            <span id="countdownPhase" class="phase-idle">待机中</span>
            <span style="margin-left:auto;font-size:11px;color:#888" id="nextFundingTs"></span>
        </div>

        <!-- 监控仪表盘 -->
        <div class="funding-dash" id="fundingDash">
            <div class="fd-card">
                <div class="fd-card-title">监控状态</div>
                <div class="fd-card-value" id="fd-status">未启动</div>
            </div>
            <div class="fd-card">
                <div class="fd-card-title">采集阶段</div>
                <div class="fd-card-value phase-idle" id="fd-phase">idle</div>
            </div>
            <div class="fd-card">
                <div class="fd-card-title">活跃采集器</div>
                <div class="fd-card-value" id="fd-active">0</div>
            </div>
            <div class="fd-card">
                <div class="fd-card-title">最后刷新</div>
                <div class="fd-card-value" id="fd-lastfetch" style="font-size:14px">--</div>
            </div>
        </div>

        <!-- 资费率排行 -->
        <div class="config-panel">
            <div class="config-title">📊 资费率排行 (按绝对值降序，已过滤低流动性小币) <span style="font-size:12px;color:#888;font-weight:400">— 负=空付多(做多受益)，正=多付空(做空受益) | 空选=自动采集TOP N</span></div>
            <div id="fundingTableArea">
                <div class="loading" style="padding:20px;color:#aaa">点击「立即刷新资费率」加载数据</div>
            </div>
        </div>

        <!-- 活跃采集信息 -->
        <div class="config-panel" id="activeCollectPanel" style="display:none">
            <div class="config-title">📡 当前自动采集中
                <span style="font-size:11px;font-weight:400;color:#667eea;margin-left:10px">
                    🔵 第1个币激活「实时采集Tab」主采集器，数据完整可实时查看K线 ｜ 其余币独立存文件
                </span>
            </div>
            <div id="activeCollectInfo"></div>
        </div>

        <!-- 日志 -->
        <div class="config-panel">
            <div class="config-title">📜 采集日志</div>
            <div class="log-box" id="collectLog">💤 待机中 | 结算前11分钟→拉取资费率锁定名单 | 结算前10分钟→启动采集 | 第1币激活实时Tab可实时看K线</div>
        </div>
    </div>

    <!-- ══════════ TAB: 历史文件 ══════════ -->
    <div id="tab-history" class="tab-content">
        <div class="config-panel">
            <div class="config-title">📂 历史文件浏览器</div>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px">
                <input type="text" id="historyFolder" value="/opt/trading/app/data/basic" placeholder="文件夹路径" style="flex:2">
                <button class="btn-info btn-sm" onclick="loadFileList()">🔍 浏览</button>
                <button class="btn-sm" onclick="document.getElementById('historyFolder').value='data/funding';loadFileList()">📂 查看资费数据</button>
            </div>
            <div id="fileListArea"><div class="loading" style="padding:20px;color:#aaa">请输入文件夹路径后点击浏览</div></div>
        </div>
        <div id="historyAlertBox"></div>
        <div class="chart-controls" id="historyChartControls" style="display:none">
            <div class="config-grid">
                <div class="control-group">
                    <label>📈 K线周期(毫秒)</label>
                    <select id="historyKlineInterval">
                        <option value="10">10ms</option><option value="50">50ms</option>
                        <option value="100">100ms</option><option value="250">250ms</option>
                        <option value="500" selected>500ms</option><option value="1000">1s</option>
                        <option value="2000">2s</option><option value="5000">5s</option>
                        <option value="10000">10s</option><option value="30000">30s</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>📊 显示K线数</label>
                    <input type="number" id="historyMaxCandles" value="200" min="20" max="2000" step="10">
                </div>
                <div class="control-group">
                    <label>&nbsp;</label>
                    <button class="btn-success btn-sm" onclick="renderHistoryChart()">📊 重新绘制</button>
                </div>
            </div>
            <div class="trade-tools-panel">
                <div class="trade-tools-title">🧪 交易回测工具（画线预测）</div>
                <div class="config-grid">
                    <div class="control-group">
                        <label>方向</label>
                        <select id="tradeSide">
                            <option value="long">做多</option>
                            <option value="short">做空</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label>入场价</label>
                        <input type="number" id="tradeEntryPrice" step="0.00000001" placeholder="例如 0.1428">
                    </div>
                    <div class="control-group">
                        <label>止损价</label>
                        <input type="number" id="tradeStopPrice" step="0.00000001" placeholder="例如 0.1415">
                    </div>
                    <div class="control-group">
                        <label>止盈价</label>
                        <input type="number" id="tradeTargetPrice" step="0.00000001" placeholder="例如 0.1460">
                    </div>
                    <div class="control-group">
                        <label>出场价</label>
                        <input type="number" id="tradeExitPrice" step="0.00000001" placeholder="由矩形右侧交点自动生成，可手调">
                    </div>
                    <div class="control-group">
                        <label>仓位金额(USDT)</label>
                        <input type="number" id="tradePositionSize" value="100" min="1" step="1">
                    </div>
                    <div class="control-group">
                        <label>&nbsp;</label>
                        <button class="btn-info btn-sm" onclick="applyHistoryTradeBacktest()">📐 画线回测</button>
                    </div>
                    <div class="control-group">
                        <label>&nbsp;</label>
                        <button class="btn-warn btn-sm" onclick="startDragAreaBacktest()">🖱️ 区域拖拽回测</button>
                    </div>
                    <div class="control-group">
                        <label>&nbsp;</label>
                        <button class="btn-sm" onclick="clearHistoryTradeBacktest()">🧹 清除回测线</button>
                    </div>
                </div>
                <div style="font-size:12px;color:#667; margin-top:6px;">
                    区域拖拽回测：点击按钮后，在图上拖一个矩形区域（左边界交点=入场，右边界交点=出场，上下边界=止盈/止损）。
                </div>
                <div style="font-size:12px;color:#667; margin-top:4px;">
                    生成回测后，可直接拖动图上的入场/止盈/止损线，系统会自动更新收益和盈亏比。
                </div>
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px;">
                    <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:#445;">
                        <input type="checkbox" id="zoomToSelection" checked>
                        拖拽后自动放大到选区
                    </label>
                    <button class="btn-sm" onclick="resetHistoryChartZoom()">🔎 重置缩放</button>
                </div>
                <div class="funding-panel disabled" id="fundingPanel">
                    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:8px;">
                        <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:#34425f;font-weight:700;">
                            <input type="checkbox" id="enableFundingRate" onchange="toggleFundingInputs()">
                            启用资金费率结算
                        </label>
                    </div>
                    <div class="config-grid" style="margin-bottom:0;">
                        <div class="control-group">
                            <label>资金费率(%)</label>
                            <input type="number" id="fundingRatePct" step="0.0001" value="0.01" disabled>
                        </div>
                        <div class="control-group">
                            <label>结算时间</label>
                            <input type="datetime-local" id="fundingSettleTime" disabled>
                        </div>
                        <div class="control-group">
                            <label>结算次数(手动)</label>
                            <input type="number" id="fundingSettleCount" min="0" step="1" value="1" disabled>
                        </div>
                    </div>
                    <div class="funding-note">
                        方向说明：正费率(+) 为「多付空」；负费率(-) 为「空付多」。可填结算时间用于单次判断，或直接用结算次数手动指定。
                    </div>
                </div>
                <div id="tradeBacktestResult" class="trade-result"></div>
            </div>
        </div>
        <div id="historyStatus" class="history-status" style="display:none"></div>
        <div id="historyChart" style="display:none"></div>
    </div>
</div>

<script>
// ─── 全局 ───
let autoRefreshInterval = null;
let lastPrice = null;
let historyData = [];
let selectedFilePath = '';
let fileRegistry = {};
let selectedHistoryFileIndexes = new Set();
let historyRangeSelectMode = false;
let historyRangeAnchorIndex = null;
let historyKlines = [];
let historyTradeBacktest = null;
let dragBacktestArmed = false;
let selectedSymbols = [];
let fundingPollTimer = null;

// ─── TAB ───
function switchTab(name) {
    const tabs = ['live','funding','history'];
    tabs.forEach((t,i) => {
        document.querySelectorAll('.tab-btn')[i].classList.toggle('active', t===name);
        document.getElementById(`tab-${t}`).classList.toggle('active', t===name);
    });
    if (name === 'funding') startFundingPoll();
    else stopFundingPoll();
}

// ─── 格式化 ───
function formatPrice(p) {
    if (p>=1000)   return p.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
    if (p>=1)      return p.toLocaleString('en-US',{minimumFractionDigits:4,maximumFractionDigits:4});
    if (p>=0.01)   return p.toLocaleString('en-US',{minimumFractionDigits:6,maximumFractionDigits:6});
    if (p>=0.0001) return p.toLocaleString('en-US',{minimumFractionDigits:8,maximumFractionDigits:8});
    return p.toLocaleString('en-US',{minimumFractionDigits:10,maximumFractionDigits:10});
}

function showAlert(msg, type='info', boxId='alertBox') {
    const icons={info:'ℹ️',success:'✅',warning:'⚠️',error:'❌'};
    document.getElementById(boxId).innerHTML=
        `<div class="alert alert-${type}"><span>${icons[type]}</span><span>${msg}</span></div>`;
    setTimeout(()=>document.getElementById(boxId).innerHTML='',6000);
}

function secToHMS(sec) {
    if (sec < 0) sec = 0;
    const h = Math.floor(sec/3600), m = Math.floor((sec%3600)/60), s = sec%60;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

// ─────────────── 实时采集 (原有逻辑) ───────────────
async function startCollection() {
    let symbol = document.getElementById('symbol').value.trim().toUpperCase();
    const exchange = document.getElementById('exchange').value;
    const filename = document.getElementById('filename').value;
    const saveFolder = document.getElementById('saveFolder').value;
    const format = document.getElementById('format').value;
    if (!symbol) { showAlert('请输入币种','warning'); return; }
    if (!symbol.endsWith('USDT')) symbol += 'USDT';
    try {
        const res = await fetch('/api/start', {method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({exchange, symbol, filename, saveFolder, format})});
        const r = await res.json();
        if (r.success) {
            document.getElementById('startBtn').disabled=true;
            document.getElementById('stopBtn').disabled=false;
            document.getElementById('collectionStatus').textContent='运行中';
            document.getElementById('collectionStatus').className='status-value status-running';
            document.getElementById('currentExchange').textContent=exchange.toUpperCase();
            document.getElementById('currentSymbol').textContent=symbol;
            showAlert(`开始采集 ${symbol}`,'success');
            if (!autoRefreshInterval) toggleAutoRefresh();
        } else showAlert(r.message,'error');
    } catch(e){ showAlert(`启动失败: ${e.message}`,'error'); }
}
async function stopCollection() {
    try {
        await fetch('/api/stop',{method:'POST'});
        document.getElementById('startBtn').disabled=false;
        document.getElementById('stopBtn').disabled=true;
        document.getElementById('collectionStatus').textContent='已停止';
        document.getElementById('collectionStatus').className='status-value status-stopped';
        showAlert('采集已停止','info');
    } catch(e){ showAlert(`停止失败: ${e.message}`,'error'); }
}
async function downloadData() {
    const fmt=document.getElementById('format').value, fn=document.getElementById('filename').value;
    const res = await fetch(`/api/download?format=${fmt}&filename=${fn}`);
    if(res.ok){ const b=await res.blob(); const u=URL.createObjectURL(b);
        const a=document.createElement('a'); a.href=u; a.download=`${fn}.${fmt}`;
        document.body.appendChild(a); a.click(); URL.revokeObjectURL(u); a.remove(); }
}
async function clearData() {
    if(!confirm('确定清空内存数据？')) return;
    await fetch('/api/clear',{method:'POST'});
    document.getElementById('dataCount').textContent='0';
    document.getElementById('candleCount').textContent='0';
    document.getElementById('latestPrice').textContent='--';
    document.getElementById('chart').innerHTML='<div class="loading"><p>数据已清空</p></div>';
}
function aggregateToKlines(data, ms) {
    if(!data||!data.length) return [];
    const klines=[]; let cur=null;
    data.forEach(t=>{
        const tm=Math.floor(t.timestamp/ms)*ms, p=t.price, v=t.quantity;
        if(!cur||cur.time!==tm){ if(cur)klines.push(cur); cur={time:tm,open:p,high:p,low:p,close:p,volume:v}; }
        else{ cur.high=Math.max(cur.high,p); cur.low=Math.min(cur.low,p); cur.close=p; cur.volume+=v; }
    });
    if(cur)klines.push(cur);
    return klines;
}
function formatTime(ts){ const d=new Date(ts);
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}.${String(d.getMilliseconds()).padStart(3,'0')}`; }
function calcKlineChangePct(k){ return k && k.open ? ((k.close-k.open)/k.open)*100 : 0; }
function calcKlineAmplitudePct(k){ return k && k.open ? ((k.high-k.low)/k.open)*100 : 0; }
function getKlineIndexFromXValue(xVal, xData){
    if(!xData||!xData.length||xVal===undefined||xVal===null) return -1;
    const s=String(xVal);
    let idx=xData.indexOf(s);
    if(idx>=0) return idx;
    const n=Number(s);
    if(Number.isFinite(n)){
        const rounded=Math.round(n);
        if(rounded>=0&&rounded<xData.length) return rounded;
    }
    return -1;
}
function normalizeRectByKlines(rect){
    if(!rect||!historyKlines.length) return null;
    const xData=historyKlines.map(k=>formatTime(k.time));
    let leftIdx=getKlineIndexFromXValue(rect.x0,xData);
    let rightIdx=getKlineIndexFromXValue(rect.x1,xData);
    if(leftIdx<0||rightIdx<0) return null;
    if(leftIdx>rightIdx){ const t=leftIdx; leftIdx=rightIdx; rightIdx=t; }
    const y0=Number(rect.y0), y1=Number(rect.y1);
    if(!Number.isFinite(y0)||!Number.isFinite(y1)) return null;
    return {
        leftIdx, rightIdx,
        x0:xData[leftIdx], x1:xData[rightIdx],
        top:Math.max(y0,y1), bottom:Math.min(y0,y1)
    };
}
function getCurrentSelectionRectByKlines(){
    if(!historyTradeBacktest || !historyTradeBacktest.selectionRect || !historyKlines.length) return null;
    const sr=historyTradeBacktest.selectionRect;
    const leftIdx=Math.max(0, Math.min(historyKlines.length-1, parseInt(sr.leftIdx ?? 0, 10)));
    const rightIdx=Math.max(0, Math.min(historyKlines.length-1, parseInt(sr.rightIdx ?? historyKlines.length-1, 10)));
    const l=Math.min(leftIdx, rightIdx), r=Math.max(leftIdx, rightIdx);
    const xData=historyKlines.map(k=>formatTime(k.time));
    const top=Number(sr.top), bottom=Number(sr.bottom);
    return {
        leftIdx:l, rightIdx:r,
        x0:xData[l], x1:xData[r],
        top:Number.isFinite(top)?top:Math.max(historyKlines[l].high, historyKlines[r].high),
        bottom:Number.isFinite(bottom)?bottom:Math.min(historyKlines[l].low, historyKlines[r].low)
    };
}
function toggleFundingInputs(){
    const enabled=document.getElementById('enableFundingRate').checked;
    const panel=document.getElementById('fundingPanel');
    ['fundingRatePct','fundingSettleTime','fundingSettleCount'].forEach(id=>{
        const el=document.getElementById(id);
        if(el) el.disabled=!enabled;
    });
    if(panel) panel.classList.toggle('disabled', !enabled);
    if(historyKlines.length && historyTradeBacktest) applyHistoryTradeBacktest();
}
function getSelectionTimeRange(){
    const sel=getCurrentSelectionRectByKlines();
    if(!sel||!historyKlines.length) return null;
    const st=historyKlines[sel.leftIdx]?.time;
    const et=historyKlines[sel.rightIdx]?.time;
    if(!Number.isFinite(st)||!Number.isFinite(et)) return null;
    return {start:Math.min(st,et), end:Math.max(st,et)};
}
function calcFundingAdjustment(side, positionUsdt){
    const enabledEl=document.getElementById('enableFundingRate');
    const enabled=!!(enabledEl && enabledEl.checked);
    if(!enabled) return {enabled:false,pnl:0,count:0,rate:0,manual:false,timeUsed:false,timeHit:false};
    const ratePct=parseFloat(document.getElementById('fundingRatePct').value) || 0;
    const rate=ratePct/100;
    const countRaw=parseFloat(document.getElementById('fundingSettleCount').value);
    let count=Number.isFinite(countRaw)&&countRaw>=0?Math.floor(countRaw):0;
    let timeUsed=false, timeHit=false;
    const settleStr=(document.getElementById('fundingSettleTime').value||'').trim();
    if(count===0 && settleStr){
        const settleMs=new Date(settleStr).getTime();
        if(Number.isFinite(settleMs)){
            timeUsed=true;
            const range=getSelectionTimeRange();
            if(range){
                timeHit=(settleMs>=range.start&&settleMs<=range.end);
                count=timeHit?1:0;
            }else{
                count=1;
            }
        }
    }
    if(count===0) count=1;
    const pnl = side==='long'
        ? (-positionUsdt * rate * count)
        : ( positionUsdt * rate * count);
    return {enabled:true,pnl,count,rate,manual:Number.isFinite(countRaw)&&countRaw>0,timeUsed,timeHit};
}
function getBacktestShapeIndexMap(){
    const hasSel=!!(historyTradeBacktest && historyTradeBacktest.selectionRect);
    const hasExit=!!(historyTradeBacktest && Number.isFinite(Number(historyTradeBacktest.exit)) && Number(historyTradeBacktest.exit)>0);
    const map={
        selectionRect:hasSel?0:-1,
        profitRect:hasSel?1:0,
        riskRect:hasSel?2:1,
        entryLine:hasSel?3:2,
        stopLine:hasSel?4:3,
        targetLine:hasSel?5:4,
        exitLine:-1
    };
    if(hasExit) map.exitLine=hasSel?6:5;
    return map;
}
function getBacktestOverlay(klines){
    if(!historyTradeBacktest || !klines.length) return {traces:[], shapes:[], annotations:[]};
    const x=klines.map(k=>formatTime(k.time));
    const sel=getCurrentSelectionRectByKlines();
    const useSel=sel && sel.x0 && sel.x1;
    const x0=useSel?sel.x0:x[0];
    const x1=useSel?sel.x1:x[x.length-1];
    const entry=historyTradeBacktest.entry;
    const stop=historyTradeBacktest.stop;
    const target=historyTradeBacktest.target;
    const exit=historyTradeBacktest.exit;
    const isLong=historyTradeBacktest.side==='long';
    const profitTop=Math.max(entry,target), profitBottom=Math.min(entry,target);
    const riskTop=Math.max(entry,stop), riskBottom=Math.min(entry,stop);
    const rr=Math.abs((target-entry)/Math.max(Math.abs(entry-stop),1e-12));
    const selTop = useSel && Number.isFinite(Number(sel.top)) ? Number(sel.top) : Math.max(profitTop, riskTop);
    const selBottom = useSel && Number.isFinite(Number(sel.bottom)) ? Number(sel.bottom) : Math.min(profitBottom, riskBottom);
    const shapes=[];
    if(useSel){
        shapes.push({
            type:'rect', xref:'x', yref:'y', x0:sel.x0, x1:sel.x1, y0:selBottom, y1:selTop, layer:'above',
            fillcolor:'rgba(118,150,210,0.14)', line:{color:'rgba(166,220,255,0.95)', width:1.6, dash:'dot'}
        });
    }
    shapes.push(
        {type:'rect', xref:'x', yref:'y', x0, x1, y0:profitBottom, y1:profitTop, layer:'below',
         fillcolor:isLong?'rgba(22,199,132,0.22)':'rgba(234,57,67,0.22)', line:{width:0}},
        {type:'rect', xref:'x', yref:'y', x0, x1, y0:riskBottom, y1:riskTop, layer:'below',
         fillcolor:isLong?'rgba(234,57,67,0.22)':'rgba(22,199,132,0.22)', line:{width:0}},
        {type:'line', xref:'x', yref:'y', x0, x1, y0:entry, y1:entry, line:{color:'#ffcc66',width:1.5}},
        {type:'line', xref:'x', yref:'y', x0, x1, y0:stop, y1:stop, line:{color:'#ff5b6e',width:1.2,dash:'dot'}},
        {type:'line', xref:'x', yref:'y', x0, x1, y0:target, y1:target, line:{color:'#1fda8a',width:1.2,dash:'dash'}}
    );
    if(Number.isFinite(Number(exit)) && Number(exit)>0){
        shapes.push({type:'line', xref:'x', yref:'y', x0, x1, y0:exit, y1:exit, line:{color:'#45a7ff',width:1.3,dash:'solid'}});
    }
    const annotations=[
        {xref:'paper', yref:'paper', x:0.01, y:0.98, showarrow:false, align:'left',
         text:`${isLong?'做多':'做空'}回测｜入场 ${formatPrice(entry)} ｜ 止损 ${formatPrice(stop)} ｜ 止盈 ${formatPrice(target)}${Number.isFinite(Number(exit))&&Number(exit)>0?` ｜ 出场 ${formatPrice(exit)}`:''} ｜ R/R ${rr.toFixed(2)}`,
         font:{size:12, color:'#dce7ff'}, bgcolor:'rgba(10,16,29,0.75)', bordercolor:'rgba(90,120,180,0.4)', borderwidth:1}
    ];
    return {traces:[], shapes, annotations};
}
function applyRectIntersectionBacktest(rect, silent=false){
    const normalized=normalizeRectByKlines(rect);
    if(!normalized){ if(!silent)showAlert('未识别到有效矩形区域，请重新框选','warning','historyAlertBox'); return false; }
    const side=document.getElementById('tradeSide').value;
    // 入场严格取矩形左边界对应K线的收盘价；出场严格取右边界对应K线的收盘价
    const entry=historyKlines[normalized.leftIdx].close;
    const exit=historyKlines[normalized.rightIdx].close;
    const stop=side==='long'?normalized.bottom:normalized.top;
    const target=side==='long'?normalized.top:normalized.bottom;
    document.getElementById('tradeEntryPrice').value=entry.toFixed(8);
    document.getElementById('tradeStopPrice').value=stop.toFixed(8);
    document.getElementById('tradeTargetPrice').value=target.toFixed(8);
    document.getElementById('tradeExitPrice').value=exit.toFixed(8);
    historyTradeBacktest = historyTradeBacktest || {};
    historyTradeBacktest.selectionRect = {
        x0:normalized.x0, x1:normalized.x1, top:normalized.top, bottom:normalized.bottom,
        leftIdx:normalized.leftIdx, rightIdx:normalized.rightIdx
    };
    applyHistoryTradeBacktest();
    if(!silent) showAlert('已按矩形左右边界与K线交点生成入场/出场，并完成回测','success','historyAlertBox');
    return true;
}
function resetHistoryChartZoom(){
    const chart=document.getElementById('historyChart');
    const zoomCheckbox=document.getElementById('zoomToSelection');
    if(zoomCheckbox) zoomCheckbox.checked=false;
    if(chart && chart.data){
        Plotly.relayout(chart,{
            'xaxis.autorange':true,
            'yaxis.autorange':true,
            'yaxis2.autorange':true
        });
    }
}
function extractRectFromRelayout(eventData, chart){
    if(!eventData) return null;
    if(Array.isArray(eventData.shapes) && eventData.shapes.length){
        for(let i=eventData.shapes.length-1;i>=0;i--){
            const s=eventData.shapes[i];
            if((s.type||'rect')==='rect' && Number.isFinite(Number(s.y0)) && Number.isFinite(Number(s.y1))){
                return s;
            }
        }
    }
    const temp={};
    Object.keys(eventData).forEach(k=>{
        const m=k.match(/^shapes\[(\d+)\]\.(x0|x1|y0|y1|type)$/);
        if(!m) return;
        const idx=parseInt(m[1],10);
        if(!temp[idx]) temp[idx]={};
        temp[idx][m[2]]=eventData[k];
    });
    const idxs=Object.keys(temp).map(n=>parseInt(n,10)).sort((a,b)=>b-a);
    for(const idx of idxs){
        const base=(chart&&chart.layout&&Array.isArray(chart.layout.shapes)&&chart.layout.shapes[idx])?chart.layout.shapes[idx]:{};
        const s=Object.assign({}, base, temp[idx]);
        if((s.type||'rect')==='rect' && Number.isFinite(Number(s.y0)) && Number.isFinite(Number(s.y1))){
            return s;
        }
    }
    return null;
}
function startDragAreaBacktest(){
    if(!historyKlines.length){ showAlert('请先加载历史数据并生成K线','warning','historyAlertBox'); return; }
    dragBacktestArmed=true;
    showAlert('已进入区域拖拽回测：矩形左边界交点=入场，右边界交点=出场','info','historyAlertBox');
    const chart=document.getElementById('historyChart');
    if(chart && chart.data){ Plotly.relayout(chart,{dragmode:'drawrect'}); }
}
function handleHistoryDragBacktestRelayout(eventData){
    const chart=document.getElementById('historyChart');
    if(dragBacktestArmed){
        const rect=extractRectFromRelayout(eventData, chart);
        if(!rect) return;
        dragBacktestArmed=false;
        if(chart && chart.data){ Plotly.relayout(chart,{dragmode:'pan'}); }
        applyRectIntersectionBacktest(rect, false);
        return;
    }
    if(!historyTradeBacktest || !chart || !chart.layout || !Array.isArray(chart.layout.shapes)) return;
    const changedShapeKeys=Object.keys(eventData||{}).filter(k=>/^shapes\[\d+\]\./.test(k));
    if(!changedShapeKeys.length) return;
    const changedIdxSet=new Set(changedShapeKeys.map(k=>parseInt((k.match(/^shapes\[(\d+)\]\./)||[])[1],10)).filter(Number.isFinite));
    const idxMap=getBacktestShapeIndexMap();
    if(idxMap.selectionRect>=0 && changedIdxSet.has(idxMap.selectionRect)){
        const rect=chart.layout.shapes[idxMap.selectionRect];
        if(rect) applyRectIntersectionBacktest(rect, true);
        return;
    }
    const entryShape=chart.layout.shapes[idxMap.entryLine];
    const stopShape=chart.layout.shapes[idxMap.stopLine];
    const targetShape=chart.layout.shapes[idxMap.targetLine];
    if(!entryShape || !stopShape || !targetShape) return;
    const entry=Number(entryShape.y0), stop=Number(stopShape.y0), target=Number(targetShape.y0);
    if(![entry,stop,target].every(v=>Number.isFinite(v))) return;
    document.getElementById('tradeEntryPrice').value=entry.toFixed(8);
    document.getElementById('tradeStopPrice').value=stop.toFixed(8);
    document.getElementById('tradeTargetPrice').value=target.toFixed(8);
    if(idxMap.exitLine>=0){
        const exitShape=chart.layout.shapes[idxMap.exitLine];
        if(exitShape && Number.isFinite(Number(exitShape.y0))){
            document.getElementById('tradeExitPrice').value=Number(exitShape.y0).toFixed(8);
        }
    }
    applyHistoryTradeBacktest();
}
function drawKlineChart(klines, cid, title) {
    const container=document.getElementById(cid);
    if(!klines||!klines.length){ container.innerHTML='<div class="loading"><div class="loading-spinner"></div><p>暂无数据</p></div>'; return; }
    const prices=klines.flatMap(k=>[k.open,k.high,k.low,k.close]);
    const avg=prices.reduce((a,b)=>a+b,0)/prices.length;
    let fmt=',.2f';
    if(avg<1000&&avg>=1) fmt='.4f'; else if(avg<1&&avg>=0.01) fmt='.6f';
    else if(avg<0.01&&avg>=0.0001) fmt='.8f'; else if(avg<0.0001) fmt='.10f';
    const xData=klines.map(k=>formatTime(k.time));
    const changeData=klines.map(k=>calcKlineChangePct(k));
    const amplitudeData=klines.map(k=>calcKlineAmplitudePct(k));
    const volumeData=klines.map(k=>k.volume||0);
    const volumeColorData=klines.map(k=>(k.close>=k.open?'rgba(22,199,132,0.58)':'rgba(234,57,67,0.58)'));
    const candleTrace={
        x:xData, open:klines.map(k=>k.open), high:klines.map(k=>k.high),
        low:klines.map(k=>k.low), close:klines.map(k=>k.close),
        customdata:changeData.map((v,i)=>[v, amplitudeData[i]]),
        hovertemplate:'时间: %{x}<br>开: %{open:'+fmt+'}<br>高: %{high:'+fmt+'}<br>低: %{low:'+fmt+'}<br>收: %{close:'+fmt+'}<br>涨跌幅: %{customdata[0]:+.2f}%<br>振幅: %{customdata[1]:.2f}%<extra></extra>',
        type:'candlestick',
        yaxis:'y',
        increasing:{line:{color:'#16c784',width:1},fillcolor:'#16c784'},
        decreasing:{line:{color:'#ea3943',width:1},fillcolor:'#ea3943'},
        whiskerwidth:.5
    };
    const volumeTrace={
        x:xData, y:volumeData, type:'bar', yaxis:'y2', hoverinfo:'skip', showlegend:false,
        marker:{color:volumeColorData}
    };
    const traces=[candleTrace, volumeTrace];
    const overlay=(cid==='historyChart')?getBacktestOverlay(klines):{traces:[],shapes:[],annotations:[]};
    traces.push(...overlay.traces);
    const zoomCfg={};
    if(cid==='historyChart'){
        const autoZoomEl=document.getElementById('zoomToSelection');
        const autoZoom=autoZoomEl ? autoZoomEl.checked : true;
        const sel=getCurrentSelectionRectByKlines();
        if(autoZoom && sel){
            const selectedBars=Math.max(1, sel.rightIdx-sel.leftIdx+1);
            const minBars=Math.min(klines.length, 120);
            const targetBars=Math.max(minBars, Math.ceil(selectedBars*1.8));
            const center=Math.floor((sel.leftIdx+sel.rightIdx)/2);
            let l=Math.max(0, center-Math.floor(targetBars/2));
            let r=Math.min(klines.length-1, l+targetBars-1);
            l=Math.max(0, r-targetBars+1);
            const selectedSlice=klines.slice(sel.leftIdx, sel.rightIdx+1);
            const highs=selectedSlice.map(k=>k.high);
            const lows=selectedSlice.map(k=>k.low);
            const yTop=Math.max(sel.top, ...highs);
            const yBottom=Math.min(sel.bottom, ...lows);
            const yPad=Math.max((yTop-yBottom)*0.30, Math.abs(yTop)*0.004 || 1e-8);
            zoomCfg.xaxisRange=[formatTime(klines[l].time), formatTime(klines[r].time)];
            zoomCfg.yaxisRange=[yBottom-yPad, yTop+yPad];
        }
    }
    if(container.data) Plotly.purge(container);
    container.innerHTML='';
    Plotly.newPlot(cid,traces,{
        title:{text:title||'K线图',font:{size:16,family:'Microsoft YaHei',color:'#dce7ff'}},
        xaxis:{
            title:'时间', rangeslider:{visible:false}, type:'category', tickangle:0,
            tickfont:{size:10,color:'#8fa2c6'}, gridcolor:'rgba(44,60,92,0.35)', zeroline:false,
            showline:false, showspikes:true, spikecolor:'#8fa2c6', spikesnap:'cursor'
        },
        yaxis:{
            domain:[0.22,1], title:'价格 (USDT)', tickformat:fmt, side:'right',
            tickfont:{color:'#9fb0d0'}, gridcolor:'rgba(44,60,92,0.35)', zeroline:false
        },
        yaxis2:{
            domain:[0,0.18], side:'right', showgrid:false, zeroline:false,
            tickfont:{color:'#6f84a8'}, title:'成交量'
        },
        plot_bgcolor:'#0b1220', paper_bgcolor:'#0b1220',
        font:{color:'#c8d5ee'},
        shapes:overlay.shapes,
        annotations:overlay.annotations,
        margin:{l:56,r:86,t:52,b:34}, hovermode:'x unified',
        dragmode:'pan',
        newshape:{line:{color:'#0f3460',width:2}}
    },{
        responsive:true, displayModeBar:true, displaylogo:false, editable:true,
        edits:{shapePosition:true},
        modeBarButtonsToAdd:['drawline','drawopenpath','drawrect','eraseshape'],
        modeBarButtonsToRemove:['lasso2d','select2d']
    }).then(()=>{
        if(zoomCfg.xaxisRange || zoomCfg.yaxisRange){
            const relayoutPayload={};
            if(zoomCfg.xaxisRange) relayoutPayload['xaxis.range']=zoomCfg.xaxisRange;
            if(zoomCfg.yaxisRange) relayoutPayload['yaxis.range']=zoomCfg.yaxisRange;
            Plotly.relayout(container, relayoutPayload);
        }
        if(cid==='historyChart'){
            if(typeof container.removeAllListeners==='function'){
                container.removeAllListeners('plotly_relayout');
            }
            container.on('plotly_relayout', handleHistoryDragBacktestRelayout);
        }
    }).catch(err=>{
        container.innerHTML=`<div class="loading" style="color:#c00">图表渲染失败: ${err.message}</div>`;
    });
}
async function updateData() {
    try {
        const res=await fetch('/api/data'); const r=await res.json();
        if(r.success&&r.data.length>0){
            const ms=parseInt(document.getElementById('klineInterval').value);
            const max=parseInt(document.getElementById('maxCandles').value);
            let klines=aggregateToKlines(r.data,ms);
            if(klines.length>max) klines=klines.slice(-max);
            drawKlineChart(klines,'chart');
            document.getElementById('dataCount').textContent=r.data.length.toLocaleString();
            document.getElementById('candleCount').textContent=klines.length;
            const lp=r.data[r.data.length-1].price;
            const el=document.getElementById('latestPrice'); el.textContent=formatPrice(lp);
            if(lastPrice!==null) el.className=lp>lastPrice?'status-value price-up':lp<lastPrice?'status-value price-down':'status-value';
            lastPrice=lp;
        }
    } catch(e){}
}
function toggleAutoRefresh(){
    const btn=document.getElementById('autoRefreshBtn');
    if(autoRefreshInterval){ clearInterval(autoRefreshInterval); autoRefreshInterval=null; btn.textContent='▶️ 自动刷新'; btn.style.background=''; }
    else{
        const ms=parseInt(document.getElementById('refreshInterval').value)*1000;
        autoRefreshInterval=setInterval(updateData,ms); btn.textContent='⏸️ 停止刷新';
        btn.style.background='linear-gradient(135deg,#f093fb,#f5576c)'; updateData();
    }
}
document.getElementById('klineInterval').addEventListener('change',updateData);
document.getElementById('maxCandles').addEventListener('change',updateData);


// ═══════════════ 资费率监控 ═══════════════
let selectedSymbolsSet = new Set();

function addSelectedSymbol(){
    let v=document.getElementById('addSymbolInput').value.trim().toUpperCase();
    if(!v) return;
    if(!v.endsWith('USDT')) v+='USDT';
    if(selectedSymbolsSet.has(v)){ showAlert(`${v} 已在列表中`,'warning','fundingAlertBox'); return; }
    selectedSymbolsSet.add(v);
    document.getElementById('addSymbolInput').value='';
    renderSymbolTags();
}
function removeSymbol(s){ selectedSymbolsSet.delete(s); renderSymbolTags(); }
function clearSelectedSymbols(){ selectedSymbolsSet.clear(); renderSymbolTags(); }
function renderSymbolTags(){
    const c=document.getElementById('selectedSymbolTags');
    c.innerHTML=[...selectedSymbolsSet].map(s=>
        `<div class="symbol-tag">${s}<span class="remove" onclick="removeSymbol('${s}')">✕</span></div>`
    ).join('');
}

async function startFundingMonitor(){
    const config = {
        topN:         parseInt(document.getElementById('topN').value),
        preMinutes:   parseFloat(document.getElementById('preMinutes').value),
        postMinutes:    parseFloat(document.getElementById('postMinutes').value),
        folder:         document.getElementById('fundingFolder').value,
        format:         document.getElementById('fundingFormat').value,
        minIntervalMs:  parseInt(document.getElementById('minIntervalMs').value),
        minVolumeUsd:   parseFloat(document.getElementById('minVolumeUsd').value) * 1e8,
        symbols:        [...selectedSymbolsSet]
    };
    try{
        const res=await fetch('/api/funding/start',{method:'POST',
            headers:{'Content-Type':'application/json'}, body:JSON.stringify(config)});
        const r=await res.json();
        if(r.success){
            document.getElementById('fundingStartBtn').disabled=true;
            document.getElementById('fundingStopBtn').disabled=false;
            document.getElementById('fd-status').textContent='运行中';
            document.getElementById('fd-status').className='fd-card-value status-running';
            showAlert('资费率监控已启动！将在结算窗口自动采集。','success','fundingAlertBox');
            document.getElementById('countdownBar').style.display='flex';
            startFundingPoll();
        } else showAlert(r.message,'error','fundingAlertBox');
    } catch(e){ showAlert(`启动失败: ${e.message}`,'error','fundingAlertBox'); }
}

async function stopFundingMonitor(){
    try{
        const res=await fetch('/api/funding/stop',{method:'POST'});
        const r=await res.json();
        if(r.success){
            document.getElementById('fundingStartBtn').disabled=false;
            document.getElementById('fundingStopBtn').disabled=true;
            document.getElementById('fd-status').textContent='已停止';
            document.getElementById('fd-status').className='fd-card-value status-stopped';
            showAlert('资费率监控已停止','info','fundingAlertBox');
        }
    } catch(e){}
}

async function refreshFundingRates(){
    showAlert('正在拉取资费率...','info','fundingAlertBox');
    try{
        const res=await fetch('/api/funding/rates');
        const r=await res.json();
        if(r.success){ renderFundingTable(r.data); showAlert(`已加载 ${r.data.length} 个币种资费率`,'success','fundingAlertBox'); }
        else showAlert(r.message,'error','fundingAlertBox');
    } catch(e){ showAlert(`失败: ${e.message}`,'error','fundingAlertBox'); }
}

// 判断某个币是否属于「本次最近结算窗口」
function getWindowTag(f, refTs){
    if(!refTs||!f.next_funding_ts) return '--';
    const diff = Math.abs(f.next_funding_ts - refTs);
    return diff <= 60000 ? '<span style="color:#16c784;font-weight:700">✅ 本次</span>' : '<span style="color:#aaa">下一轮</span>';
}
function renderFundingTable(data){
    const nextFundingRef = fundingStatusCache && fundingStatusCache.next_funding_time || 0;
    if(!data||!data.length){ document.getElementById('fundingTableArea').innerHTML='<div class="loading">暂无数据</div>'; return; }
    let html=`<table class="funding-table"><thead><tr>
        <th>#</th><th>交易对</th><th>资费率</th><th>绝对值</th><th>方向</th>
        <th>标记价格</th><th>24h成交额</th><th>下次结算</th><th>本次窗口</th><th>操作</th>
    </tr></thead><tbody>`;
    data.forEach((f,i)=>{
        const rateClass = f.rate<0?'rate-negative':'rate-positive';
        const badge = f.rate>0?`<span class="badge badge-long">多付空</span>`:`<span class="badge badge-short">空付多</span>`;
        html+=`<tr>
            <td style="font-weight:700;color:#888">${i+1}</td>
            <td style="font-weight:700;font-family:monospace">${f.symbol}</td>
            <td class="${rateClass}">${f.rate_pct}</td>
            <td style="font-weight:600">${(f.abs_rate*100).toFixed(4)}%</td>
            <td>${badge}</td>
            <td style="font-family:monospace">${f.mark_price>0?formatPrice(f.mark_price):'--'}</td>
            <td style="font-family:monospace;color:#666">${f.next_funding_time}</td>
            <td><button class="btn-sm btn-success" onclick="quickAddSymbol('${f.symbol}')">➕采集</button></td>
        </tr>`;
    });
    html+='</tbody></table>';
    document.getElementById('fundingTableArea').innerHTML=html;
}

function quickAddSymbol(sym){
    selectedSymbolsSet.add(sym);
    renderSymbolTags();
    showAlert(`已将 ${sym} 加入采集列表`,'success','fundingAlertBox');
}

// ─── 资费状态轮询 ───
function startFundingPoll(){
    if(fundingPollTimer) return;
    fundingPollTimer=setInterval(pollFundingStatus,3000);
    pollFundingStatus();
}
function stopFundingPoll(){ clearInterval(fundingPollTimer); fundingPollTimer=null; }

let fundingStatusCache = null;
async function pollFundingStatus(){
    try{
        const res=await fetch('/api/funding/status');
        const r=await res.json();
        if(!r.success) return;
        const s=r.status;
        fundingStatusCache = s;

        // 仪表盘
        document.getElementById('fd-status').textContent = s.running?'运行中':'已停止';
        document.getElementById('fd-status').className   = `fd-card-value ${s.running?'status-running':'status-stopped'}`;
        document.getElementById('fd-active').textContent = Object.keys(s.auto_collectors).length;
        document.getElementById('fd-lastfetch').textContent = s.last_fetch_time||'--';

        const phaseMap={'idle':'⏸ 待机','pre_collect':'⏰ 预采集','collecting':'🔴 采集中','post_collect':'📡 后置采集'};
        const phaseClsMap={'idle':'phase-idle','pre_collect':'phase-pre','collecting':'phase-collecting','post_collect':'phase-post'};
        const phase=s.auto_collect_phase||'idle';
        const phaseEl=document.getElementById('fd-phase');
        phaseEl.textContent=phaseMap[phase]||phase;
        phaseEl.className=`fd-card-value ${phaseClsMap[phase]||'phase-idle'}`;

        // 倒计时
        if(s.next_funding_time){
            const diff=s.next_funding_time - Date.now();
            const sec=Math.max(0,Math.floor(diff/1000));
            document.getElementById('countdownNum').textContent=secToHMS(sec);
            const ndt=new Date(s.next_funding_time);
            document.getElementById('nextFundingTs').textContent=
                `下次结算: ${ndt.toLocaleString('zh-CN')}`;
            const phaseLabel=document.getElementById('countdownPhase');
            const pre_ms=s.pre_minutes*60000, post_ms=s.post_minutes*60000;
            const pre_fetch_ms=(s.pre_minutes+1)*60000;
            if(diff>pre_fetch_ms){ phaseLabel.textContent='💤 待机中'; phaseLabel.className='phase-idle'; }
            else if(diff>pre_ms){ phaseLabel.textContent='⏳ 拉取名单中'; phaseLabel.className='phase-pre'; }
            else if(diff>0){ phaseLabel.textContent='⏰ 采集前段'; phaseLabel.className='phase-pre'; }
            else if(diff>-post_ms){ phaseLabel.textContent='🔴 采集中'; phaseLabel.className='phase-collecting'; }
            else{ phaseLabel.textContent='✅ 窗口结束'; phaseLabel.className='phase-idle'; }
        }

        // 资费排行
        if(s.top_symbols&&s.top_symbols.length){
            renderFundingTable(s.top_symbols);
        }

        // 活跃采集
        const ac=s.auto_collectors;
        if(Object.keys(ac).length>0){
            document.getElementById('activeCollectPanel').style.display='block';
            let html='<div style="display:flex;flex-wrap:wrap;gap:10px;">';
            for(const [sym,info] of Object.entries(ac)){
                const isPrimary = info.is_primary;
                const bg  = isPrimary ? '#e8f0ff' : '#e8f8f0';
                const bdr = isPrimary ? '#667eea' : '#27ae60';
                const tag = isPrimary
                    ? '<span style="background:#667eea;color:white;padding:1px 7px;border-radius:10px;font-size:10px;margin-left:5px">实时Tab</span>'
                    : '<span style="background:#27ae60;color:white;padding:1px 7px;border-radius:10px;font-size:10px;margin-left:5px">独立文件</span>';
                html+=`<div style="background:${bg};border:2px solid ${bdr};border-radius:8px;padding:10px 14px;min-width:220px">
                    <div style="font-weight:700;color:${bdr};font-size:14px">🔴 ${sym}${tag}</div>
                    <div style="font-size:11px;color:#555;margin-top:4px">开始: ${info.started.substring(11,19)} | 间隔: ${s.min_interval_ms===0?'全量逐笔':s.min_interval_ms+'ms'}</div>
                    <div style="font-size:11px;color:#555;word-break:break-all">文件: ${info.file.split('/').pop()}</div>
                </div>`;

                // 若是主采集器，同步更新实时Tab状态栏
                if(isPrimary){
                    document.getElementById('collectionStatus').textContent='运行中';
                    document.getElementById('collectionStatus').className='status-value status-running';
                    document.getElementById('currentExchange').textContent='BINANCE';
                    document.getElementById('currentSymbol').textContent=sym;
                }
            }
            html+='</div>';
            document.getElementById('activeCollectInfo').innerHTML=html;

            // 如果当前在实时Tab，触发一次数据刷新
            if(document.getElementById('tab-live').classList.contains('active') && !autoRefreshInterval){
                updateData();
            }
        } else {
            document.getElementById('activeCollectPanel').style.display='none';
            // 资费监控停完了，同步重置实时Tab状态
            if(!document.getElementById('startBtn').disabled){
                document.getElementById('collectionStatus').textContent='已停止';
                document.getElementById('collectionStatus').className='status-value status-stopped';
            }
        }

        // 日志
        if(s.collect_log&&s.collect_log.length){
            const lb=document.getElementById('collectLog');
            lb.innerHTML=s.collect_log.slice(-60).join('\n');
            lb.scrollTop=lb.scrollHeight;
        }
    } catch(e){}
}


// ═══════════════ 历史文件浏览器 ═══════════════
function updateHistorySelectionCounter(){
    const checks=[...document.querySelectorAll('.history-file-checkbox')];
    const checked=checks.filter(c=>c.checked);
    selectedHistoryFileIndexes=new Set(checked.map(c=>parseInt(c.value,10)));
    const countEl=document.getElementById('historySelectedCount');
    if(countEl) countEl.textContent=`已选择 ${selectedHistoryFileIndexes.size} 个`;
    const all=document.getElementById('historySelectAll');
    if(all) all.checked=checks.length>0&&checked.length===checks.length;
}
function syncHistoryRangeModeButton(){
    const btn=document.getElementById('historyRangeModeBtn');
    if(!btn) return;
    if(historyRangeSelectMode){
        btn.textContent='🔗 连选模式：开';
        btn.style.background='#16a085';
        btn.style.color='#fff';
    }else{
        btn.textContent='🔗 连选模式：关';
        btn.style.background='';
        btn.style.color='';
    }
}
function toggleHistoryRangeSelectMode(){
    historyRangeSelectMode=!historyRangeSelectMode;
    historyRangeAnchorIndex=null;
    syncHistoryRangeModeButton();
}
function toggleHistorySelectAll(checked){
    document.querySelectorAll('.history-file-checkbox').forEach(c=>{c.checked=checked;});
    historyRangeAnchorIndex=null;
    updateHistorySelectionCounter();
}
function toggleHistoryFileSelection(i, checked){
    const checks=[...document.querySelectorAll('.history-file-checkbox')];
    const pos=new Map(checks.map((c,idx)=>[parseInt(c.value,10),idx]));
    if(
        historyRangeSelectMode &&
        historyRangeAnchorIndex!==null &&
        pos.has(historyRangeAnchorIndex) &&
        pos.has(i)
    ){
        const from=Math.min(pos.get(historyRangeAnchorIndex),pos.get(i));
        const to=Math.max(pos.get(historyRangeAnchorIndex),pos.get(i));
        for(let p=from;p<=to;p++) checks[p].checked=checked;
    }
    historyRangeAnchorIndex=i;
    updateHistorySelectionCounter();
}
function getSelectedHistoryPaths(){
    return [...selectedHistoryFileIndexes]
        .map(i=>fileRegistry[i]?.path)
        .filter(Boolean);
}
async function downloadSelectedHistoryFiles(){
    const paths=getSelectedHistoryPaths();
    if(!paths.length){ showAlert('请先选择要下载的文件','warning','historyAlertBox'); return; }
    const btn=document.getElementById('downloadBatchBtn');
    if(btn){ btn.disabled=true; btn.textContent='⏳ 打包中...'; }
    try{
        const res=await fetch('/api/download_files_batch',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({paths})
        });
        if(!res.ok){
            let msg=await res.text();
            try{
                const parsed=JSON.parse(msg);
                if(parsed&&parsed.message) msg=parsed.message;
            }catch(_){}
            throw new Error(msg||'下载失败');
        }
        const blob=await res.blob();
        let filename=`history_files_${new Date().toISOString().replace(/[-:.TZ]/g,'').slice(0,14)}.zip`;
        const cd=res.headers.get('content-disposition')||'';
        const mt=cd.match(/filename\*=UTF-8''([^;]+)|filename="?([^\";]+)"?/i);
        if(mt) filename=decodeURIComponent(mt[1]||mt[2]);
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');
        a.href=url; a.download=filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showAlert(`已打包下载 ${paths.length} 个文件（ZIP）`,'success','historyAlertBox');
    }catch(e){
        showAlert(`批量下载失败: ${e.message}`,'error','historyAlertBox');
    }finally{
        if(btn){ btn.disabled=false; btn.textContent='📦 批量下载(打包)'; }
    }
}
async function loadFileList(){
    const folder=document.getElementById('historyFolder').value.trim();
    if(!folder){showAlert('请输入文件夹路径','warning','historyAlertBox');return;}
    document.getElementById('fileListArea').innerHTML='<div class="loading"><div class="loading-spinner"></div><p>扫描文件...</p></div>';
    fileRegistry={};
    selectedHistoryFileIndexes.clear();
    historyRangeSelectMode=false;
    historyRangeAnchorIndex=null;
    try{
        const res=await fetch(`/api/files?folder=${encodeURIComponent(folder)}`);
        const r=await res.json();
        if(!r.success){
            document.getElementById('fileListArea').innerHTML=`<div class="loading" style="color:#c00">${r.message}</div>`;
            return;
        }
        if(!r.files.length){
            document.getElementById('fileListArea').innerHTML='<div class="loading">没有找到CSV/JSON文件</div>'; return;
        }
        r.files.forEach(f=>fileRegistry[f.index]={path:f.path,name:f.name});
        let html=`<div class="file-actions">
            <div class="left">
                <button class="btn-sm" onclick="toggleHistorySelectAll(true)">✅ 全选</button>
                <button class="btn-sm" onclick="toggleHistorySelectAll(false)">↩ 取消全选</button>
                <button class="btn-sm" id="historyRangeModeBtn" onclick="toggleHistoryRangeSelectMode()">🔗 连选模式：关</button>
                <span class="file-select-count" id="historySelectedCount">已选择 0 个</span>
            </div>
            <div class="right">
                <button class="btn-info btn-sm" id="downloadBatchBtn" onclick="downloadSelectedHistoryFiles()">📦 批量下载(打包)</button>
            </div>
        </div>
        <div class="file-list-scroll"><table class="file-table"><thead><tr>
            <th class="file-check-col"><input type="checkbox" id="historySelectAll" onchange="toggleHistorySelectAll(this.checked)"></th>
            <th>文件名</th><th>格式</th><th>大小</th><th>修改时间</th><th>操作</th>
        </tr></thead><tbody>`;
        r.files.forEach(f=>{
            const badge=f.format==='csv'?
                `<span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">CSV</span>`:
                `<span style="background:#d1ecf1;color:#0c5460;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">JSON</span>`;
            html+=`<tr id="frow-${f.index}">
                <td class="file-check-col"><input class="history-file-checkbox" type="checkbox" value="${f.index}" onchange="toggleHistoryFileSelection(${f.index}, this.checked)"></td>
                <td style="font-family:monospace;font-size:12px">${f.name}</td>
                <td>${badge}</td><td>${f.size}</td><td>${f.modified}</td>
                <td>
                    <button class="btn-success btn-sm" onclick="loadHistoryFile(${f.index})">📊 查看</button>
                    <button class="btn-info btn-sm" onclick="downloadFileByIndex(${f.index})" style="margin-left:5px">⬇ 下载</button>
                </td>
            </tr>`;
        });
        html+='</tbody></table></div>';
        document.getElementById('fileListArea').innerHTML=html;
        syncHistoryRangeModeButton();
        updateHistorySelectionCounter();
        showAlert(`找到 ${r.files.length} 个文件`,'success','historyAlertBox');
    } catch(e){ showAlert(`失败: ${e.message}`,'error','historyAlertBox'); }
}
function downloadFileByIndex(i){ const e=fileRegistry[i]; if(e) window.location.href=`/api/download_file?path=${encodeURIComponent(e.path)}`; }
async function loadHistoryFile(i){
    const e=fileRegistry[i]; if(!e){showAlert('文件信息丢失','error','historyAlertBox');return;}
    document.querySelectorAll('.file-table tr').forEach(r=>r.classList.remove('selected'));
    const row=document.getElementById(`frow-${i}`); if(row)row.classList.add('selected');
    selectedFilePath=e.path;
    clearHistoryTradeBacktest();
    document.getElementById('historyChartControls').style.display='block';
    document.getElementById('historyChart').style.display='block';
    document.getElementById('historyStatus').style.display='flex';
    document.getElementById('historyChart').innerHTML='<div class="loading"><div class="loading-spinner"></div><p>加载数据...</p></div>';
    document.getElementById('historyStatus').innerHTML='<span>⏳ 加载中...</span>';
    try{
        const res=await fetch(`/api/load_file?path=${encodeURIComponent(e.path)}`);
        const r=await res.json();
        if(!r.success){showAlert(r.message,'error','historyAlertBox');return;}
        historyData=r.data;
        showAlert(`已加载 ${historyData.length.toLocaleString()} 条数据`,'success','historyAlertBox');
        renderHistoryChart();
    } catch(err){ showAlert(`失败: ${err.message}`,'error','historyAlertBox'); }
}
function renderHistoryChart(){
    if(!historyData.length){showAlert('没有数据','warning','historyAlertBox');return;}
    const ms=parseInt(document.getElementById('historyKlineInterval').value);
    const max=parseInt(document.getElementById('historyMaxCandles').value);
    let klines=aggregateToKlines(historyData,ms);
    const total=klines.length;
    if(klines.length>max) klines=klines.slice(-max);
    historyKlines=klines;
    const p=historyData.map(d=>d.price);
    const latest=klines[klines.length-1];
    const latestChangePct=calcKlineChangePct(latest);
    const latestAmplitudePct=calcKlineAmplitudePct(latest);
    document.getElementById('historyStatus').innerHTML=`
        <span>📊 <strong>总Tick:</strong> ${historyData.length.toLocaleString()}</span>
        <span>🕯️ <strong>K线:</strong> ${total}（显示${klines.length}根）</span>
        <span>📉 <strong>最低:</strong> ${formatPrice(Math.min(...p))}</span>
        <span>📈 <strong>最高:</strong> ${formatPrice(Math.max(...p))}</span>
        <span>🧮 <strong>最新涨跌幅:</strong> ${latestChangePct.toFixed(2)}%</span>
        <span>〰️ <strong>最新振幅:</strong> ${latestAmplitudePct.toFixed(2)}%</span>
    `;
    setHistoryTradeInputDefaults();
    drawKlineChart(klines,'historyChart',`历史K线 | ${selectedFilePath.split(/[\\/]/).pop()} | ${ms}ms`);
}
function setHistoryTradeInputDefaults(){
    if(!historyKlines.length) return;
    const side=document.getElementById('tradeSide').value;
    const last=historyKlines[historyKlines.length-1];
    const entryEl=document.getElementById('tradeEntryPrice');
    const stopEl=document.getElementById('tradeStopPrice');
    const targetEl=document.getElementById('tradeTargetPrice');
    const exitEl=document.getElementById('tradeExitPrice');
    const defaultEntry=last.close;
    if(!Number.isFinite(parseFloat(entryEl.value))||parseFloat(entryEl.value)<=0){
        entryEl.value=defaultEntry.toFixed(8);
    }
    const entry=parseFloat(entryEl.value)||defaultEntry;
    const offset=entry*0.01;
    if(!Number.isFinite(parseFloat(stopEl.value))||parseFloat(stopEl.value)<=0){
        stopEl.value=(side==='long'?entry-offset:entry+offset).toFixed(8);
    }
    if(!Number.isFinite(parseFloat(targetEl.value))||parseFloat(targetEl.value)<=0){
        targetEl.value=(side==='long'?entry+offset*1.5:entry-offset*1.5).toFixed(8);
    }
    if(!Number.isFinite(parseFloat(exitEl.value))||parseFloat(exitEl.value)<=0){
        exitEl.value=entry.toFixed(8);
    }
}
function applyHistoryTradeBacktest(){
    if(!historyKlines.length){ showAlert('请先加载历史文件并生成K线','warning','historyAlertBox'); return; }
    const side=document.getElementById('tradeSide').value;
    const entry=parseFloat(document.getElementById('tradeEntryPrice').value);
    const stop=parseFloat(document.getElementById('tradeStopPrice').value);
    const target=parseFloat(document.getElementById('tradeTargetPrice').value);
    const exit=parseFloat(document.getElementById('tradeExitPrice').value);
    const hasExit=Number.isFinite(exit)&&exit>0;
    const positionUsdt=Math.max(parseFloat(document.getElementById('tradePositionSize').value)||0,1);
    if(![entry,stop,target].every(v=>Number.isFinite(v)&&v>0)){
        showAlert('请填写有效的入场/止损/止盈价格','warning','historyAlertBox'); return;
    }
    const isLong=side==='long';
    const riskPerUnit=isLong?(entry-stop):(stop-entry);
    const rewardPerUnit=isLong?(target-entry):(entry-target);
    if(riskPerUnit<=0||rewardPerUnit<=0){
        showAlert('参数不合法：做多需 止损<入场<止盈，做空需 止盈<入场<止损','warning','historyAlertBox'); return;
    }
    const riskPct=Math.abs((riskPerUnit/entry)*100);
    const rewardPct=Math.abs((rewardPerUnit/entry)*100);
    const riskAmt=(riskPct/100)*positionUsdt;
    const rewardAmt=(rewardPct/100)*positionUsdt;
    const rr=rewardAmt/riskAmt;
    const funding=calcFundingAdjustment(side, positionUsdt);
    const prevRect=historyTradeBacktest && historyTradeBacktest.selectionRect ? historyTradeBacktest.selectionRect : null;
    historyTradeBacktest={side,entry,stop,target,exit:hasExit?exit:null,selectionRect:prevRect,funding};
    const ms=parseInt(document.getElementById('historyKlineInterval').value);
    drawKlineChart(historyKlines,'historyChart',`历史K线 | ${selectedFilePath.split(/[\\/]/).pop()} | ${ms}ms`);
    let fundingText='';
    if(funding.enabled){
        const directionText=funding.rate>=0?'多付空':'空付多';
        const actionText=funding.pnl>=0?'收入':'支出';
        const absAmt=Math.abs(funding.pnl);
        const settleTimeValue=(document.getElementById('fundingSettleTime').value||'').trim();
        let settleInfo=`结算次数: ${funding.count}`;
        if(settleTimeValue){
            settleInfo = `${settleInfo} ｜ 结算时间: ${settleTimeValue.replace('T',' ')}`;
            if(funding.timeUsed){
                settleInfo += funding.timeHit?'（在持仓区间内）':'（不在持仓区间内）';
            }
        }
        fundingText=`<br>资金费率: ${(funding.rate*100).toFixed(4)}%（${directionText}）｜ ${settleInfo} ｜ 资金费${actionText}: ${absAmt.toFixed(6)} USDT`;
    }
    let realizedText='';
    if(hasExit){
        const realizedPct=side==='long'?((exit-entry)/entry*100):((entry-exit)/entry*100);
        const realizedAmt=(realizedPct/100)*positionUsdt;
        const realizedNet=realizedAmt + (funding.enabled?funding.pnl:0);
        realizedText=`<br>出场 ${formatPrice(exit)} ｜ 实际收益: ${realizedAmt.toFixed(6)} USDT (${realizedPct.toFixed(2)}%)`;
        if(funding.enabled){
            realizedText += ` ｜ 含资金费净收益: ${realizedNet.toFixed(6)} USDT`;
        }
    }
    document.getElementById('tradeBacktestResult').innerHTML=`
        <strong>${side==='long'?'做多':'做空'}回测</strong>｜
        入场 ${formatPrice(entry)} ｜ 止损 ${formatPrice(stop)} ｜ 止盈 ${formatPrice(target)} ｜ 仓位金额 ${positionUsdt.toFixed(2)} USDT<br>
        预估风险: ${riskAmt.toFixed(6)} USDT (${riskPct.toFixed(2)}%) ｜ 预估收益: ${rewardAmt.toFixed(6)} USDT (${rewardPct.toFixed(2)}%) ｜ 盈亏比: 1 : ${rr.toFixed(2)}
        ${fundingText}
        ${realizedText}
    `;
}
function clearHistoryTradeBacktest(){
    historyTradeBacktest=null;
    dragBacktestArmed=false;
    document.getElementById('tradeExitPrice').value='';
    document.getElementById('tradeBacktestResult').innerHTML='';
    if(historyKlines.length){
        const ms=parseInt(document.getElementById('historyKlineInterval').value);
        drawKlineChart(historyKlines,'historyChart',`历史K线 | ${selectedFilePath.split(/[\\/]/).pop()} | ${ms}ms`);
    }
}
document.getElementById('historyKlineInterval').addEventListener('change',()=>{if(historyData.length)renderHistoryChart();});
document.getElementById('historyMaxCandles').addEventListener('change',()=>{if(historyData.length)renderHistoryChart();});
document.getElementById('tradeSide').addEventListener('change',()=>{setHistoryTradeInputDefaults();});
['fundingRatePct','fundingSettleTime','fundingSettleCount','tradePositionSize','tradeExitPrice','tradeEntryPrice','tradeStopPrice','tradeTargetPrice']
    .forEach(id=>{
        const el=document.getElementById(id);
        if(!el) return;
        el.addEventListener('change',()=>{ if(historyKlines.length && historyTradeBacktest) applyHistoryTradeBacktest(); });
    });

window.addEventListener('load',()=>{
    toggleFundingInputs();
    showAlert('欢迎！资费率自动采集功能已就绪。','info');
});
</script>
</body>
</html>
'''


# ─────────────────────────── API 路由 ───────────────────────────
