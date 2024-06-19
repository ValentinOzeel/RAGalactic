# Import modules
import os
import json

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_parse import LlamaParse
from llama_index.core.extractors import (TitleExtractor, QuestionsAnsweredExtractor, SummaryExtractor, 
                                         QuestionsAnsweredExtractor, TitleExtractor, KeywordExtractor)
from llama_index.extractors.entity import EntityExtractor
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.core import PromptTemplate

import chromadb
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters, FilterCondition

from prompt import (PROMPT_NO_KNOWLEDGE_BASE, PROMPT_WITH_KNOWLEDGE_BASE,
                    text_qa_template_str, refine_template_str,
                    text_qa_template_str_no_knowledge_base, refine_template_str_no_knowledge_base)


import torch

import nest_asyncio
nest_asyncio.apply()

from typing import Dict, Tuple, List

import logging
#logging.basicConfig(level=logging.DEBUG)
#logging.debug('This is a debug message')
#logging.info('This is an info message')
#logging.warning('This is a warning message')
#logging.error('This is an error message')
#logging.critical('This is a critical message')

class RAGalacticPDF():
    def __init__(self):
        
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_folder_path = os.path.join(self.project_root, 'data')
        self.db_folder_path = os.path.join(self.project_root, 'chroma_db_data')
        # Ensure the destination directory exists
        for path in [self.data_folder_path, self.db_folder_path]:
            os.makedirs(path, exist_ok=True)
            
        self.json_ids_path = os.path.join(self.data_folder_path, 'json_ids.json')
        self.app_credentials_path = os.path.join(self.project_root, 'app_credentials', 'app_credentials.yaml')


        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.llm = Ollama(model="llama3", request_timeout=200.0, )
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5", device=self.device)
        self._init_llm_and_embedd_models()
        
        self.parser = self._get_parser()
        self.llm_mode, self.streaming = None, None
        self.chat_history = []
        
        self.user_id = None
        self.chroma_client = self._get_chromadb_client()
        self.chroma_collection, self.vector_store, self.storage_context = None, None, None

        self.use_custom_transforms = False
        
        self.custom_transforms = [
                SentenceSplitter(separator=" ", chunk_size=1024, chunk_overlap=128),
                SummaryExtractor(summaries=["prev", "self", "next"]), # automatically extracts a summary over a set of Nodes
                QuestionsAnsweredExtractor(questions=3), # extracts a set of questions that each Node can answer
                TitleExtractor(nodes=5), # extracts a title over the context of each Node
                EntityExtractor(device=self.device), # - extracts entities (i.e. names of places, people, things) mentioned in the content of each Node
                KeywordExtractor(),
                self.embed_model,
            ]
        
        # Context prompt for chat engine
        self.context_prompt = None
        # Context prompt for query engine
        self.text_qa_template = None
        self.refine_template = None
        # Engine parameters
        self.similarity_top_k=3 
        self.chat_mode='condense_plus_context'

    def _init_llm_and_embedd_models(self):
        # Initialize llm and ServiceContext
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

    def set_user_id(self, user_id):
        self.user_id = user_id 
        # Set up database corresponding to the user_id
        self.chroma_collection, self.vector_store, self.storage_context = self._get_chromadb_setup()
        
    def _set_engine_feature(self, engine_mode, llm_knowledge_base, streaming):
        self.llm_mode, self.streaming = engine_mode, streaming
        if llm_knowledge_base:
            self.context_prompt = PROMPT_WITH_KNOWLEDGE_BASE
            self.text_qa_template = PromptTemplate(text_qa_template_str)
            self.refine_template = PromptTemplate(refine_template_str)
        else:
            self.context_prompt = PROMPT_NO_KNOWLEDGE_BASE
            self.text_qa_template = PromptTemplate(text_qa_template_str_no_knowledge_base)
            self.refine_template = PromptTemplate(refine_template_str_no_knowledge_base)
        
        if self.llm_mode == 'Conversation':
            self.manage_chat_history(create_or_reset=True)
        
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
        
    def _get_chromadb_setup(self):
        if not self.user_id:
            raise ValueError('User need to set self.user_id first (set_user_id(user_id) method) before to access/create the corresponding database setup.')
        # Check if the collection already exists
        collection_names = [getattr(collection_obj, 'name') for collection_obj in self.chroma_client.list_collections()]
        # Get preexisting collection or create one if does not exist yet
        chroma_collection = self.chroma_client.get_collection(name=self.user_id) if self.user_id in collection_names else self.chroma_client.create_collection(name=self.user_id)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return chroma_collection, vector_store, storage_context 



    ###               ###
    ### LOAD NEW PDFS ###
    ###               ###

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
            #file_metadata= lambda filepath: {'file_name': os.path.basename(filepath), 'tags': tags}, 
            file_extractor={".pdf": self.parser}
        ).load_data()
        
    def _add_metadata(self, docs, file_name:str, tags:List[Dict]=None):
        for document in docs:
            document.metadata["file_name"] = file_name
            for dict_tag in tags:
                # Single entry dict
                tag_name = next(iter(dict_tag.keys()))
                document.metadata[tag_name] = dict_tag[tag_name]
        return docs

    def _create_nodes(self, docs):
        pipeline = IngestionPipeline(
            transformations=self.custom_transforms,
        )
        return pipeline.run(documents=docs)  
        
    def _create_index(self, docs):
        if not self.use_custom_transforms:
            return VectorStoreIndex.from_documents(docs, storage_context=self.storage_context)
        else:
            return VectorStoreIndex(nodes=self._create_nodes(docs), storage_context=self.storage_context)
        

    def _add_new_json_data(self, file_name:str, tags:List[Dict]=None):
        # Load existing user ids from json file, or create a new dictionary if the file does not exist
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
        else:
            json_data = {}

        # Create ID entry if doesnt exists
        if not json_data.get(self.user_id):
            json_data[self.user_id] = {'files': [file_name], 'tags': [tags]}
        # Add file to ID's files if file not in ID's files already
        elif file_name not in json_data[self.user_id]['files']:
            json_data[self.user_id]['files'].append(file_name)
            json_data[self.user_id]['tags'].append(tags)
        # Write the updated data back to the JSON file
        with open(self.json_ids_path, 'w') as f:
            json.dump(json_data, f, indent=4)
             
    def _check_already_loaded(self, pdf_input:str):
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
            
            if json_data.get(self.user_id, None):
                return True if pdf_input.name in json_data[self.user_id]['files'] else False
            else:
                return False
        
    def load_new_pdf(self, pdf_input, tags:List[Dict]=None):
        # If already loaded previously, then use pre-loaded
        if self._check_already_loaded(pdf_input):
            return self.load_existing_pdf([pdf_input.name])
        # Temp save the pdf
        temp_path = self._temp_save_pdf(pdf_input, dir_path=self.data_folder_path)
        # Parse pdf (temp saved in dir self.data_folder_path)
        docs = self._parse_pdf(dir_path=self.data_folder_path)
        # Add metadata
        docs = self._add_metadata(docs, file_name=pdf_input.name, tags=tags)
        # Create vector indexing and save it in database
        index = self._create_index(docs)
        # Delete temp pdf
        self._delete_temp_pdf(temp_path)
        # Add input pdf name to corresponding user ID in 
        self._add_new_json_data(file_name=pdf_input.name, tags=tags)
        # Create engine
        return self._create_corresponding_engine(index)

        
        
        
        
    ###                        ###
    ### PREVIOUSLY LOADED PDFS ###
    ###                        ###
    
    def get_user_pdfs(self, tagged_with_all:List[str]=None, tagged_with_at_least_one:List[str]=None):
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
                
                if not json_data.get(self.user_id):
                    return None
                
                # If there is no tag passed to the method, return all file names
                if not tagged_with_all and not tagged_with_at_least_one:
                    return sorted(json_data[self.user_id]['files'])
                
                if json_data.get(self.user_id):
                    files = json_data[self.user_id]['files']
                    tags = json_data[self.user_id]['tags']
                    # if tagged_with_all: Get all file names where every tag {tag_name:tag} in 'tagged_with_all' is present in the corresponding 'file_tags'.
                    # if tagged_with_at_least_one: Get all file names where at least one tag {tag_name:tag} in 'tagged_with_at_least_one' is present in the corresponding 'file_tags'
                    # - The 'zip(files, tags)' pairs each file with its associated tags.
                    # - The 'all(tag_dict in file_tags for tag_dict in tagged_with_all)' checks if all tag dicts in 'tagged_with_all' are in the current 'file_tags' tag dict list.
                    # - The 'any(tag_dict in file_tags for tag_dict in tagged_with_all)' checks if at least tag dict in 'tagged_with_at_least_one' are in the current 'file_tags' tag dict list.
                    return sorted([
                        file for file, file_tags in zip(files, tags) if all(tag_dict in file_tags for tag_dict in tagged_with_all)
                        ]) if tagged_with_all else sorted([
                            file for file, file_tags in zip(files, tags) if any(tag_dict in file_tags for tag_dict in tagged_with_at_least_one)
                            ]) if tagged_with_at_least_one else None
                        
                        
    # Method to extract sorting metrics (key, value) from each single entry dictionary. 
    # To be used for sorting according to key first and then value
    def _sort_key(self, dictionnary):
        key, value = next(iter(dictionnary.items()))
        return (key, value)


    def get_users_tags(self):
        if os.path.exists(self.json_ids_path):
            with open(self.json_ids_path, 'r') as f:
                json_data = json.load(f)
                # Extract and flatten single-entry dictionaries from the nested lists in json_data[self.user_id]['tags'] list,
                # convert each dictionary to a tuple to ensure uniqueness with a set,
                # and then convert the unique tuples back to single-entry dictionaries.
                all_unique_tags = [
                    {tag_name: tag} for tag_name, tag in set(tuple(single_entry_dict.items())[0] for tag_dict_list in json_data[self.user_id]['tags'] for single_entry_dict in tag_dict_list)
                    ] if (json_data[self.user_id].get('tags') and json_data[self.user_id]['tags']) else None

                # Return list of single entry dict (list sorted by dict key first and then by dict value) or None
                return sorted(all_unique_tags, key=self._sort_key) if all_unique_tags else None
        
    def _get_index(self, vector_store):
        return VectorStoreIndex.from_vector_store(vector_store)

    def load_existing_pdf(self, pdf_names):
        ## Load existing index from database
        index = self._get_index(self.vector_store)
        
        filter_list = [MetadataFilter(key="file_name", value=pdf_name) for pdf_name in pdf_names]
        filters = MetadataFilters(filters=filter_list, condition=FilterCondition.OR)
        
        logging.debug(f'FILTERRRRRRS: {filters}')
        
        # Create query engine
        return self._create_corresponding_engine(index, filters=filters)

    




    ###                    ###
    ### GET CHATBOT ENGINE ###
    ###                    ###

    def _create_corresponding_engine(self, index, filters=None):
        if self.llm_mode == 'Conversation':
            return self._create_chat_engine(index, filters)
        else:
            return self._create_query_engine(index, filters)

    def _create_chat_engine(self, index, filters):    
        return index.as_chat_engine(chat_mode=self.chat_mode, 
                                    streaming=self.streaming,
                                    memory= ChatMemoryBuffer.from_defaults(
                                                 token_limit=10000,
                                                 chat_history=self.chat_history,
                                             ),
                                    context_prompt=self.context_prompt,
                                    # Retriever params
                                    similarity_top_k=self.similarity_top_k,
                                    filters=filters,
                                    verbose=False,                            
                                    )
            
    def _create_query_engine(self, index, filters):
        return index.as_query_engine(similarity_top_k=self.similarity_top_k, 
                                     text_qa_template=self.text_qa_template, refine_template=self.refine_template,
                                     streaming=self.streaming, 
                                     filters=filters
                                     )
        
    def run_query(self, query_engine, query_text:str):
        return query_engine.query(query_text)
 
    def run_chat(self, chat_engine, prompt:str):
        return chat_engine.stream_chat(prompt) if self.streaming else chat_engine.chat(prompt)
    

    def manage_chat_history(self, create_or_reset:bool=False, to_append:Tuple=()):
        if create_or_reset:
            self.chat_history = []
        if to_append and isinstance(to_append, Tuple):
            self.chat_history.append(ChatMessage(role=to_append[0], content=to_append[1])) 