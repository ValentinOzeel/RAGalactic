# Import modules
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore


name_file_wo_ext = 'intro_quantum_mechs'
extension = '.pdf'
file_name = ''.join([name_file_wo_ext, extension])
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_root, 'data', file_name)
db_path = os.path.join(project_root, 'chroma_db_data')


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
response = query_engine.query("What are the main takeaways of the document ?")
print(response)