import os
import sys
import streamlit.web.cli as stcli

def main():
    # Captura a porta dinâmica do Railway (ou usa 8501 localmente)
    port = int(os.environ.get("PORT", "8501"))

    # Corrige o endereço e define as variáveis certas
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_HEADLESS"] = "true"

    print(f"🚀 Starting Streamlit on dynamic port {port}")

    # Executa o Streamlit programaticamente
    sys.argv = [
        "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0"
    ]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
