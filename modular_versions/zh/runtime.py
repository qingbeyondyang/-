"""
加密货币毫秒级K线图系统 - 统一Web服务器
新增功能：资费率自动监控 + 资费结算窗口自动采集
- 每小时/每8小时自动拉取资费率最高币种
- 结算前10分钟自动开始采集，结算后10分钟自动停止
- 支持自定义采集频率（毫秒级）
- 支持多个高资费币种同时监控
"""

from flask import Flask, jsonify, render_template_string, request, send_file
from flask_cors import CORS
import json
import csv
import asyncio
import websockets
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import threading
import io
import os
import time
import zipfile

app = Flask(__name__)
CORS(app)

# ─────────────────── 全局变量 ───────────────────
data_collector = None
price_data = []
max_memory_records = 5000
write_batch_size = 100
current_config = {
    'exchange': 'binance',
    'symbol': 'BTCUSDT',
    'filename': 'price_data',
    'format': 'csv',
    #'save_folder': 'data', #相对路径
    'save_folder': '/opt/trading/app/data/basic', #绝对路径
    'running': False
}

# 资费率监控相关
funding_monitor = None
funding_status = {
    'running': False,
    'top_symbols': [],           # 当前资费率TOP列表
    'last_fetch_time': None,
    'next_funding_time': None,   # 下次结算时间戳(ms)
    'auto_collect_symbol': None, # 当前自动采集的币种
    'auto_collect_phase': 'idle',# idle / pre_collect / collecting / post_collect
    'auto_collectors': {},       # {symbol: DataCollector}
    'collect_log': [],           # 采集日志
    'top_n': 5,                  # 显示前N个高资费币种
    'pre_minutes': 10,           # 结算前N分钟开始采集
    'post_minutes': 10,          # 结算后N分钟停止采集
    'min_interval_ms': 0,        # 最小采集间隔(ms)，0=不节流(全量逐笔)
    'collect_format': 'csv',
    #'collect_folder': 'data/funding', #相对路径
    'collect_folder': '/opt/trading/app/data/funding', #绝对路径
    'selected_symbols': [],      # 用户选择要采集的币种(空=自动用TOPN)
    'min_volume_usd': 30_000_000,  # 24h成交额最小门槛(U)，过滤极低流动性小币
}


def format_price(price):
    if price >= 1000:   return f"{price:.2f}"
    elif price >= 1:    return f"{price:.4f}"
    elif price >= 0.01: return f"{price:.6f}"
    elif price >= 0.0001: return f"{price:.8f}"
    else:               return f"{price:.10f}"

def format_funding_rate(rate):
    """资费率格式化为百分比，保留4位小数"""
    return f"{rate * 100:.4f}%"

def get_earliest_next_funding(symbols_data):
    """
    从已拉取的资费率数据中，找出最近的一次结算时间戳(ms)。
    各币种结算周期不同(1h/4h/8h)，直接用API返回的 nextFundingTime。
    """
    if not symbols_data:
        return None
    valid = [s['next_funding_ts'] for s in symbols_data if s.get('next_funding_ts', 0) > 0]
    return min(valid) if valid else None


# ═══════════════════════════════════════════
# DataCollector  (与原版相同，稍作扩展)
# ═══════════════════════════════════════════

