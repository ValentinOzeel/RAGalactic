# Import modules
import os
import json
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_parse import LlamaParse
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters

import nest_asyncio
nest_asyncio.apply()




# EVALUATE RAG 










class RAGSinglePDF():
    def __init__(self, user_id):
        
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_folder_path = os.path.join(self.project_root, 'data')
        self.db_folder_path = os.path.join(self.project_root, 'chroma_db_data')
        # Ensure the destination directory exists
        for path in [self.data_folder_path, self.db_folder_path]:
            os.makedirs(path, exist_ok=True)
            
        self.json_ids_path = os.path.join(self.data_folder_path, 'json_ids.json')
        self.app_credentials_path = os.path.join(self.project_root, 'app_credentials', 'app_credentials.yaml')

        self.llm = Ollama(model="llama3", request_timeout=200.0)
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self._init_llm_and_embedd_models()
        
        self.parser = self._get_parser()
        self.memory, self.streaming = None, None
        
        self.user_id = user_id
        self.chroma_client = self._get_chromadb_client()

    
    def _init_llm_and_embedd_models(self):
        # Initialize llm and ServiceContext
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

    def _set_engine_feature(self, engine_memory, streaming):
        self.memory, self.streaming = engine_memory, streaming
         
        
    def _get_parser(self):
        return LlamaParse(
            api_key=os.environ.get('LLAMA_CLOUD_API_KEY'),
            result_type="markdown",  # "markdown" and "text" are available
            num_workers=4,  # if multiple files passed, split in `num_workers` API calls
            verbose=True,
            language="en",  # Optionally you can define a language, default=en
            )
        
    def _get_chromadb_client(self):
        # Create Chroma DB client and store
        return chromadb.PersistentClient(path=self.db_folder_path)
        
    
    def _get_chromadb_setup(self, pdf_name):
        target_name = '_'.join([self.user_id, pdf_name])
        # Check if the collection already exists
        collection_names = [getattr(collection_obj, 'name') for collection_obj in self.chroma_client.list_collections()]
        # Get preexisting collection or create one if does not exist yet
        chroma_collection = self.chroma_client.get_collection(name=target_name) if target_name in collection_names else self.chroma_client.create_collection(name=target_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        return chroma_collection, vector_store, storage_context 
    
    
    

    def _create_corresponding_engine(self, index, top_k=5, chat_mode='condense_plus_context'):
        if self.memory:
            return self._create_chat_engine(index, chat_mode, self.streaming)
        else:
            return self._create_query_engine(index, top_k, self.streaming)
        
            
    def _create_query_engine(self, index, top_k:int, streaming:bool):
        return index.as_query_engine(similarity_top_k=top_k, streaming=streaming)
    
    def _create_chat_engine(self, index, chat_mode:str, streaming:bool):
        return index.as_chat_engine(chat_mode=chat_mode, streaming=streaming)

 


    def _temp_save_pdf(self, pdf_input, dir_path:str):
        # Save the uploaded PDF file temporarily
        temp_pdf_path = os.path.join(dir_path, pdf_input.name)
        with open(temp_pdf_path, 'wb') as temp_pdf:
            temp_pdf.write(pdf_input.getvalue())
        return temp_pdf_path

    def _delete_temp_pdf(self, temp_pdf_path:str):
        # Delete the file after performing the action
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

    def _parse_pdf(self, dir_path:str):
        return SimpleDirectoryReader(
            dir_path,
            required_exts=[".pdf"],
            filename_as_id=True,
            #file_metadata= lambda filepath: {'file_name': os.path.basename(filepath)}, 
            file_extractor={".pdf": self.parser}
        ).load_data()

    def _create_index(self, docs, storage_context):
        # Create VectorStoreIndex and save it with a specific document ID
        return VectorStoreIndex.from_documents(docs, storage_context=storage_context)
    
    
    
 
    def _add_new_json_data(self, file_name):
        # Load existing user ids from json file, or create a new dictionary if the file does not exist
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
        else:
            json_data = {}

        # Create ID entry if doesnt exists
        if not json_data.get(self.user_id):
            json_data[self.user_id] = {'files': [file_name]}
        # Add file to ID's files if file not in ID's files already
        elif file_name not in json_data[self.user_id]['files']:
            json_data[self.user_id]['files'].append(file_name)

        # Write the updated data back to the JSON file
        with open(self.json_ids_path, 'w') as f:
            json.dump(json_data, f, indent=4)
             
    def load_new_pdf(self, pdf_input):
        _, _, storage_context = self._get_chromadb_setup(pdf_input.name)
        # Temp save the pdf
        temp_path = self._temp_save_pdf(pdf_input, dir_path=self.data_folder_path)
        # Parse pdf (temp saved in dir self.data_folder_path)
        docs = self._parse_pdf(dir_path=self.data_folder_path)
        # Create vector indexing and save it in database
        index = self._create_index(docs, storage_context)
        # Add input pdf name to corresponding user ID in 
        self._add_new_json_data(file_name=pdf_input.name)
        # Delete temp pdf
   #     self._delete_temp_pdf(temp_path)
        # Create engine
        return self._create_corresponding_engine(index)


    
        


        
    def get_users_pdf(self):
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
                return json_data[self.user_id]['files'] if json_data.get(self.user_id) else None  
        
    def _get_index(self, vector_store):
        return VectorStoreIndex.from_vector_store(vector_store)

        
    def load_existing_pdf(self, pdf_name):
        ## Load existing index for a document from database
        _, vector_store, _ = self._get_chromadb_setup(pdf_name)
        index = self._get_index(vector_store)
        # Create query engine
        return self._create_corresponding_engine(index)

    
    
    
        
    def run_query(self, query_engine, query_text:str):
        return query_engine.query(query_text)
 
    def run_chat(self, chat_engine, prompt:str):
        return chat_engine.stream_chat(prompt) if self.streaming else chat_engine.chat(prompt)
    

         