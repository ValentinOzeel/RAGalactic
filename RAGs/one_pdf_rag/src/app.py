import os
import yaml 
import base64
import uuid # For user ID
import time

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
        
        # App parameters and corresponding default value
        self.param_reset_values = {
            'messages': [],
            'chat_history': [],
            'memory': True,
            'streaming': True,
            'input_source': 'load_new_pdf',
            'add_tags': False,
            'tags_str': None,
            'tags_pdf_input': None,
            'pdf_input': None,
            'pdf_filter_param': 'show_all_pdf_names',
            'selected_pdfs': None,
        }
        
        # Initialize session state parameters (messages, widget values etc...)
        self.init_session_state_parameters()

        # Set user_id in RAG_CLS_INST
        RAG_CLS_INST.set_user_id(self.user_id)
        
        
        logging.debug(f'CLASS INIT')
        

        
            

        self.ask_app_parameters()
        self.ask_input()
        self.run_chatbot()
        

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
    
    def _manage_session_state(self, key, modify=None, reset:bool=False):
        # Initialize non-existing key in session_state
        if not modify and not reset:
            if key not in st.session_state:
                st.session_state[key] = self.param_reset_values[key]
                
        if key in st.session_state:
            # Update key's value
            if modify:
                st.session_state[key] = modify
            # Reset existing key to default value
            elif reset:
                st.session_state[key] = self.param_reset_values[key]    
    
    def init_session_state_parameters(self):
        # Initialize as session_state key
        for param in ['messages', 'chat_history']:
            self._manage_session_state(param)

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


            
           
           
           
           
            
    def ask_app_parameters(self):
        logging.debug(f'ASK PARAMS')
        with st.sidebar:
            self._ask_engine_features()
            self._ask_new_or_previously_loaded()

    def _ask_engine_features(self):
        st.radio("LLM memory:", (False, True), 
                 key='memory', horizontal=True, 
                 on_change=self._empty_chat_and_set_engine_features_callback)
        
        st.radio("LLM response streaming:", (False, True), 
                 key='streaming',  horizontal=True,
                 on_change=self._empty_chat_and_set_engine_features_callback)
           
    def _ask_new_or_previously_loaded(self):
        # Option to select input source
        st.radio("Select input source:", ('load_new_pdf', 'previously_loaded_pdf'),
                 key='input_source',
                 on_change=self._empty_chat_callback)

    def _empty_chat_and_set_engine_features_callback(self):
        self._manage_session_state('messages', reset=True)
        self._manage_session_state('chat_history', reset=True)
        RAG_CLS_INST._set_engine_feature(st.session_state.memory, st.session_state.streaming)
    
    def _empty_chat_callback(self):
        st.session_state.messages = []
        st.session_state.chat_history = []




    def _ask_input_callback(self):
        st.session_state.messages = []
        st.session_state.chat_history = []
        self.ask_input()
        
    def _reset_widget_value_and_empty_chat_callback(self, params:List=None, reset_values:List=None):
        st.session_state.messages = []
        st.session_state.chat_history = []
        
        
    #@st.experimental_fragment
    def ask_input(self):
        logging.debug(f'ASK INPUT')
        with st.sidebar:
            if st.session_state.input_source == 'load_new_pdf':
                self._ask_tags()
                self._ask_pdf_input()
    
            # If user already loaded pdf in the past, talk to preexiting embbedings
            elif st.session_state.input_source == 'previously_loaded_pdf':
                all_pdfs = RAG_CLS_INST.get_user_pdfs()
    
                # If not, user needs to upload a pdf, carry out embbedings etc..
                if not all_pdfs:
                    st.write('You currently do not have loaded any pdf yet. Please load one below:')
                    self._ask_tags()
                    self._ask_pdf_input()
                    
                # Else we can select previously loaded pdfs
                else:
                    self._pdf_selection_parameter()
                       
                       
                       

                #RESET self.pdf_select_param and other attributes AFTER USAGE
                #################
                ##############
                if st.session_state.pdf_filter_param:
                    if st.session_state.pdf_filter_param == 'show_all_pdf_names':
                        self._ask_all_previously_loaded_pdfs(all_pdfs)
                       
                    else:
                        all_user_tags = RAG_CLS_INST.get_users_tags()

                        if not all_user_tags: 
                            st.write('You currently do not have loaded pdf assiocated with a tag yet.')
                            st.write('Select amongst all your previously loaded PDFs:')
                            self._ask_all_previously_loaded_pdfs(all_pdfs)
                        
                        else:
                            self._ask_which_tags(all_user_tags)
                            
                            if st.session_state.pdf_filter_param == 'show_pdf_strictly_tagged':
                                files_with_selected_tags = RAG_CLS_INST.get_user_pdfs(tagged_with_all=st.session_state.selected_tags)
                            elif st.session_state.pdf_filter_param == 'show_pdf_at_least_one_tag':
                                files_with_selected_tags = RAG_CLS_INST.get_user_pdfs(tagged_with_at_least_one=st.session_state.selected_tags)
                        
                            if files_with_selected_tags:
                                self._ask_previously_loaded_pdfs_with_tags(files_with_selected_tags)
                                
                            else:
                                st.write('You currently do not have loaded pdf assiocated with the selected tag(s).')
                                st.write('Select amongst all your previously loaded PDFs:')
                                self._ask_all_previously_loaded_pdfs(all_pdfs)
                                
                                
                                #FILTER WITH STRICT ALL TAGS OR AT LEAST ONE OF THE TAG ? AND or OR ATTR 
                                #THEN LET USER SELECT SOME PDFs from the filter OR ALL PDFs
                                

        
        



    def _run_chatbot_callback(self):
        st.session_state.messages = []
        st.session_state.chat_history = []
        self.run_chatbot()
        
    def _pdf_selection_parameter(self):
        st.selectbox('Select a PDF selection parameter:', ['show_all_pdf_names', 'show_pdf_strictly_tagged', 'show_pdf_at_least_one_tag'], 
                     key='pdf_filter_param',
                     on_change=self._empty_chat_callback)
        
    def _ask_all_previously_loaded_pdfs(self, pdfs):
        st.multiselect("Select -at least- one pre-existing PDF", pdfs, 
                        key='selected_pdfs',
                        on_change=self._empty_chat_callback)
    
    def _ask_which_tags(self, all_tags):
        st.multiselect("Select -at least- one tag", all_tags, 
                       key='selected_tags',
                       on_change=self._empty_chat_callback)

    def _ask_previously_loaded_pdfs(self, files_with_selected_tags):
        files_with_selected_tags.insert(0, 'SELECT ALL LISTED PDFs')
        selected_pdfs = st.multiselect("Select -at least- one pre-existing PDF (presented PDFs have all been tagged with the tags you selected)", files_with_selected_tags, 
                                       key='selected_pdfs',
                                       on_change=self._empty_chat_callback)
        
        if 'SELECT ALL LISTED PDFs' in selected_pdfs:
            files_with_selected_tags.pop(0)
            return files_with_selected_tags
        else:
            return selected_pdfs
        
        
        
    def _ask_tags(self):
        name_value_sep = '::'
        tag_sep = '//'
        
        st.radio('Do you want to add tag(s) to your PDF ?', [False, True], 
                key='add_tags', horizontal=True, 
                on_change=self._empty_chat_callback)
        
        if st.session_state.add_tags:
            st.write(f"Single tag format: 'name{name_value_sep}value'")
            st.write(f"Multiple tags format: 'name{name_value_sep}value{tag_sep}name{name_value_sep}value{tag_sep}name{name_value_sep}value'")
            
            st.text_input(f"Please enter the desired tag(s) for your PDF.", 
                          key='tags_str')   
              
            try:       
                list_str_tag_name_tag = st.session_state.tags_str.split(tag_sep) if tag_sep in st.session_state.tags_str else [st.session_state.tags_str]


                st.session_state.tags_pdf_input = [{name: tag} for str_tag_name_tag in list_str_tag_name_tag for name, tag in [str_tag_name_tag.split(name_value_sep)]]

                placeholder = st.empty()
                placeholder.text(f'Tags: {st.session_state.tags_pdf_input}')
                #placeholder.empty() 
            
            except ValueError:
                alert = st.warning("Invalid tag entry. Please retry using the correct format.")
                time.sleep(10)
                alert.empty() # Clear the alert



    def _ask_pdf_input(self):
        st.file_uploader("Please upload your PDF file (file name, including extention, should be <= 42 caracters)", type="pdf", 
                        key='pdf_input',   
                        on_change=self._empty_chat_callback)





    def run_chatbot(self):
        if st.session_state.input_source == 'load_new_pdf':
            self.load_new_pdf()
        elif st.session_state.input_source == 'previously_loaded_pdf':
            self.previously_loaded_pdf()      
            
    def load_new_pdf(self):
        if st.session_state.pdf_input:
            # Validate pdf input through pydantic
            validate_pdf_input(self.pdf_input)
            engine = RAG_CLS_INST.load_new_pdf(st.session_state.pdf_input, tags=st.session_state.tags_pdf_input)
            self.reset_attributes(['pdf_input', 'tags_pdf_input'])
            self._chat_with_pdf(engine)
    
    def previously_loaded_pdf(self):
        logging.debug(f'PREVIOUSLY LOADED PDF FOR CHAT')
        if st.session_state.selected_pdfs:
            engine = RAG_CLS_INST.load_existing_pdf(st.session_state.selected_pdfs)   
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
                    rag_response = RAG_CLS_INST.run_chat(engine, prompt) if st.session_state.memory else RAG_CLS_INST.run_query(engine, prompt)
                    response = st.write_stream(rag_response.response_gen) if st.session_state.streaming else st.markdown(rag_response.response)
                    
            self._add_to_chat_history('user', str(prompt))
            self._add_to_chat_history('system', str(rag_response.response))
            st.session_state.messages.append({"role": "assistant", "content": response})

    def _add_to_chat_history(self, who:str, message:str):
        st.session_state.chat_history.append(ChatMessage(role=who, content=message))
        RAG_CLS_INST.chat_history = st.session_state.chat_history
            
            












