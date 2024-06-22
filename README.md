# RAGalacticPDF

RAGalacticPDF is an interactive AI assistant embedded within a Retrieval-Augmented Generation (RAG) system, tailored specifically for PDF documents.    
This application allows users to engage with one or several of their PDFs through a conversational AI interface, offering detailed responses to user queries based on document content and chat history.    
The application supports two distinct modes: a conversational mode, which enables interactive discussions with awareness of chat history, and a question mode tailored for straightforward inquiries. Users can also choose between streaming responses in real-time or receiving complete answers at once.     
Users can seamlessly manage their PDFs by uploading new documents directly into the application and organizing them with user-defined tags for easy retrieval. For previously uploaded PDFs, the app provides robust filtering options based on tag requirements, allowing users to refine their selections precisely.     
RAGalacticPDF offers flexibility in information retrieval strategies with options to integrate external knowledge sources for more comprehensive responses or to restrict responses strictly to the content within uploaded PDFs and chat history, ensuring adherence to specific knowledge usage policies.     
Furthermore, the documents used in generating responses are automatically cited in conversation mode, promoting transparency and accountability in information sourcing. It also maintains secure user sessions with unique IDs and encrypted cookies, ensuring data privacy and continuity across sessions.     

## Key Features:

• Interactive PDF Assistant: Engage with your PDF documents through a chatbot interface.

• PDF Management:
    Load New PDFs: 
        - Upload and process new PDF documents directly into the application.
        - Add tags to PDFs upon upload, facilitating organization and retrieval based on user-defined categories.
    Previously Loaded PDFs: 
        - Access and interact with PDFs that have been previously loaded into the system.
        - Filter by Tags:
            All Tags Requirement: Filter PDFs requiring all specified tags for selection.
            Any Tag Requirement: Filter PDFs requiring at least one of the specified tags for selection.

• Conversation Modes: Choose between a conversational mode for interactive discussions (with chat history awareness) or a question mode for straightforward queries.

• Streaming Mode: Choose between real-time streaming of responses or waiting for the answer to come all at once.

• External Knowledge Integration:
    Knowledge Base Usage: Optionally allow the AI to leverage its knowledge base for enhanced response accuracy.
    No Knowledge Base Usage: Strictly limit responses to information contained within uploaded PDFs and chat history.

• Accurate Document Citation: Automatically cite documents used to generate responses, ensuring transparency and traceability of information sources.

• User Authentication: Maintain user sessions with unique user IDs and encrypted cookies.

## Architecture

language: Python    
Frontend: Streamlit for gathering user's options and inputs as well as for building the conversational interface.    
Backend: LlamaIndex as the RAG framework and PDF parsing, Pydantic for data input validation.    
Database: Chroma database for storing embedded nodes.    
    
[app.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/app.py): Main application script to run the Streamlit app.    
[rag.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/rag.py): Contains the RAGalacticPDF class that handles the core RAG functionality built on LlamaIndex.    
[prompt.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/prompt.py): Contains the prompt engeenered templates used by the RAG system (enables various option such as knowledge base usage or not depending on the prompt used).    
[pydantic_valids.py](https://github.com/ValentinOzeel/RAGalactic/blob/main/RAGalacticPDF/src/pydantic_valids.py): Contains the Pydantic validation for PDF file inputs.    
    
The application uses encrypted cookies to manage user sessions.


## Installation and usage

#### Using Poetry

- Install poetry
https://python-poetry.org/docs/

- Clone the repository

        git clone https://github.com/yourusername/RAGalacticPDF.git

- cd to the corresponding folder

        cd Your/Path/To/The/Cloned/RAGalactic/RAGalacticPDF  

- Activate your virtual environment with your favorite environment manager such as venv or conda (or poetry will create one and you will need to add `poetry run` in front of your install command)

- Run the installation process:

        poetry install

- Run the application:

        streamlit run src\app.py --client.showErrorDetails=false




ADD:

INSTALL DOCKER
HOW TO USE + VIDEOS
What could be added/improved ?
LICENCE