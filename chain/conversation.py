# chain/conversation.py — LangChain conversational retrieval chain

from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_community.vectorstores import faiss
from langchain.globals import set_llm_cache
from config import CHAT_MODEL, RETRIEVER_K, ENABLE_CACHE
from langchain_community.cache import SQLiteCache  # zero extra deps

if ENABLE_CACHE:
    set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))
# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_QA_TEMPLATE = (
    "Tu es un assistant documentaire intelligent et précis. "
    "Le contexte ci-dessous contient des extraits d'un ou plusieurs documents.\n\n"
    "Règles STRICTES:\n"
    "- Réponds UNIQUEMENT en français.\n"
    "- N'invente JAMAIS d'informations, de chiffres, d'adresses ou de noms.\n"
    "- Adapte le format à la question : si c'est une question générale sur une personne ou une entité, "
    "réponds en langage naturel et fluide. "
    "Si c'est une demande de données précises (facture, totaux, coordonnées), "
    "liste les champs clairement.\n"
    "- Recopie les valeurs EXACTEMENT comme elles apparaissent dans le document.\n"
    "- Synthétise TOUTES les informations pertinentes — ne t'arrête pas au premier résultat.\n\n"
    "Contexte:\n{context}\n\n"
    "Question: {question}\n"
    "Réponse:"
)

QA_PROMPT = PromptTemplate(input_variables=["context", "question"], template=_QA_TEMPLATE)

# ---------------------------------------------------------------------------
# Helper to format retrieved docs into a single context string
# ---------------------------------------------------------------------------

def _format_docs(docs) -> str:
    return "\n\n---\n\n".join(d.page_content for d in docs)

# ---------------------------------------------------------------------------
# Chain factory — returns an LCEL chain that supports .stream()
# ---------------------------------------------------------------------------

def get_conversationchain(vectorstore: faiss.FAISS):
    """Build an LCEL chain backed by *vectorstore*. Supports .stream()."""
    llm = Ollama(model=CHAT_MODEL)
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

    chain = (
        {
            "context": RunnableLambda(lambda x: x["question"]) | retriever | RunnableLambda(_format_docs),
            "question": RunnableLambda(lambda x: x["question"]),
        }
        | QA_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain