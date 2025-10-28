from __future__ import annotations

import json
from pathlib import Path
from typing import IO, List, Union

import pdfplumber
from decouple import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, ConfigDict, Field, ValidationError

# ========================================
# CONFIGURAÇÕES
# ========================================
OPENAI_API_KEY = config("OPENAI_API_KEY")

# Inicializa modelo LLM
llm = ChatOpenAI(model="gpt-5", api_key=OPENAI_API_KEY, temperature=0)


# ========================================
# SCHEMA DE VALIDAÇÃO
# ========================================
class HistoricoItem(BaseModel):
    mes: str = Field(default="")
    consumo: str = Field(default="")


class FaturaSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nome_do_cliente: str = Field(default="", alias="nome do cliente")
    data_de_emissao: str = Field(default="", alias="data de emissao")
    data_de_vencimento: str = Field(default="", alias="data de vencimento")
    codigo_do_cliente_uc: str = Field(default="", alias="codigo do cliente - uc")
    mes_de_referencia: str = Field(default="", alias="mes de referencia")
    consumo_kwh: str = Field(default="", alias="consumo kwh")
    valor_a_pagar: str = Field(default="", alias="valor a pagar")
    economia: str = Field(default="", alias="Economia")
    historico_de_consumo: List[HistoricoItem] = Field(
        default_factory=list, alias="historico de consumo"
    )
    saldo_acumulado: str = Field(default="", alias="saldo acumulado")
    preco_unit_com_tributos: str = Field(default="", alias="preco unit com tributos")
    energia_atv_injetada: str = Field(default="", alias="Energia Atv Injetada")


# ========================================
# PROMPT TEMPLATE
# ========================================
PROMPT_TEMPLATE = PromptTemplate.from_template(
    """Você é um assistente especializado em leitura de faturas de energia elétrica.
Receberá abaixo o TEXTO EXTRAÍDO DE UM PDF (pode conter ruídos, quebras e colunas desordenadas).
Sua tarefa é identificar e retornar um JSON com os campos EXATOS abaixo:

- "nome do cliente"
- "data de emissao"
- "data de vencimento"
- "codigo do cliente - uc"
- "mes de referencia"
- "consumo kwh"
- "valor a pagar"
- "Economia" 
- "historico de consumo" (lista de objetos com "mes" e "consumo" em ordem cronológica se possível)
- "saldo acumulado"
- "preco unit com tributos"
- "Energia Atv Injetada"



Orientações específicas:
- "nome do cliente": geralmente aparece após "PAGADOR" ou destacado próximo ao endereço do cliente.
- "codigo do cliente - uc": normalize para o formato "10/########-#". Prefira valores já com "10/" na fatura (ex.: "10/33525227-0"). Se só houver versões fragmentadas (ex.: "3352527-2025-9-6"), reconstrua removendo sufixos extras e aplicando o prefixo "10/" com o dígito verificador mais plausível.
- "consumo kwh" está no campo Quant. ao lado de Unit. kWh. Ele será encontrado em itens da fatura
- "historico de consumo": extraia pares de mês e consumo da seção CONSUMO DOS ÚLTIMOS 13 meses ou da lista "Consumo FATURADO".
  Quando números e meses estiverem em colunas diferentes, faça a correspondência
  usando proximidade e ordem: valores mais recentes devem ser ligados aos meses mais recentes
  e meses sem valor claramente identificado devem receber "".
- "preco unit com tributos": busque o valor decimal da coluna "Preço unit (R$) com tributos" como valor aproximado de 1,099590.
- "Energia Atv Injetada": identifique todas as linhas de energia ativa injetada (Energia Atv Injetada), ela está em itens da fatura, e some as quantidades e divida pelo preco unit com tributos. Remova sinais negativos, normalize para o formato brasileiro e desconsidere valores que não estejam explicitamente ligados à energia injetada.
- "valor a pagar": calcule como `valor_a_pagar = energia_injetada_total_kwh * preco_unit_com_tributos * 0.7`. Se qualquer um desses valores estiver ausente.
- "Economia":  Calcule `Economia = Energia Atv Injetada em kWh * preco unit com tributos * 0.3`. Formate com vírgula e duas casas decimais; se não encontrar os componentes necessários, retorne "".


Regras importantes:
0. Use pistas como "PAGADOR", "DATA DO DOCUMENTO", "VENCIMENTO", "NOTA FISCAL Nº", "MATRÍCULA", "Consumo em kWh", "VALOR DO DOCUMENTO" e "CONT.IL.PUB".
1. Analise cuidadosamente números que apareçam junto a descrições; selecione o valor mais plausível.
2. Se houver múltiplos candidatos, escolha o que esteja mais próximo da descrição do campo.
3. Converta valores numéricos para o padrão brasileiro com vírgula como separador decimal.
4. Só utilize "" quando realmente não houver valor legível no texto.
5. O histórico deve ser uma lista — mesmo vazia — nunca uma string.
6. Responda **somente** com o JSON final, sem comentários ou textos adicionais.
7. Quando números e meses estiverem em colunas separadas, faça a correspondência respeitando
   a ordem cronológica (meses mais recentes com valores mais recentes).
8. Não invente "0,00" para consumo ausente — se não houver valor explícito, use "".
9. Ignore sequências de "0,00" sem rótulo claro; trate-as como ruído.
10. "codigo do cliente - uc" deve sempre começar com "10/" e ter apenas um hífen final para o dígito verificador (ex.: "10/33525227-0").
11. Antes de realizar cálculos, converta os valores extraídos para números (substituindo vírgula por ponto), execute as operações e depois formate novamente com vírgula e duas casas decimais.
12. Ao calcular "valor a pagar" e "Economia", mantenha o resultado com duas casas decimais e formato brasileiro.
13. A Energia Atv Injetada estará com sinal negativo no PDF; Some todos e converta para positivo antes de usar nos cálculos.
Texto a ser analisado:
----------------------
{{ text_pdf }}
----------------------
""",
    template_format="jinja2",
)


