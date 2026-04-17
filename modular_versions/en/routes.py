"""
API routes module (English version).
This file keeps route responsibilities separate from runtime classes and state.
"""

import csv
import io
import json
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from flask import jsonify, render_template_string, request, send_file

import runtime
from template import HTML_TEMPLATE

@runtime.app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@runtime.app.route('/api/start', methods=['POST'])
def start_collection():
    try:
        data        = request.json
        exchange    = data.get('exchange', 'binance')
        symbol      = data.get('symbol', 'BTCUSDT')
        filename    = data.get('filename', 'price_data')
        save_folder = data.get('saveFolder', 'data')
        format_type = data.get('format', 'csv')
        success = runtime._start_main_collector(exchange, symbol, save_folder, filename, format_type)
        if success:
            return jsonify({'success': True, 'message': 'Capture started'})
        return jsonify({'success': False, 'message': 'Collector start failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/stop', methods=['POST'])
def stop_collection():
    try:
        runtime._stop_main_collector()
        return jsonify({'success': True, 'message': 'Capture stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/data')
def get_data():
    return jsonify({'success': True, 'data': runtime.price_data, 'config': runtime.current_config})


@runtime.app.route('/api/download')
def download_data():
    format_type = request.args.get('format', 'csv')
    filename    = request.args.get('filename', 'price_data')
    if not runtime.price_data:
        return jsonify({'success': False, 'message': 'No data available'})
    try:
        if format_type == 'csv':
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(['时间戳','价格','数量','日期时间'])
            for r in runtime.price_data:
                w.writerow([r['timestamp'],r['price'],r['quantity'],r['datetime']])
            out.seek(0)
            return send_file(io.BytesIO(out.getvalue().encode('utf-8-sig')),
                             mimetype='text/csv', as_attachment=True,
                             download_name=f'{filename}.csv')
        else:
            data = {'exchange':runtime.current_config['exchange'],'symbol':runtime.current_config['symbol'],
                    'total_records':len(runtime.price_data),'last_update':datetime.now().isoformat(),
                    'prices':runtime.price_data}
            return send_file(io.BytesIO(json.dumps(data,ensure_ascii=False,indent=2).encode()),
                             mimetype='application/json', as_attachment=True,
                             download_name=f'{filename}.json')
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/clear', methods=['POST'])
def clear_data():
    runtime.price_data = []
    return jsonify({'success': True})


# ── 资费率 API ────────────────────────────────────────────────

@runtime.app.route('/api/funding/start', methods=['POST'])
def funding_start():
    try:
        cfg = request.json or {}
        runtime.funding_status['top_n']          = int(cfg.get('topN', 5))
        runtime.funding_status['pre_minutes']    = float(cfg.get('preMinutes', 10))
        runtime.funding_status['post_minutes']   = float(cfg.get('postMinutes', 10))
        runtime.funding_status['collect_folder'] = cfg.get('folder', 'data/funding')
        runtime.funding_status['collect_format'] = cfg.get('format', 'csv')
        runtime.funding_status['selected_symbols'] = cfg.get('symbols', [])
        runtime.funding_status['min_interval_ms']  = int(cfg.get('minIntervalMs', 0))
        runtime.funding_status['min_volume_usd']   = float(cfg.get('minVolumeUsd', 30_000_000))

        if runtime.funding_monitor and runtime.funding_monitor.running:
            runtime.funding_monitor.stop()

        runtime.funding_monitor = runtime.FundingMonitor()
        runtime.funding_monitor.start()
        return jsonify({'success': True, 'message': 'Funding monitor started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/funding/stop', methods=['POST'])
def funding_stop():
    try:
        if runtime.funding_monitor:
            runtime.funding_monitor.stop()
            runtime.funding_monitor = None
        runtime.funding_status['running'] = False
        return jsonify({'success': True, 'message': 'Monitor stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/funding/status')
def funding_get_status():
    """返回完整资费监控状态"""
    status_copy = dict(runtime.funding_status)
    status_copy['pre_minutes']    = runtime.funding_status['pre_minutes']
    status_copy['post_minutes']   = runtime.funding_status['post_minutes']
    status_copy['min_interval_ms'] = runtime.funding_status.get('min_interval_ms', 0)
    return jsonify({'success': True, 'status': status_copy})


@runtime.app.route('/api/funding/rates')
def funding_get_rates():
    """按需手动拉取资费率（含24h成交额过滤），无需 aiohttp"""
    try:
        min_vol = runtime.funding_status.get('min_volume_usd', 30_000_000)

        def _get(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode('utf-8'))

        funding_raw = _get(runtime.FundingMonitor.FUNDING_API)
        ticker_raw  = _get(runtime.FundingMonitor.TICKER_API)

        vol_map = {t['symbol']: float(t.get('quoteVolume', 0)) for t in ticker_raw
                   if 'symbol' in t and 'quoteVolume' in t}

        result = []
        for item in funding_raw:
            symbol = item.get('symbol', '')
            if not symbol.endswith('USDT'):
                continue
            try:
                rate       = float(item.get('lastFundingRate', 0))
                next_ts    = int(item.get('nextFundingTime', 0))
                mark_price = float(item.get('markPrice', 0))
                volume_24h = vol_map.get(symbol, 0)
                if volume_24h < min_vol:
                    continue
                result.append({
                    'symbol':            symbol,
                    'rate':              rate,
                    'abs_rate':          abs(rate),
                    'rate_pct':          f"{rate*100:.4f}%",
                    'next_funding_ts':   next_ts,
                    'next_funding_time': datetime.fromtimestamp(next_ts/1000).strftime('%H:%M:%S') if next_ts else '--',
                    'mark_price':        mark_price,
                    'volume_24h':        volume_24h,
                    'volume_str':        f"{volume_24h/1e8:.2f}亿U" if volume_24h >= 1e8 else f"{volume_24h/1e6:.1f}百万U",
                    'direction':         'Longs pay shorts' if rate > 0 else 'Shorts pay longs'
                })
            except (ValueError, TypeError):
                continue

        result.sort(key=lambda x: x['abs_rate'], reverse=True)
        top_n = max(runtime.funding_status.get('top_n', 20), 30)
        return jsonify({'success': True, 'data': result[:top_n],
                        'filtered_total': len(result), 'min_vol_usd': min_vol})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ── 历史文件 API ────────────────────────────────────────────────

@runtime.app.route('/api/files')
def list_files():
    folder = request.args.get('folder', 'data')
    try:
        p = Path(folder)
        if not p.exists():
            return jsonify({'success': False, 'message': f'Folder does not exist: {folder}'})
        if not p.is_dir():
            return jsonify({'success': False, 'message': f'Path is not a folder: {folder}'})
        files = []
        for i, fp in enumerate(sorted(p.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)):
            if fp.suffix.lower() in ('.csv', '.json') and fp.is_file():
                stat = fp.stat()
                kb = stat.st_size / 1024
                files.append({
                    'index': i, 'name': fp.name,
                    'path': str(fp.resolve()).replace('\\', '/'),
                    'format': fp.suffix.lower().lstrip('.'),
                    'size': f"{kb:.1f} KB" if kb < 1024 else f"{kb/1024:.2f} MB",
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/load_file')
def load_file():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'success': False, 'message': 'File path is required'})
    fp = Path(path)
    if not fp.exists():
        return jsonify({'success': False, 'message': f'File does not exist: {path}'})
    try:
        records = []
        if fp.suffix.lower() == '.csv':
            with open(fp, 'r', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    try:
                        records.append({
                            'timestamp': int(row.get('时间戳') or row.get('timestamp', 0)),
                            'price':     float(row.get('价格') or row.get('price', 0)),
                            'quantity':  float(row.get('数量') or row.get('quantity', 0)),
                            'datetime':  row.get('日期时间') or row.get('datetime', '')
                        })
                    except: continue
        elif fp.suffix.lower() == '.json':
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            raw = data if isinstance(data, list) else data.get('prices', [])
            for row in raw:
                try:
                    records.append({
                        'timestamp': int(row.get('timestamp', 0)),
                        'price':     float(row.get('price', 0)),
                        'quantity':  float(row.get('quantity', 0)),
                        'datetime':  row.get('datetime', '')
                    })
                except: continue
        records = [r for r in records if r['timestamp'] > 0 and r['price'] > 0]
        records.sort(key=lambda x: x['timestamp'])
        return jsonify({'success': True, 'data': records, 'total': len(records)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Read failed: {str(e)}'})


@runtime.app.route('/api/download_file')
def download_file():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'success': False, 'message': 'Path is required'})
    fp = Path(path)
    if not fp.exists():
        return jsonify({'success': False, 'message': 'File does not exist'})
    try:
        return send_file(str(fp.resolve()), as_attachment=True, download_name=fp.name)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@runtime.app.route('/api/download_files_batch', methods=['POST'])
def download_files_batch():
    data = request.json or {}
    paths = data.get('paths', [])
    if not isinstance(paths, list) or not paths:
        return jsonify({'success': False, 'message': 'No files selected'}), 400

    valid_files = []
    seen = set()
    for raw_path in paths[:500]:
        fp = Path(str(raw_path))
        try:
            rp = fp.resolve()
        except Exception:
            continue
        key = str(rp).lower()
        if key in seen:
            continue
        if rp.exists() and rp.is_file() and rp.suffix.lower() in ('.csv', '.json'):
            seen.add(key)
            valid_files.append(rp)

    if not valid_files:
        return jsonify({'success': False, 'message': 'No valid files to download'}), 400

    try:
        zip_buffer = io.BytesIO()
        name_counter = {}
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for fp in valid_files:
                base_name = fp.name
                count = name_counter.get(base_name, 0)
                name_counter[base_name] = count + 1
                arcname = base_name if count == 0 else f"{fp.stem}_{count}{fp.suffix}"
                zf.write(str(fp), arcname=arcname)
        zip_buffer.seek(0)
        zip_name = f"history_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=zip_name)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Zip packaging failed: {str(e)}'}), 500
