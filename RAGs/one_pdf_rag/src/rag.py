# Import modules
import os
import json
import base64
import uuid # For user ID
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from PyPDF2 import PdfFileReader, PdfFileWriter



EVALUATE RAG 



class RAGSinglePDF():
    def __init__(self, pdf_input):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_folder_path = os.path.join(self.project_root, 'data')
        self.db_folder_path = os.path.join(self.project_root, 'chroma_db_data')
        # Ensure the destination directory exists
        for path in [self.data_folder_path, self.db_folder_path]:
            os.makedirs(path, exist_ok=True)
        self.json_ids_path = os.path.join(self.data_folder_path, 'json_ids.json')
        self.app_credentials_path = os.path.join(self.project_root, 'app_credentials', 'app_credentials.yaml')
        
def get_cookie_manager_secret_key():
    OPEN AND LOAD YAML at self.app_credentials_path:
    if 'secret_key' not in credentials:
        WRITE IN YAML credentials_yaml['secret_key'] = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    
    return credentials_yaml['secret_key']

# Get or create a user ID for the current session
def get_user_id(cookies):
    # Check if the user_id cookie is already set
    if "user_id" not in cookies:
        user_id = str(uuid.uuid4())
        cookies["user_id"] = user_id
        cookies.save()
    else:
        user_id = cookies["user_id"]

    return user_id

def get_users_pdf(self, id):
    if os.path.exists(self.json_ids_path):
        with open(self.json_ids_path, 'r') as f:
            json_data = json.load(f)
            return json_data[id]['files'] if json_data.get(id) else None
            
def add_new_json_data(self, id, file_name):
    # Load existing user ids from json file, or create a new dictionary if the file does not exist
    if os.path.exists(self.json_ids_path):
        with open(self.json_ids_path, 'r') as f:
            json_data = json.load(f)
    else:
        json_data = {}
        
    # Create ID entry if doesnt exists
    if not json_data.get(id):
        json_data[id] = {'files': [file_name]}
    # Add file to ID's files if file not in ID's files already
    elif file_name not in json_data[id]['files']:
        json_data[id]['files'].append(file_name)

    # Write the updated data back to the JSON file
    with open(self.json_ids_path, 'w') as f:
        json.dump(json_data, f, indent=4)






    def load_pdf(name:str):
        if name:
            
            if os.path.isfile()
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