from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

import re

import streamlit as st
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from asset_utils import get_logo_data_uri, get_logo_path, get_qrcode_data_uri
from main import extrair_dados, ler_pdf
from ui_theme import inject_global_styles

# ========================================
# CONFIGURAÇÕES
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
PDF_TEMPLATE = env.get_template("fatura_pdf.html")

inject_global_styles()


# ========================================
# HELPERS
# ========================================
def ensure_dashboard_state() -> None:
    if "results" not in st.session_state:
        st.session_state.results: List[dict] = []


def map_pdf_context(dados: Dict) -> Dict:
    def pick(key: str, default: str = "—") -> str:
        raw = dados.get(key, "")
        if raw is None:
            return default
        text = str(raw).strip()
        return text if text else default

    def parse_decimal(value: Optional[object]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        # remove currency and thousand separators
        text = re.sub(r"[^\d,.-]", "", text)
        if not text:
            return None
        text = text.replace(".", "").replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    def format_currency(value: Optional[float]) -> str:
        if value is None:
            return ""
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"

    def format_number(value: Optional[float], suffix: str = "") -> str:
        if value is None:
            return ""
        formatted = (
            f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        return f"{formatted}{suffix}"

    def split_mes_ano(label: str) -> (str, str):
        if not label:
            return ("—", "")
        label = label.strip()
        match = re.match(r"([A-Za-zÀ-ÿ]+)[^\d]*(\d{2,4})", label)
        if match:
            mes = match.group(1).upper()
            ano = match.group(2)
            if len(ano) == 2:
                ano = f"20{ano}"
            return (mes, ano)
        return (label, "")

    consumo_atual_val = parse_decimal(pick("consumo kwh", ""))
    energia_injetada_val = parse_decimal(pick("Energia Atv Injetada", ""))
    preco_unitario_val = parse_decimal(pick("preco unit com tributos", ""))
    valor_total_val = parse_decimal(pick("valor a pagar", ""))
    economia_val = parse_decimal(pick("Economia", ""))
    valor_pagar_val = parse_decimal(pick("valor a pagar", ""))
    saldo_acumulado_val = parse_decimal(pick("saldo acumulado", ""))

    historico_items = []
    consumos_validos: List[float] = []
    for raw_item in dados.get("historico de consumo", []):
        if isinstance(raw_item, dict):
            mes_label = raw_item.get("mes", "")
            consumo_raw = raw_item.get("consumo", "")
        else:
            mes_label = getattr(raw_item, "mes", "")
            consumo_raw = getattr(raw_item, "consumo", "")
        mes, ano = split_mes_ano(mes_label)
        consumo_val = parse_decimal(consumo_raw)
        has_consumo = consumo_val is not None and consumo_val > 0
        if has_consumo:
            consumos_validos.append(consumo_val)
        historico_items.append(
            {
                "rotulo": f"{mes}/{ano}" if ano else mes,
                "consumo_display": format_number(consumo_val, " kWh")
                if consumo_val is not None
                else ("Sem dados" if consumo_raw in (None, "", "0") else consumo_raw),
                "has_consumo": has_consumo,
            }
        )

    historico_resumo = ""
    if consumos_validos:
        media = sum(consumos_validos) / len(consumos_validos)
        historico_resumo = (
            f"{len(consumos_validos)} meses com consumo registrado | "
            f"Média: {format_number(media, ' kWh')}"
        )

    bandeira_val = dados.get("bandeira") or ""
    bandeira_classe = ""
    if isinstance(bandeira_val, str):
        lower = bandeira_val.lower()
        if "vermelha" in lower:
            bandeira_classe = "bandeira-vermelha"
        elif "amarela" in lower:
            bandeira_classe = "bandeira-amarela"
        elif lower.strip():
            bandeira_classe = "bandeira-verde"

    cliente = {
        "nome": pick("nome do cliente"),
        "codigo_uc": pick("codigo do cliente - uc"),
        "cpf_cnpj": dados.get("documento do cliente", "—"),
        "telefone": dados.get("telefone", ""),
        "email": dados.get("email", ""),
        "endereco": dados.get("endereco", None),
    }

    fatura = {
        "numero_fatura": dados.get("numero da fatura", pick("codigo do cliente - uc")),
        "data_vencimento": pick("data de vencimento"),
        "data_emissao": pick("data de emissao"),
        "valor_total_display": format_currency(valor_total_val) or pick("valor a pagar"),
        "valor_total_num": valor_total_val or 0.0,
        "codigo_barras": dados.get("codigo de barras", ""),
        "saldo_acumulado_display": format_currency(saldo_acumulado_val)
        if saldo_acumulado_val is not None
        else pick("saldo acumulado"),
    }

    context = {
        "logo_path": get_logo_data_uri(),
        "qrcode_path": get_qrcode_data_uri(),
        "mes_referencia": pick("mes de referencia"),
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "cliente": cliente,
        "fatura": fatura,
        "consumo_atual": format_number(consumo_atual_val, " kWh")
        if consumo_atual_val is not None
        else pick("consumo kwh"),
        "energia_ativa_display": format_number(energia_injetada_val, " kWh")
        if energia_injetada_val is not None
        else pick("Energia Atv Injetada"),
        "preco_unitario_display": format_number(preco_unitario_val)
        if preco_unitario_val is not None
        else pick("preco unit com tributos"),
        "economia_display": format_currency(economia_val)
        if economia_val is not None
        else "",
        "valor_pagar_display": format_currency(valor_pagar_val)
        if valor_pagar_val is not None
        else fatura["valor_total_display"],
        "saldo_acumulado_display": fatura["saldo_acumulado_display"],
        "bandeira": bandeira_val if isinstance(bandeira_val, str) else "",
        "bandeira_classe": bandeira_classe,
        "historico_consumo": historico_items,
        "historico_resumo": historico_resumo,
    }
    return context

def render_pdf(dados: Dict) -> bytes:
    context = map_pdf_context(dados)
    html_content = PDF_TEMPLATE.render(**context)
    pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
    return pdf_bytes


def build_zip(results: List[dict]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        for item in results:
            zip_file.writestr(f"{item['filename']}.pdf", item["pdf"])
    buffer.seek(0)
    return buffer.getvalue()


# ========================================
# PÁGINA PRINCIPAL
# ========================================
def main() -> None:
    ensure_dashboard_state()

    if not st.session_state.get("authenticated"):
        st.warning("Faça login para acessar o portal.")
        st.switch_page("app.py")
        st.stop()

    logo_path = get_logo_path()
    if logo_path.exists():
        st.image(str(logo_path), width=220)

    st.sidebar.subheader("Sessão")
    st.sidebar.markdown(
        f"Usuário: **{st.session_state.get('login_user', '—')}**"
    )
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.results = []
        st.switch_page("app.py")
        st.stop()

    st.title("Central de Processamento Boeira 🌩️")
    st.caption("Envie uma ou mais faturas em PDF para extrair os dados estruturados.")

    uploaded_files = st.file_uploader(
        "Selecionar faturas (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Você pode arrastar vários arquivos PDF ao mesmo tempo.",
    )

    processar = st.button(
        "Processar arquivos",
        type="primary",
        disabled=not uploaded_files,
        help="Envia os PDFs selecionados para leitura e análise.",
    )

    if processar and uploaded_files:
        resultados = []
        for item in uploaded_files:
            with st.spinner(f"Processando {item.name}..."):
                try:
                    item.seek(0)
                    texto = ler_pdf(item)
                    dados = extrair_dados(texto)
                    pdf_bytes = render_pdf(dados)
                    resultados.append(
                        {
                            "filename": Path(item.name).stem,
                            "dados": dados,
                            "pdf": pdf_bytes,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Erro ao processar {item.name}: {exc}")
        if resultados:
            st.session_state.results = resultados

    if st.session_state.results:
        st.subheader("Resultados")
        for resultado in st.session_state.results:
            with st.container():
                st.markdown(
                    f'<div class="result-card"><h3>{resultado["filename"]}</h3></div>',
                    unsafe_allow_html=True,
                )
                st.json(resultado["dados"])
                st.download_button(
                    label="Download em PDF",
                    data=resultado["pdf"],
                    file_name=f'{resultado["filename"]}.pdf',
                    mime="application/pdf",
                )
                st.divider()

        zip_bytes = build_zip(st.session_state.results)
        st.download_button(
            label="Download de todos (.zip)",
            data=zip_bytes,
            file_name="faturas_boeira.zip",
            mime="application/zip",
        )


if __name__ == "__main__":
    main()
