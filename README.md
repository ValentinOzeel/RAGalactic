# RAGalactic

**RAGalactic** is an interactive AI assistant embedded within a **Retrieval-Augmented Generation** (_RAG_) system, tailored for _PDF_ documents. This application allows users to engage with one or several of their PDFs through a _conversational AI interface_, offering detailed responses to user queries based on _document content and chat history_.    
    
The application, which runs completely **locally**, maintains secure _user specific sessions_ with unique IDs and encrypted cookies, ensuring continuity across sessions.     
It supports two distinct modes: a _conversational mode_, which enables interactive discussions with awareness of chat history, and a _question mode_ tailored for straightforward inquiries.     
Users can seamlessly manage their PDFs by _uploading new documents_ directly into the application and organizing them with **user-defined tags** for easy retrieval.     
With regards to _previously uploaded PDFs_, the app provides robust **filtering options based on tag requirements**, allowing users to _refine their document selections_ precisely before to interact with the RAG system.   
Furthermore, _documents used in generated responses_ are **automatically cited** in conversation mode, promoting transparency in _information sourcing_.     
**RAGalactic** offers flexibility in information retrieval strategies with options to **integrate LLM knowledge base** for more comprehensive responses or to **restrict responses** strictly to the **content within uploaded PDFs and chat history**. Users can also choose between **streaming responses** in real-time or receiving complete answers at once.       
        

## Key Features:

• **Interactive PDF Assistant running locally**: Engage with your PDF documents through a chatbot interface running locally on your machine.

• **PDF Management**:
1. *Load New PDFs*:    
    - Upload and process new PDF documents directly into the application.    
    - Add tags to PDFs upon upload, facilitating organization and retrieval based on user-defined categories.    
2. *Previously Loaded PDFs*:    
    - Access and interact with PDFs that have been previously loaded into the system.    
    - Filter by Tags:    
        - All Tags Requirement: Filter PDFs requiring all specified tags for selection.    
        - Any Tag Requirement: Filter PDFs requiring at least one of the specified tags for selection.     

• **Conversation Modes**: Choose between a conversational mode for interactive discussions (with chat history awareness) or a question mode for straightforward queries.

• **Streaming Mode**: Choose between real-time streaming of responses or waiting for the answer to come all at once.

• **External Knowledge Integration** (through prompt engeenering):
    *Knowledge Base Usage*: Optionally allow the AI to leverage its knowledge base for enhanced response accuracy.
    *No Knowledge Base Usage*: Strictly limit responses to information contained within uploaded PDFs and chat history.

• **Accurate Document Citation** (through prompt engeenering): Cite the documents used to generate responses, ensuring transparency and traceability of information sources.

• **User Authentication**: Maintain user sessions with unique user IDs and encrypted cookies.

## App demo

https://github.com/ValentinOzeel/RAGalactic/assets/117592568/791b2a9d-083f-4633-8e25-5649a9f4a88f

Disclosure: Some parts of the video have been slightly edited (cuts and video speed augments) notably when the LLM response is generating. App running locally on PC (GPU: NVIDIA GeForce GTX 1660 Ti).     
     
***0-0.26***: Load first pdf (waves_quantum.pdf) related to general quantum mechanics with tags (we could then directly talk to this document).     
***0.26-0.42***: Load second pdf (quantum-computing.pdf) with appropriate tags.     
***0.42-1.15***: Select previously loaded pdfs to talk, with possibility to filter based on tags.      
***1.15-2.24***: Exemple of a query needing information from different documents (with accurate listing of used documents).      
***2.24-3.43***: Exemple of custom instruction (answer in one sentence) and citation of the corresponding document covering the question (despite having selected all previously loaded document option). Then ask for more details about the question.         
***3.43-4.51***: RAG response without activating LLM's pre-existing knowledge base VS with LLM's knowledge option activated.     

## Architecture

Running in **virtual environment through poetry** or running as a **contenerized app with Docker/Docker-compose** (multi-services, multi-containers including RAGalactic app, ollama and genai ollama model auto pulling containers).