# ========================================
# FUNÇÕES PRINCIPAIS
# ========================================
def ler_pdf(caminho_pdf: Union[str, Path, IO[bytes]]) -> str:
    """Extrai texto de um PDF usando pdfplumber, preservando melhor a estrutura."""
    if hasattr(caminho_pdf, "seek"):
        caminho_pdf.seek(0)

    partes = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = (pagina.extract_text() or "").strip()
            if texto:
                partes.append(texto)
    return "\n\n".join(partes)


def extrair_dados(texto_pdf: str) -> dict:
    """Envia o texto do PDF ao LLM e retorna o JSON estruturado validado."""
    prompt = PROMPT_TEMPLATE.format(text_pdf=texto_pdf)
    resposta = llm.invoke(prompt)

    try:
        dados_raw = json.loads(resposta.content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Resposta do LLM não é JSON válido: {exc.msg}") from exc

    try:
        resultado = FaturaSchema.model_validate(dados_raw)
    except ValidationError as exc:
        raise ValueError(
            f"JSON recebido não corresponde ao schema esperado: {exc}"
        ) from exc

    return resultado.model_dump(by_alias=True)


def processar_pdf(caminho_pdf: Union[str, Path, IO[bytes]]) -> dict:
    """Extrai texto do PDF e retorna o dicionário estruturado com os dados da fatura."""
    texto = ler_pdf(caminho_pdf)
    if not texto.strip():
        raise ValueError("Nenhum texto foi extraído do PDF.")
    return extrair_dados(texto)


# ========================================
# EXECUÇÃO DIRETA
# ========================================
if __name__ == "__main__":
    pdf_path = Path(__file__).resolve().parent / "pdfs" / "exemplo.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado em {pdf_path}. Coloque o PDF esperado ou ajuste o caminho."
        )

    texto_extraido = ler_pdf(pdf_path)
    print("=== TEXTO EXTRAÍDO DO PDF ===")
    print(texto_extraido)

    try:
        dados_fatura = extrair_dados(texto_extraido)
    except ValueError as erro:
        print("Erro ao interpretar resposta:", erro)
    else:
        print("\n=== JSON FINAL ===")
        print(json.dumps(dados_fatura, indent=2, ensure_ascii=False))
