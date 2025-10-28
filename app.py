from __future__ import annotations

import streamlit as st
from decouple import UndefinedValueError, config

from asset_utils import get_logo_data_uri
from ui_theme import inject_global_styles

# ========================================
# CONFIGURAÇÕES GERAIS
# ========================================
st.set_page_config(
    page_title="Boeira | Leitor de Faturas",
    page_icon="⚡",
    layout="wide",
)

DEFAULT_USERNAME = config("APP_USERNAME", default="boeira.pereira")
try:
    DEFAULT_PASSWORD = config("APP_PASSWORD")
except UndefinedValueError:
    DEFAULT_PASSWORD = None


# ========================================
inject_global_styles()


# ========================================
# HELPERS
# ========================================
def ensure_session_defaults() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""
    if "login_user" not in st.session_state:
        st.session_state.login_user = DEFAULT_USERNAME


def render_login() -> None:
    logo_data = get_logo_data_uri()
    logo_html = (
        f'<img src="{logo_data}" alt="Logotipo Boeira" class="hero-logo" />'
        if logo_data
        else ""
    )
    st.markdown(
        f"""
        <section class="hero-section">
            {logo_html}
            <h1>Boeira Soluções - Portal de Faturas</h1>
            <p>
                Automatize a leitura das suas faturas de energia com suporte a múltiplos arquivos,
                cálculo inteligente e relatórios personalizados prontos para distribuição.
            </p>
            <ul class="hero-bullets">
                <li>Upload múltiplo de arquivos</li>
                <li>Resumo HTML pronto</li>
                <li>Download individual ou .zip</li>
            </ul>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="sidebar-header">
                <h2>Acesso</h2>
                <p>Use suas credenciais para iniciar uma nova leitura.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        menu_option = st.radio(
            "Menu",
            options=("Login"),
            index=0,
            key="login_menu",
            label_visibility="collapsed",
        )

        if menu_option == "Login":
            with st.form("login_form"):
                username = st.text_input(
                    "Usuário",
                    value=st.session_state.get("login_user", DEFAULT_USERNAME),
                    placeholder="boeira.pereira",
                )
                password = st.text_input(
                    "Senha",
                    value="",
                    type="password",
                    placeholder="********",
                )
                submit = st.form_submit_button(
                    "Entrar",
                    use_container_width=True,
                    disabled=DEFAULT_PASSWORD is None,
                )

            if DEFAULT_PASSWORD is None:
                st.warning(
                    "Defina a senha do portal através da variável de ambiente "
                    "`APP_PASSWORD` antes de liberar o acesso.",
                    icon="⚠️",
                )

            if submit:
                if DEFAULT_PASSWORD is None:
                    st.session_state.authenticated = False
                    st.session_state.login_error = (
                        "Senha indisponível. Consulte a equipe técnica."
                    )
                elif username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.login_error = ""
                    st.session_state.login_user = username
                    st.session_state.results = []
                    st.switch_page("pages/portal.py")
                else:
                    st.session_state.authenticated = False
                    st.session_state.login_error = "Usuário ou senha inválidos."

            if st.session_state.login_error:
                st.error(st.session_state.login_error)
        else:
            st.session_state.login_error = ""          
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    ensure_session_defaults()

    if st.session_state.authenticated:
        st.switch_page("pages/portal.py")
        return

    render_login()


if __name__ == "__main__":
    main()
