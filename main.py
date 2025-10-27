from typing import Union

from decouple import config
from pypdf import PdfReader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

# ========================================
# CONFIGURAÇÕES
# ========================================
OPENAI_API_KEY = config("OPENAI_API_KEY")  # Carrega do .env

# Inicializa modelo LLM
llm = ChatOpenAI(model="gpt-5", api_key=OPENAI_API_KEY)

# Inicializa embeddings
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Prompt template
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
- "historico de consumo": extraia pares de mês e consumo da seção de 13 meses ou da lista "Consumo kWh".
  Quando números e meses estiverem em colunas diferentes, faça a correspondência
  usando proximidade e ordem: valores mais recentes devem ser ligados aos meses mais recentes
  e meses sem valor claramente identificado devem receber "".
  Exemplo prático: se a região mostrar os números "162,00" e "365,00" junto aos meses
  "JUL/25" e "AGO/25", associe "JUL/25" → "162,00" e "AGO/25" → "365,00".
- "preco unit com tributos": busque o valor decimal da coluna "Preço unit (R$) com tributos" como valor aproximado de 1,099590.
- "Energia Atv Injetada": identifique todas as linhas de energia ativa injetada (Energia Atv Injetada), ela está em itens da fatura, e some as quantidades em kWh (coluna "Quant."). Remova sinais negativos, normalize para o formato brasileiro e desconsidere valores que não estejam explicitamente ligados à energia injetada.
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

Texto a ser analisado:
----------------------
{{ text_pdf }}
----------------------
""",
    template_format="jinja2",
)

# ========================================
# FUNÇÃO: Ler PDF
# ========================================
def ler_pdf(caminho_pdf: Union[str, Path]) -> str:
    """Extrai texto de um arquivo PDF"""
    leitor = PdfReader(caminho_pdf)
    texto = ""
    for pagina in leitor.pages:
        texto += pagina.extract_text() + "\n"
    return texto

# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    pdf_path = base_dir / "pdfs" / "exemplo.pdf"  # Caminho do PDF

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado em {pdf_path}. Coloque o PDF esperado ou ajuste o caminho."
        )
    texto = ler_pdf(pdf_path)

    print("=== TEXTO EXTRAÍDO DO PDF ===")
    print(texto)

    # Quebra o texto em chunks para embeddings
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    documentos = [Document(page_content=chunk) for chunk in splitter.split_text(texto)]

    # Gera embeddings
    vetores = embeddings.embed_documents([doc.page_content for doc in documentos])
    print(f"\nEmbeddings gerados para {len(vetores)} chunks de texto.")

    # Gera prompt estruturado e envia ao LLM
    prompt = PROMPT_TEMPLATE.format(text_pdf=texto)
    resposta = llm.invoke(prompt)
    print("\n=== RESPOSTA DO LLM ===")
    print(resposta.content)
