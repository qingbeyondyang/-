"""English version bootstrap entry."""

import routes  # noqa: F401
import runtime


def main():
    print("\n" + "=" * 65)
    print("🌐 Crypto Millisecond K-Line System Pro v3.0 (Modular-English)")
    print("=" * 65)
    print("\n📊 URL: http://localhost:7891")
    print("\n📦 Install deps: pip install flask flask-cors websockets")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 65 + "\n")
    runtime.app.run(host='0.0.0.0', port=7891, debug=False, threaded=True)


if __name__ == '__main__':
    main()

