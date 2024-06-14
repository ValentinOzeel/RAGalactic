import os
import yaml 
import base64
import uuid # For user ID

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from pydantic_valids import validate_pdf_input
from rag import RAGSinglePDF

from typing import List, Dict, Tuple
import logging
logging.basicConfig(level=logging.DEBUG)
    
logging.debug(f'CHECK MAIN')


from llama_index.core.llms import ChatMessage


# Create instance of RAGSinglePDF class
RAG_CLS_INST = RAGSinglePDF()


class RAGPDFapp():
    def __init__(self):
        st.sidebar.title("RAGalactic")
        st.sidebar.write("This app enables you to talk to your favorite PDFs.")
        st.title('Welcome to RAGalactic!')
        
        # Get the cookie manager key
        secret_key = self._get_cookie_manager_secret_key()
        # Create a cookie manager
        cookies = EncryptedCookieManager(prefix="streamlit_", password=secret_key)
        if not cookies.ready():
            st.stop()
        # Retrieve or create the user ID
        self.user_id = self._get_user_id(cookies)
        # Add user ID as a query parameter in the URL
        st.query_params.user_id = self.user_id
        # Initialize messages in session_state
        self._init_messages()
        self._init_llama_index_chat_history()

        # Set user_id in RAG_CLS_INST
        RAG_CLS_INST._set_user_id(self.user_id)
        
        
        logging.debug(f'CLASS INIT')
        self.memory, self.streaming = None, None
        self.input_source = None 
        self.pdf_input, self.tags_pdf_input = None, None
        self.selected_pdfs = None 

        
        with st.sidebar:
            self.ask_app_parameters()
            self.ask_input()
        self.run_chatbot()
        
        
    def reset_attributes(self, attr_str_list:List[str]):
        for attr in attr_str_list:
            if hasattr(self, attr):                
                setattr(self, attr, None)
         
                 
    def _get_cookie_manager_secret_key(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        cred_path = os.path.join(root, 'app_credentials', 'app_credentials.yaml')
        
        with open(cred_path, 'r') as file:
            credentials = yaml.safe_load(file)
        
        if credentials and credentials.get('secret_key'):
            secret_key = credentials['secret_key']
        else:
            secret_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
            # Write the secret key in the cred file  
            with open(cred_path, 'w') as outfile:
                yaml.dump({'secret_key': secret_key}, outfile, default_flow_style=False)
        return secret_key
    
    # Get or create a user ID for the current session
    def _get_user_id(self, cookies):
        # Check if the user_id cookie is already set
        if "user_id" not in cookies:
            user_id = str(uuid.uuid4())
            cookies["user_id"] = user_id
            cookies.save()
        else:
            user_id = cookies["user_id"]
        return user_id[:20]
    
    
    def _init_messages(self):
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    def _init_llama_index_chat_history(self):
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        

    def ask_app_parameters(self):
        logging.debug(f'ASK PARAMS')
        self._ask_engine_features()
        self._ask_new_or_previously_loaded()

    def _ask_engine_features(self):
        self.memory = st.radio("LLM memory:", (False, True), on_change=self._empty_chat_and_set_engine_features_callback, horizontal=True)
        self.streaming = st.radio("LLM response streaming:", (False, True), on_change=self._empty_chat_and_set_engine_features_callback, horizontal=True)
           
    def _ask_new_or_previously_loaded(self):
        # Option to select input source
        self.input_source = st.radio("Select input source:", ('load_new_pdf', 'previously_loaded_pdf'), on_change=self._ask_input_callback)

    def _empty_chat_and_set_engine_features_callback(self):
        st.session_state.messages = []
        RAG_CLS_INST._set_engine_feature(self.memory, self.streaming)

    def _ask_input_callback(self):
        st.session_state.messages = []
        self.ask_input()
        
    
    #@st.experimental_fragment
    def ask_input(self):
        logging.debug(f'ASK INPUT')
        if self.input_source == 'load_new_pdf':
            self._ask_pdf_input_and_tags()

        # If user already loaded pdf in the past, talk to preexiting embbedings
        elif self.input_source == 'previously_loaded_pdf':
            all_pdfs = RAG_CLS_INST.get_user_pdfs()

            # If not, user needs to upload a pdf, carry out embbedings etc..
            if not all_pdfs:
                st.write('You currently do not have loaded any pdf yet.')
                self._ask_pdf_input_and_tags()
                
            # Else we can select previously loaded pdfs
            else:
                self._pdf_selection_parameter()
                   
                   
                   
            #CHANGE THE CALLBACKSSSSSSSSS !!!!
            #RESET self.pdf_select_param and other attributes AFTER USAGE
            

            if self.pdf_select_param:
                if self.pdf_select_param == 'show_all_pdf_names':
                    self._ask_all_previously_loaded_pdfs(all_pdfs)
                   
                else:
                    all_tags = RAG_CLS_INST.get_users_tags()
                    if not all_tags: 
                        st.write('You currently do not have loaded pdf assiocated with a tag yet.')
                        self._pdf_selection_parameter()
                        
                    selected_tags = self._ask_which_tags(all_tags)
                    files_with_selected_tags = RAG_CLS_INST.get_user_pdfs(tagged_with=selected_tags)
                    
                    if self.pdf_select_param == 'filter_pdf_with_tag':
                        self._ask_previously_loaded_pdfs_with_tags(files_with_selected_tags)

                    elif self.pdf_select_param == 'get_all_pdfs_with_tags':
                        self.selected_pdfs = files_with_selected_tags 


    def _run_chatbot_callback(self):
        st.session_state.messages = []
        self.run_chatbot()
        
    def _pdf_selection_parameter(self):
        self.pdf_select_param = st.selectbox('Select a PDF selection parameter:', ['show_all_pdf_names', 'filter_pdf_with_tag', 'get_all_pdfs_with_tags'])
        
    def _ask_all_previously_loaded_pdfs(self, pdfs):
        self.selected_pdfs = st.multiselect("Select -at least- one pre-existing PDF", pdfs, on_change=self._run_chatbot_callback)
    
    def _ask_which_tags(self, all_tags):
        return st.multiselect("Select -at least- one tag", all_tags, on_change=self._run_chatbot_callback)

    def _ask_previously_loaded_pdfs_with_tags(self, files_with_selected_tags):
        self.selected_pdfs = st.multiselect("Select -at least- one pre-existing PDF (presented PDFs have all been tagged with the tags you selected)", files_with_selected_tags, on_change=self._run_chatbot_callback)
        
    def _ask_pdf_input_and_tags(self):
        tag_separator = '//'
        
        y_or_n = st.radio('Do you want to add a tag to your PDF ?', ['no', 'yes'], horizontal=True)
        if y_or_n == 'yes':
            tag_str = st.text_input(f"Please enter the desired tag(s) for your PDF. Format for multiple tags: 'tag1{tag_separator}tag2{tag_separator}tag3'")            
            self.tags_pdf_input = tag_str.split(tag_separator) if tag_separator in tag_str else [tag_str]

        self.pdf_input = st.file_uploader("Please upload your PDF file (file name, including extention, should be <= 42 caracters)", type="pdf", on_change=self._run_chatbot_callback)

    





    def run_chatbot(self):
        if self.input_source == 'load_new_pdf':
            self.load_new_pdf()
        elif self.input_source == 'previously_loaded_pdf':
            self.previously_loaded_pdf()      
            
    def load_new_pdf(self):
        if self.pdf_input:
            # Validate pdf input through pydantic
            validate_pdf_input(self.pdf_input)
            engine = RAG_CLS_INST.load_new_pdf(self.pdf_input, tags=self.tags_pdf_input)
            self.reset_attributes(['pdf_input', 'tags_pdf_input'])
            self._chat_with_pdf(engine)
    
    def previously_loaded_pdf(self):
        logging.debug(f'PREVIOUSLY LOADED PDF FOR CHAT')
        if self.selected_pdfs:
            engine = RAG_CLS_INST.load_existing_pdf(self.selected_pdfs)   
            self.reset_attributes(['selected_pdfs'])  
            self._chat_with_pdf(engine)
        
    def _chat_with_pdf(self, engine):
        logging.debug(f'HISTORY: {RAG_CLS_INST.chat_history}')
        if prompt := st.chat_input("You can now start chatting with your PDF."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                if prompt:
                    rag_response = RAG_CLS_INST.run_chat(engine, prompt) if self.memory else RAG_CLS_INST.run_query(engine, prompt)
                    response = st.write_stream(rag_response.response_gen) if self.streaming else st.markdown(rag_response.response)
                    
            self._add_to_chat_history('user', str(prompt))
            self._add_to_chat_history('system', str(rag_response.response))
            st.session_state.messages.append({"role": "assistant", "content": response})

    def _add_to_chat_history(self, who:str, message:str):
        st.session_state.chat_history.append(ChatMessage(role=who, content=message))
        RAG_CLS_INST.chat_history = st.session_state.chat_history
            
            