_language_: **Python**   
_Frontend_: **Streamlit** for gathering user's options and inputs as well as for building the conversational LLM interface. The application uses encrypted cookies to manage user sessions.   
_Backend_: **LlamaIndex** as the RAG framework and PDF parsing tool, **Pydantic** for data input validation.    
_Database_: **Chroma database** for storing user's embedded nodes.   
_LLM_: Currently **llama3** through **ollama** (`self.llm` attribute can be modified in [rag.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/rag.py)) 
_Embeddings model_: Currently **BAAI/bge-small-en-v1.5** through **HuggingFace** (`self.embed_model` attribute can be modified in [rag.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/rag.py))

    
[app.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/app.py): Main application script to run the Streamlit app.    
[rag.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/rag.py): Contains the RAGalacticPDF class that handles the core RAG functionality built on LlamaIndex.    
[prompt.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/prompt.py): Contains the prompt engeenered templates used by the RAG system (enables various option such as knowledge base usage or not depending on the prompt used, citation of used document to provide the user with an answer etc...).    
[pydantic_valids.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/pydantic_valids.py): Contains the Pydantic validation for PDF file inputs.    
    


## Installation and usage

Start by visiting https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/ to get an API key for LlamaParse (used to parse the .pdf files).     
Then set the API key as the environmment variable **LLAMA_CLOUD_API_KEY**.    


#### Using Poetry

- Install poetry:
https://python-poetry.org/docs/

- Install ollama:
https://ollama.com/download

- Pull the used model (llama3, 8b parameter version):

        ollama run llama3

- Clone the RAGalactic repository:

        git clone https://github.com/ValentinOzeel/RAGalactic.git

- cd to the corresponding folder:

        cd Your/Path/To/The/Cloned/RAGalactic  

- Activate your virtual environment with your favorite environment manager such as venv or conda (or poetry will create one and you will need to add `poetry run` in front of your install command)

- Run the installation process:

        poetry install

- Run the application:

        streamlit run RAGalacticPDF/src/app.py --client.showErrorDetails=false


#### Using Docker

- You need a cuda-enabled GPU and the cuda container toolkit available on your machine:
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

- Docker related installs:
    - Docker: https://docs.docker.com/engine/install/
    - Docker desktop: https://docs.docker.com/desktop/install/windows-install/
    - Docker compose: https://docs.docker.com/compose/install/

- Clone the RAGalactic repository:

        git clone https://github.com/ValentinOzeel/RAGalactic.git

- cd to the corresponding folder:

        cd Your/Path/To/The/Cloned/RAGalactic 

- Create an .env file (based on [.env_exemple](https://github.com/ValentinOzeel/RAGalactic/blob/main/.env_exemple) template) and add your LLAMA_CLOUD_API_KEY API key.

- Build the RAGalactic image and start all the services defined in the docker-compose file:

        docker compose up --build


## What could be improved

- Trying other models regarding both the llm used (currently llama3 through ollama) and embeddings (currently BAAI/bge-small-en-v1.5 through HuggingFace).

- Potentially let the user choose the llm and embedding models.

- Could use another database such as Milvus, a GPU-optimized vector database, which also allow for Hybrid Search (combining keyword-based search with vector/semantic search), a technique not usable with Chroma db.

- Use other advanced capabilities such as implementing postnodeprocessor for nodes reranking upon retrieval.

- Currently, only .pdf files are accepted. Other document types could be used (not tested) by modifying the `required_exts` and `file_extractor` kwargs in the following code in [rag.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/rag.py):

        def _parse_pdf(self, dir_path:str):
            return SimpleDirectoryReader(
                dir_path,
                required_exts=[".pdf"],
                filename_as_id=True,
                #file_metadata= lambda filepath: {'file_name': os.path.basename(filepath), 'tags': tags}, 
                file_extractor={".pdf": self.parser}
            ).load_data() 

- We could add the ability for the user to remove previously uploaded documents.



