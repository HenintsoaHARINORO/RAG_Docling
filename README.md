# 📄 ChatPDF — RAG local sur documents

Chatbot RAG (Retrieval-Augmented Generation) 100 % local, sans API externe.  
Posez des questions sur vos PDF, DOCX, factures, images et tableaux — tout tourne sur votre machine via Ollama.

---

## Sommaire

1. [Architecture & structure](#architecture--structure)
2. [Pipeline d'ingestion](#pipeline-dingestion)
3. [Choix techniques](#choix-techniques)
4. [Temps de traitement](#temps-de-traitement)
5. [Installation](#installation)
6. [Lancement](#lancement)
7. [Docker](#docker)
8. [Changer de backend LLM](#changer-de-backend-llm)
9. [FAQ](#faq)

---

## Architecture & structure

```
ChatPDF/
├── app.py                  # Point d'entrée Streamlit
├── pipeline.py             # Orchestration ingestion → embedding → FAISS
├── config.py               # Tous les paramètres centralisés (modèles, timeouts…)
│
├── ingestion/
│   ├── extractor.py        # Extraction Markdown via Docling
│   ├── converter.py        # Factory DocumentConverter (PDF + VLM)
│   └── chunker.py          # Découpage du texte en chunks
│
├── embeddings/
│   └── ollama.py           # Appel direct à l'API Ollama /api/embed
│
├── vectorstore/
│   └── faiss_store.py      # Création et chargement de l'index FAISS
│
├── db/
│   ├── connection.py       # Connexion PostgreSQL (psycopg2)
│   ├── documents.py        # CRUD table documents
│   ├── chunks.py           # CRUD table chunks
│   └── faiss_index.py      # Persistance de l'index FAISS en base (BYTEA)
│
├── chain/
│   └── conversation.py     # Chaîne LangChain ConversationalRetrievalChain
│
├── ui/
│   ├── sidebar.py          # Upload, boutons, statuts
│   └── chat.py             # Affichage des messages
│
└── htmlTemplates.py        # Templates HTML des bulles de chat
```

### Flux de données

```
Fichier uploadé
     │
     ▼
[Docling] ──────────────────────────────────────────────────────┐
  • Extraction Markdown structuré                               │
  • Détection des tableaux (TableFormer ACCURATE)              │
  • Description des images/figures via VLM (qwen3-vl:2b)      │
     │                                                          │
     ▼                                                          │
[Chunker]  →  chunks de 2 000 tokens (overlap 400)            │
     │                                                          │
     ▼                                                          │
[PostgreSQL]  →  documents + chunks persistés                  │
     │                                                          │
     ▼                                                          │
[Ollama /api/embed]  →  nomic-embed-text                       │
     │                                                          │
     ▼                                                          │
[FAISS index]  →  sauvegardé en BYTEA dans PostgreSQL ─────────┘
     │
     ▼
Question utilisateur
     │
     ▼
[Retriever FAISS]  →  top-4 chunks pertinents
     │
     ▼
[LangChain ConversationalRetrievalChain]
     │
     ▼
[Ollama qwen2.5:7b]  →  réponse finale
```

---

## Pipeline d'ingestion

### Docling — extraction des documents

[Docling](https://github.com/DS4SD/docling) est la bibliothèque d'IBM Research pour l'extraction structurée de documents.  
Il remplace les approches classiques (PyPDF2, python-docx) pour les formats PDF et DOCX.

**Pourquoi Docling plutôt que PyPDF2 seul ?**

| Capacité | PyPDF2 | Docling |
|---|---|---|
| Extraction texte brut | ✅ | ✅ |
| Structure Markdown (titres, listes) | ❌ | ✅ |
| Détection et extraction de tableaux | ❌ | ✅ (TableFormer) |
| Description automatique des images | ❌ | ✅ (via VLM) |
| Factures avec zones complexes | ❌ | ✅ |
| Export paginé avec marqueurs | ❌ | ✅ |

**Ce qui se passe concrètement (`ingestion/extractor.py`) :**

1. Le fichier uploadé est écrit dans un fichier temporaire
2. `DocumentConverter.convert()` produit un objet document structuré
3. `export_to_markdown()` génère du Markdown avec :
   - des marqueurs de saut de page (`<!-- page_break -->`)
   - des balises `<image_description>…</image_description>` pour chaque figure
4. Le Markdown est nettoyé et stocké en base

**Configuration PDF (`ingestion/converter.py`) :**

```python
PdfPipelineOptions(
    do_table_structure=True,              # TableFormer ACCURATE
    generate_picture_images=True,         # Rasterise les figures
    do_picture_description=True,          # Appelle le VLM sur chaque image
    picture_description_options=...       # → qwen3-vl:2b via Ollama
)
```

### VLM — description des images

Pour les factures et documents avec figures, le modèle `qwen3-vl:2b` est appelé via l'endpoint OpenAI-compatible d'Ollama (`/v1/chat/completions`).  
Le prompt est orienté OCR : il extrait tout le texte visible de haut en bas.

> **Paramètre clé :** `think=False` désactive le mode raisonnement de qwen3 pour des réponses plus rapides.

---

## Choix techniques

### Pourquoi Ollama ?

- **100 % local** : aucune donnée ne quitte la machine — essentiel pour des factures ou documents confidentiels
- **Gestion des modèles simplifiée** : `ollama pull qwen2.5:7b` suffit
- **Apple Silicon natif** : Ollama utilise Metal/MLX, les modèles tournent sur le GPU unifié du Mac M-series
- **`keep_alive: -1`** : le modèle d'embedding reste chargé en mémoire entre les requêtes, évitant le rechargement à chaque chunk
- **Endpoint OpenAI-compatible** : Docling peut appeler le VLM via `/v1/chat/completions` sans adaptation

### Pourquoi LangChain ?

- `ConversationalRetrievalChain` gère nativement l'historique de conversation + la reformulation des questions
- Abstraction du retriever FAISS : un seul appel pour récupérer les top-K chunks
- Facile à remplacer par une autre chaîne (ReAct, RAG-Fusion…) sans toucher au reste du code

### Pourquoi FAISS ?

- Recherche vectorielle en mémoire, ultra-rapide pour des corpus de taille raisonnable (< 100k chunks)
- Index sérialisé et stocké en PostgreSQL (colonne `BYTEA`) → pas de fichier à gérer, rechargement instantané
- Pas de serveur vectoriel supplémentaire à maintenir (pas de Qdrant, Weaviate, etc.)

### Pourquoi PostgreSQL ?

- Persistance des documents, chunks et de l'index FAISS dans une seule base
- Déduplication via `file_hash` (SHA-256) : un fichier déjà ingéré n'est jamais retraité
- Requêtes SQL simples pour lister, filtrer, supprimer des documents

### Modèles utilisés

| Rôle | Modèle | Raison |
|---|---|---|
| Chat / RAG | `qwen2.5:7b` | Bon équilibre vitesse/qualité, multilingue, fonctionne bien en français |
| Embedding | `nomic-embed-text:latest` | Modèle d'embedding open-source de référence, 768 dimensions |
| Vision / OCR | `qwen3-vl:2b` | Léger, rapide, efficace sur le texte dans les images et factures |

---

## Temps de traitement

Les temps varient selon la complexité du document. Mesures indicatives sur **Mac Apple Silicon (M-series)** :

| Opération | Temps approximatif |
|---|---|
| PDF texte simple (10 pages) | 5 – 15 secondes |
| PDF avec tableaux (TableFormer) | 20 – 45 secondes |
| PDF avec images / factures (VLM) | 30 – 90 secondes selon le nombre de figures |
| Embedding d'un chunk | ~1.5 secondes (pause `EMBED_DOC_SLEEP` incluse) |
| Réponse chat (question courte) | 5 – 15 secondes |
| Réponse chat (question complexe) | 15 – 30 secondes |

> Le premier appel d'embedding est plus lent (warmup du modèle). Les suivants sont plus rapides grâce à `keep_alive: -1`.

**Paramètres à ajuster dans `config.py` pour accélérer :**

```python
EMBED_DOC_SLEEP = 1.5   # réduire si votre machine est puissante
CHUNK_SIZE = 2000       # réduire pour moins de tokens par appel
RETRIEVER_K = 4         # réduire pour moins de contexte envoyé au LLM
```

---

## Installation

### Prérequis

- Python 3.11+
- [Ollama](https://ollama.com) installé et en cours d'exécution
- PostgreSQL en local
- (Optionnel) Docker + Docker Compose

### 1. Cloner le projet

```bash
git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
cd VOTRE_REPO
```

### 2. Environnement Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Télécharger les modèles Ollama

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text:latest
ollama pull qwen3-vl:2b
```

### 4. Configurer les variables d'environnement

Créer un fichier `.env` à la racine :

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pdf_chatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe
OLLAMA_URL=http://localhost:11434
```

### 5. Initialiser la base de données

```bash
python -c "from db.connection import init_db; init_db()"
```

---

## Lancement

```bash
streamlit run app.py
```

Ouvrir [http://localhost:8501](http://localhost:8501)

---

## Docker

Ollama et PostgreSQL tournent en local — le conteneur Docker contient uniquement l'application Streamlit.

```bash
docker compose up --build
```
---

## Changer de backend LLM

Tout est centralisé dans **`config.py`** et **`chain/conversation.py`**. Voici les points de modification selon le nouveau backend.

### Passer à l'API Anthropic / OpenAI

**`config.py` :**
```python
# Remplacer
CHAT_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434"

# Par
CHAT_MODEL = "claude-3-5-sonnet-20241022"  # ou "gpt-4o"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
```

**`chain/conversation.py` :**
```python
# Remplacer le LLM Ollama
from langchain_community.llms import Ollama
llm = Ollama(model=CHAT_MODEL, base_url=OLLAMA_URL)

# Par Anthropic
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model=CHAT_MODEL, api_key=ANTHROPIC_API_KEY)

# Ou OpenAI
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
```

**`embeddings/ollama.py` :**
```python
# Remplacer embed_one() par
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

### Passer à vLLM (serveur local OpenAI-compatible)

vLLM expose une API compatible OpenAI — le changement est minimal.

**`config.py` :**
```python
OLLAMA_URL = "http://localhost:8000"  # port vLLM par défaut
CHAT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"  # ou tout modèle HuggingFace
```

**`chain/conversation.py` :**
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model=CHAT_MODEL,
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # vLLM n'exige pas de clé
)
```

**`embeddings/ollama.py` :**  
L'endpoint `/api/embed` est spécifique à Ollama. Avec vLLM, utiliser un modèle d'embedding séparé (ex. `nomic-embed-text` via une instance Ollama dédiée) ou `langchain_huggingface`.

### Tableau récapitulatif

| Fichier | Ollama (défaut) | OpenAI / Anthropic | vLLM |
|---|---|---|---|
| `config.py` | `OLLAMA_URL` | Clé API | URL vLLM |
| `chain/conversation.py` | `Ollama(...)` | `ChatOpenAI` / `ChatAnthropic` | `ChatOpenAI(base_url=...)` |
| `embeddings/ollama.py` | `/api/embed` direct | `OpenAIEmbeddings` | Ollama séparé ou HF |
| `ingestion/converter.py` | `/v1/chat/completions` Ollama | Inchangé si compatible | Inchangé si compatible |


### 4. Captures

![Screenshot](assets/ingestion.png)
![Screenshot](assets/conversation.png)

---

## FAQ
**Q : Puis-je utiliser plusieurs documents à la fois ?**  
R : Oui. Tous les documents ingérés sont indexés ensemble dans FAISS. Le chatbot répond en cherchant dans l'ensemble du corpus.

**Q : Un fichier déjà uploadé est-il retraité ?**  
R : Non. Chaque fichier est haché (SHA-256). S'il existe déjà en base, l'ingestion est ignorée.

**Q : L'index FAISS est-il rechargé à chaque démarrage ?**  
R : Oui, depuis PostgreSQL. L'index est sérialisé en `BYTEA` et désérialisé au lancement — pas de fichier local à gérer.

**Q : Pourquoi `EMBED_DOC_SLEEP = 1.5` secondes entre chaque chunk ?**  
R : Pour éviter de saturer Ollama sur des documents longs. Vous pouvez réduire cette valeur si votre machine le permet.