"""中文版本启动入口。"""

import routes  # noqa: F401
import runtime


def main():
    print("\n" + "=" * 65)
    print("🌐 加密货币毫秒级K线图系统 Pro v3.0（模块化-中文）")
    print("=" * 65)
    print("\n📊 访问地址: http://localhost:7890")
    print("\n📦 依赖安装: pip install flask flask-cors websockets")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 65 + "\n")
    runtime.app.run(host='0.0.0.0', port=7890, debug=False, threaded=True)


if __name__ == '__main__':
    main()