class DataCollector:
    def __init__(self, exchange, symbol, save_folder, filename, format_type,
                 on_tick=None, tag=''):
        self.exchange    = exchange.lower()
        self.symbol      = symbol.upper()
        self.running     = False
        self.ws          = None
        self.loop        = None
        self.thread      = None
        self.on_tick     = on_tick   # 额外回调(用于资费窗口数据写入)
        self.tag         = tag       # 用于日志标识

        self.save_folder = save_folder
        self.filename    = filename
        self.format_type = format_type
        self.write_buffer = []
        self.total_written = 0
        self.current_file_path = None
        self.local_data  = []        # 本采集器的本地数据(不写全局)
        self.min_interval_ms = 0     # 最小采集间隔，0=全量
        self._last_saved_ts  = -1    # 上次实际保存的时间戳

        Path(self.save_folder).mkdir(parents=True, exist_ok=True)
        self._init_file()

    def _init_file(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fn = f"{self.filename}_{self.exchange}_{self.symbol}_{timestamp}"
        if self.format_type == 'csv':
            self.current_file_path = Path(self.save_folder) / f"{fn}.csv"
            with open(self.current_file_path, 'w', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow(['时间戳', '价格', '数量', '日期时间'])
        else:
            self.current_file_path = Path(self.save_folder) / f"{fn}.json"
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                json.dump({'exchange':self.exchange,'symbol':self.symbol,
                           'start_time':datetime.now().isoformat(),'prices':[]}, f,
                          ensure_ascii=False, indent=2)
        print(f"📁 [{self.tag or self.symbol}] 数据文件: {self.current_file_path}")

    def _write_to_file(self, records):
        if not records: return
        try:
            if self.format_type == 'csv':
                with open(self.current_file_path, 'a', encoding='utf-8-sig', newline='') as f:
                    w = csv.writer(f)
                    for r in records:
                        w.writerow([r['timestamp'],r['price'],r['quantity'],r['datetime']])
            else:
                with open(self.current_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['prices'].extend(records)
                data['last_update'] = datetime.now().isoformat()
                data['total_records'] = len(data['prices'])
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            self.total_written += len(records)
        except Exception as e:
            print(f"❌ 写入文件失败: {e}")

    def get_websocket_url(self):
        if self.exchange == 'binance':
            return f"wss://fstream.binance.com/ws/{self.symbol.lower()}@aggTrade"
        elif self.exchange == 'bybit':
            return "wss://stream.bybit.com/v5/public/linear"
        raise ValueError(f"不支持的交易所: {self.exchange}")

    async def _handle_record(self, record):
        # ── 节流：若设置了最小间隔，丢弃过密的tick ──
        ts = record['timestamp']
        if self.min_interval_ms > 0:
            if self._last_saved_ts >= 0 and (ts - self._last_saved_ts) < self.min_interval_ms:
                return   # 间隔不足，丢弃本条
        self._last_saved_ts = ts

        self.local_data.append(record)
        # 同步写全局 price_data（仅主采集器）
        if self.tag == 'main':
            price_data.append(record)
            if len(price_data) > max_memory_records:
                price_data.pop(0)
        # 资费窗口采集写独立列表（限内存）
        if len(self.local_data) > max_memory_records:
            self.local_data.pop(0)
        self.write_buffer.append(record)
        if len(self.write_buffer) >= write_batch_size:
            self._write_to_file(self.write_buffer)
            self.write_buffer = []
        if self.on_tick:
            self.on_tick(record, self)

    async def process_binance_message(self, message):
        try:
            data = json.loads(message)
            if 'p' in data and 'T' in data:
                record = {
                    'timestamp': data['T'],
                    'price':     float(data['p']),
                    'quantity':  float(data['q']),
                    'datetime':  datetime.fromtimestamp(data['T']/1000).isoformat()
                }
                await self._handle_record(record)
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")

    async def process_bybit_message(self, message):
        try:
            data = json.loads(message)
            if 'topic' in data and 'data' in data:
                for trade in data['data']:
                    record = {
                        'timestamp': int(trade['T']),
                        'price':     float(trade['p']),
                        'quantity':  float(trade['v']),
                        'datetime':  datetime.fromtimestamp(int(trade['T'])/1000).isoformat()
                    }
                    await self._handle_record(record)
        except Exception as e:
            print(f"❌ 处理Bybit消息失败: {e}")

    async def subscribe_bybit(self):
        await self.ws.send(json.dumps({"op":"subscribe","args":[f"publicTrade.{self.symbol}"]}))

    async def start_collection(self):
        ws_url = self.get_websocket_url()
        retry_count = 0
        max_retries = 10
        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(
                    ws_url, ping_interval=20, ping_timeout=10,
                    close_timeout=10, open_timeout=20
                ) as websocket:
                    self.ws = websocket
                    retry_count = 0
                    if self.exchange == 'bybit':
                        await self.subscribe_bybit()
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(websocket.recv(), timeout=30)
                            if self.exchange == 'binance':
                                await self.process_binance_message(msg)
                            else:
                                await self.process_bybit_message(msg)
                        except asyncio.TimeoutError:
                            try: await websocket.ping()
                            except: break
            except Exception as e:
                retry_count += 1
                print(f"⚠️ [{self.symbol}] 连接失败({retry_count}/{max_retries}): {e}")
                if retry_count < max_retries and self.running:
                    await asyncio.sleep(min(retry_count * 2, 15))

    def run_in_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start_collection())
        except Exception as e:
            if self.running: print(f"⚠️ 采集器异常 [{self.symbol}]: {e}")
        finally:
            try: self.loop.close()
            except: pass

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        self.running = False
        if self.write_buffer:
            self._write_to_file(self.write_buffer)
            self.write_buffer = []
        print(f"✅ [{self.tag or self.symbol}] 采集完成，共写入 {self.total_written} 条")
        print(f"📁 文件: {self.current_file_path}")
        return self.current_file_path


# ═══════════════════════════════════════════
# FundingMonitor  - 资费率监控核心
# ═══════════════════════════════════════════

class FundingMonitor:
    """
    1. 定时从币安拉取所有永续合约资费率
    2. 按绝对值排列，找TOP N
    3. 在下次结算前 pre_minutes 分钟自动开始采集
    4. 结算后 post_minutes 分钟停止采集
    """
    FUNDING_API = "https://fapi.binance.com/fapi/v1/premiumIndex"
    FUNDING_INFO_API = "https://fapi.binance.com/fapi/v1/fundingInfo"

    def __init__(self):
        self.running = False
        self.thread  = None
        self.loop    = None
        self._active_collectors = {}   # symbol -> DataCollector
        self._scheduled_start_done = False
        self._scheduled_stop_done  = False
        self._last_funding_ts = None   # 上次结算时间戳(记录已处理)

    def _log(self, msg, level='INFO'):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        entry = f"[{ts}] {msg}"
        print(f"💰 {entry}")
        funding_status['collect_log'].append(entry)
        if len(funding_status['collect_log']) > 200:
            funding_status['collect_log'].pop(0)

    TICKER_API = "https://fapi.binance.com/fapi/v1/ticker/24hr"

    async def fetch_funding_rates(self):
        """
        拉取资费率 + 24h成交额，过滤低流动性小币。
        排序规则: 按资费率绝对值降序（已过滤掉成交额低于门槛的币种）
        """
        try:
            loop = asyncio.get_event_loop()
            min_vol = funding_status.get('min_volume_usd', 30_000_000)  # 默认3000万U/天

            def _fetch_all():
                def _get(url):
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        return json.loads(r.read().decode('utf-8'))
                funding_raw = _get(FundingMonitor.FUNDING_API)
                ticker_raw  = _get(FundingMonitor.TICKER_API)
                return funding_raw, ticker_raw

            funding_raw, ticker_raw = await loop.run_in_executor(None, _fetch_all)

            # 构建成交额查找表 {symbol: quoteVolume_24h}
            vol_map = {}
            for t in ticker_raw:
                try:
                    vol_map[t['symbol']] = float(t.get('quoteVolume', 0))
                except (ValueError, TypeError):
                    pass

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

                    # 过滤流动性不足的小币
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
                        'direction':         '多付空' if rate > 0 else '空付多'
                    })
                except (ValueError, TypeError):
                    continue

            # 按资费率绝对值降序
            result.sort(key=lambda x: x['abs_rate'], reverse=True)
            self._log(f"📊 共 {len(result)} 个币种通过流动性过滤（门槛:{min_vol/1e6:.0f}百万U）")
            return result

        except Exception as e:
            self._log(f"拉取资费率失败: {e}", 'ERROR')
            return []

    def _start_symbol_collect(self, symbol, tag_prefix='FUNDING', is_primary=False):
        """
        启动对某个symbol的采集。
        is_primary=True（第一个币）: 直接激活第一个Tab的主采集器，
                                     price_data 全局数据、K线图、状态栏全部同步。
        is_primary=False（其余币）: 启动独立 DataCollector，存独立文件。
        """
        if symbol in self._active_collectors:
            self._log(f"{symbol} 已在采集中，跳过重复启动")
            return

        folder  = funding_status['collect_folder']
        fmt     = funding_status['collect_format']
        fn      = f"funding_{symbol}"
        min_ms  = funding_status.get('min_interval_ms', 0)

        if is_primary:
            # ── 复用第一个Tab主采集器 ──
            ok = _start_main_collector(
                exchange='binance', symbol=symbol,
                save_folder=folder, filename=fn,
                format_type=fmt, min_interval_ms=min_ms
            )
            if ok:
                # 用 data_collector 对象做占位，统一管理
                self._active_collectors[symbol] = data_collector
                funding_status['auto_collectors'][symbol] = {
                    'started': datetime.now().isoformat(),
                    'file': str(data_collector.current_file_path).replace('\\','/'),
                    'is_primary': True
                }
                self._log(f"🔴 [主采集] 激活实时Tab采集 {symbol}，K线图实时可见")
            else:
                self._log(f"❌ 主采集器启动失败: {symbol}", 'ERROR')
        else:
            # ── 独立采集器（第2~N个币）──
            collector = DataCollector(
                exchange='binance', symbol=symbol,
                save_folder=folder, filename=fn,
                format_type=fmt, tag=f"{tag_prefix}_{symbol}"
            )
            collector.min_interval_ms = min_ms
            collector.start()
            self._active_collectors[symbol] = collector
            funding_status['auto_collectors'][symbol] = {
                'started': datetime.now().isoformat(),
                'file': str(collector.current_file_path).replace('\\','/'),
                'is_primary': False
            }
            self._log(f"▶️ [独立采集] 启动 {symbol}，文件: {collector.current_file_path}")

    def _stop_symbol_collect(self, symbol):
        """停止某个symbol的采集"""
        info = funding_status['auto_collectors'].get(symbol, {})
        collector = self._active_collectors.pop(symbol, None)
        funding_status['auto_collectors'].pop(symbol, None)
        if not collector:
            return
        if info.get('is_primary'):
            # 主采集器：调用统一停止函数
            written = collector.total_written if collector else 0
            _stop_main_collector()
            self._log(f"⏹️ [主采集] 停止 {symbol}，共 {written} 条")
        else:
            fp = collector.stop()
            self._log(f"⏹️ [独立采集] 停止 {symbol}，共 {collector.total_written} 条，文件: {fp}")

    def _stop_all_collectors(self):
        for sym in list(self._active_collectors.keys()):
            self._stop_symbol_collect(sym)

    async def monitor_loop(self):
        """
        主监控循环 - 精简版：
          · 非窗口期：每5分钟拉一次资费率刷新排行显示，其余时间休眠
          · 结算前 pre+1 分钟：拉取一次资费率，锁定本次采集名单
          · 结算前 pre 分钟 ~ 结算后 post 分钟：持续采集
          · 窗口结束：停止采集，重置，等待下次
        """
        self._log("🚀 资费率监控已启动（智能调度模式）")

        IDLE_REFRESH_SEC  = 300   # 非窗口期每5分钟刷新一次排行显示
        CHECK_SEC         = 5     # 窗口附近每5秒检查一次
        last_idle_fetch   = 0     # 上次非窗口期拉取时间戳(s)
        targets_confirmed = False # 本轮窗口是否已确认采集名单
        confirmed_targets = []    # 本轮确认的采集名单
        session_key       = None  # 本轮结算时间戳，用于防止重复处理

        async def _do_fetch_rates(reason=''):
            """拉取资费率并更新全局状态，返回 rates 列表"""
            self._log(f"🔄 拉取资费率{'（'+reason+'）' if reason else ''}...")
            rates = await self.fetch_funding_rates()
            if rates:
                top_n = funding_status['top_n']
                funding_status['top_symbols'] = rates[:top_n]
                funding_status['last_fetch_time'] = datetime.now().strftime('%H:%M:%S')
                earliest = get_earliest_next_funding(rates[:top_n])
                if earliest:
                    funding_status['next_funding_time'] = earliest
                self._log(
                    f"✅ {len(rates)} 个合约 | TOP1: {rates[0]['symbol']} "
                    f"({rates[0]['rate_pct']}) | 最近结算: "
                    f"{datetime.fromtimestamp(funding_status['next_funding_time']/1000).strftime('%H:%M:%S')}"
                )
            return rates

        # 启动时先拉一次，初始化排行和结算时间
        await _do_fetch_rates('初始化')

        while self.running:
            now_ms  = int(time.time() * 1000)
            now_sec = now_ms / 1000
            next_ts = funding_status.get('next_funding_time') or 0
            pre_ms  = funding_status['pre_minutes']  * 60 * 1000
            post_ms = funding_status['post_minutes'] * 60 * 1000
            diff_ms = next_ts - now_ms   # 正=未到结算，负=已过结算

            # ════════ 阶段判断 ════════
            in_collect_window = (-post_ms) <= diff_ms <= pre_ms
            need_pre_fetch    = (diff_ms <= (pre_ms + 60_000)) and not targets_confirmed

            # ════════ 阶段A：非窗口期，低频待机 ════════
            if not in_collect_window and not need_pre_fetch:
                funding_status['auto_collect_phase'] = 'idle'

                # 如果有遗留采集器（异常情况），清掉
                if self._active_collectors:
                    self._stop_all_collectors()

                # 非窗口期每5分钟刷新一次排行表（仅供UI显示，不影响采集）
                if now_sec - last_idle_fetch >= IDLE_REFRESH_SEC:
                    await _do_fetch_rates('定时刷新排行')
                    last_idle_fetch = now_sec

                    # 更新 next_ts（因为已刷新）
                    next_ts = funding_status.get('next_funding_time') or 0
                    diff_ms = next_ts - now_ms

                # 计算距进入窗口还有多久，尽量长睡眠减少空转
                time_to_prefetch_ms = diff_ms - (pre_ms + 60_000)
                if time_to_prefetch_ms > CHECK_SEC * 1000:
                    # 最多睡到"下次非窗口刷新"或"进入窗口前"两者较近的那个
                    sleep_sec = min(
                        time_to_prefetch_ms / 1000 - 1,    # 提前1秒醒来
                        IDLE_REFRESH_SEC - (now_sec - last_idle_fetch) + 1
                    )
                    sleep_sec = max(sleep_sec, CHECK_SEC)
                    await asyncio.sleep(sleep_sec)
                else:
                    await asyncio.sleep(CHECK_SEC)
                continue

            # ════════ 阶段B：进入预拉取区，确认本轮采集名单（只做一次）════════
            if need_pre_fetch and not targets_confirmed:
                self._log(f"⏰ 距结算 {diff_ms/1000:.0f}s，进入预拉取，锁定采集名单...")
                funding_status['auto_collect_phase'] = 'pre_collect'
                rates = await _do_fetch_rates('窗口前确认名单')
                last_idle_fetch = now_sec  # 重置避免立刻再拉

                # 锁定本轮 targets
                manual = funding_status.get('selected_symbols', [])
                if manual:
                    confirmed_targets = list(manual)
                    self._log(f"📌 手动指定采集: {confirmed_targets}")
                else:
                    n        = funding_status.get('top_n', 5)
                    next_ref = funding_status.get('next_funding_time', 0)
                    in_window_syms = [
                        s['symbol'] for s in funding_status['top_symbols']
                        if abs(s.get('next_funding_ts', 0) - next_ref) <= 60_000
                    ]
                    confirmed_targets = (in_window_syms[:n] if in_window_syms
                                         else [s['symbol'] for s in funding_status['top_symbols'][:n]])
                    self._log(f"📌 本轮自动采集名单({len(confirmed_targets)}个): {confirmed_targets}")

                targets_confirmed = True
                session_key = next_ts

            # ════════ 阶段C：采集窗口内，保持采集器运行 ════════
            if in_collect_window and targets_confirmed:
                if diff_ms > 0:
                    funding_status['auto_collect_phase'] = 'pre_collect'
                else:
                    funding_status['auto_collect_phase'] = 'post_collect'

                for idx, sym in enumerate(confirmed_targets):
                    if sym not in self._active_collectors:
                        self._log(f"▶️ 启动采集 {sym}（距结算 {diff_ms/1000:.0f}s）")
                        # 第1个币激活主采集器(实时Tab可见)，其余币独立采集
                        self._start_symbol_collect(sym, is_primary=(idx == 0))

                await asyncio.sleep(CHECK_SEC)
                continue

            # ════════ 阶段D：窗口结束，收尾 ════════
            if diff_ms < -post_ms and targets_confirmed:
                self._log(f"⏹️ 采集窗口结束（结算已过 {abs(diff_ms)/1000:.0f}s），停止所有采集器")
                self._stop_all_collectors()
                self._last_funding_ts = session_key
                funding_status['auto_collect_phase'] = 'idle'
                targets_confirmed = False
                confirmed_targets = []
                session_key = None

                # 结束后立即拉取新的资费率，刷新下次结算时间
                await _do_fetch_rates('结算完毕，准备下轮')
                last_idle_fetch = now_sec

            await asyncio.sleep(CHECK_SEC)

        self._stop_all_collectors()
        self._log("🛑 资费率监控已停止")

    def run_in_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.monitor_loop())
        except Exception as e:
            print(f"⚠️ FundingMonitor 异常: {e}")
        finally:
            try: self.loop.close()
            except: pass

    def start(self):
        if not self.running:
            self.running = True
            funding_status['running'] = True
            self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        self.running = False
        funding_status['running'] = False
        self._stop_all_collectors()
        funding_status['auto_collect_phase'] = 'idle'


# ─────────────────────────── HTML 模板 ───────────────────────────

def _start_main_collector(exchange, symbol, save_folder, filename, format_type, min_interval_ms=0):
    """
    核心启动函数：启动第一个Tab的主采集器，同时更新全局 price_data 和 current_config。
    FundingMonitor 触发时直接调用此函数，保证两个Tab共享同一份数据。
    """
    global data_collector, current_config, price_data
    if data_collector:
        data_collector.stop()
    price_data = []
    dc = DataCollector(exchange, symbol, save_folder, filename, format_type, tag='main')
    dc.min_interval_ms = min_interval_ms
    success = dc.start()
    if success:
        data_collector = dc
        current_config.update({
            'exchange': exchange, 'symbol': symbol,
            'filename': filename, 'save_folder': save_folder,
            'format': format_type, 'running': True
        })
    return success

def _stop_main_collector():
    """停止主采集器"""
    global data_collector, current_config
    if data_collector:
        data_collector.stop()
        data_collector = None
    current_config['running'] = False

