# Import modules
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from PyPDF2 import PdfFileReader, PdfFileWriter


MAKE CLASS 
EVALUATE RAG 
MAKE API/STREAMLIT APP

class RAGSinglePDF():
    def __init__(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_folder_path = os.path.join(self.project_root, 'data')
        self.db_folder_path = os.path.join(self.project_root, 'chroma_db_data')
        # Ensure the destination directory exists
        for path in [self.data_folder_path, self.db_folder_path]:
            os.makedirs(path, exist_ok=True)

        
    def save_input_pdf(self, pdf_file_or_path, name:str):
        try:        
            reader = PdfReader(pdf_file_or_path)
            writer = PdfWriter()
            # Add all pages from the reader to the writer
            for page_num in range(len(reader.pages)):
                writer.add_page(reader.pages[page_num])
            # Write the content to the destination PDF file
            with open(os.path.join(self.data_folder_path, name), 'wb') as output_file:
                writer.write(output_file)
        
        except Exception as e:
            print(e)

    def load_pdf(names:List=None):
        if names:
            
            CHECK IF FILES EXISTS BEFORE LOAD 
            THEN USE SimpleDirectoryReader(input_files=[xxx, yyy])
        
        else:
            USE SimpleDirectoryReader(input_dir=XXXX, required_exts=['.pdf'])
            

        
name_file_wo_ext = 'intro_quantum_mechs'
extension = '.pdf'
file_name = ''.join([name_file_wo_ext, extension])


# Load a PDF with llama index SimpleDirectoryReader
loader = SimpleDirectoryReader(
    input_files=[data_path]
)
doc_quantum_intro = loader.load_data()
print(f"Loaded {len(doc_quantum_intro)} docs from {file_name}\n")

# Create Chroma DB client and store
client = chromadb.PersistentClient(path=db_path)
# Check if the collection already exists
collection_names = [getattr(collection_obj, 'name') for collection_obj in client.list_collections()]
if name_file_wo_ext in collection_names:
    chroma_collection = client.get_collection(name=name_file_wo_ext)
    print(f"Using existing collection: {name_file_wo_ext}")
else:
    chroma_collection = client.create_collection(name=name_file_wo_ext)
    print(f"Created new collection: {name_file_wo_ext}")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
print('Chroma db initialized.\n')
    
# Initialize Ollama and ServiceContext
llm = Ollama(model="llama3", request_timeout=200.0)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = llm
Settings.embed_model = embed_model
print('Llama3 and embedding model succesfully loaded.\n')

# Create VectorStoreIndex and query engine
index = VectorStoreIndex.from_documents(doc_quantum_intro, storage_context=storage_context, embed_model=embed_model)
query_engine = index.as_query_engine(llm=llm)
print('Query engine initialized.\n')

# Perform a query and print the response
response = query_engine.query("As bulletpoints, what are the main takeaways of the document ?")
print(response)