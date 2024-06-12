import os
import yaml 
import base64
import uuid # For user ID

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from pydantic_valids import validate_pdf_input
from rag import RAGSinglePDF


    
class RAGPDFapp():
    def __init__(self):
        st.sidebar.title("RAGSinglePDF")
        st.sidebar.write("This app enables you to talk to your favorite PDF.")
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
        # Create instance of RAGSinglePDF class
        self.rag_cls_inst = RAGSinglePDF(user_id=self.user_id)

        self._ask_inputs()

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
    
    def _ask_inputs(self):

        
        input_source = self._ask_new_or_previously_loaded()
        
        if input_source == 'load_new_pdf':
            pdf_input = self._ask_pdf_input()
            self.load_new_pdf(pdf_input)
            
        elif input_source == 'previously_loaded_pdf':
            pdfs = self.rag_cls_inst.get_users_pdf()
            
            # If user already loaded pdf in the past, talk to preexiting embbedings
            if pdfs:
                
                #selected_pdf = st.sidebar.multiselect('From your previously loaded PDFs, select the one(s) you want to talk to', pdfs)
                selected_pdf = st.sidebar.selectbox("Select a pre-existing PDF", pdfs)
                self.previously_loaded_pdf(selected_pdf)
            # If not, user needs to upload a pdf, carry out embbedings etc..
            else:
                st.sidebar.write('You currently do not have loaded any pdf yet.')
                pdf_input = self._ask_pdf_input()
                self.load_new_pdf(pdf_input)
        
    def _ask_new_or_previously_loaded(self):
        # Option to select input source
        return st.sidebar.radio("Select input source:", ('load_new_pdf', 'previously_loaded_pdf'))
    
    def _ask_pdf_input(self):
        return st.sidebar.file_uploader("Please upload your PDF file (file name, including extention, should be <= 42 caracters)", type="pdf")
    
    
    #def _ask_tag():
    
    def _chat_with_pdf(self, query_engine):
        if query := st.chat_input("You can now start chatting with your PDF."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            with st.chat_message("assistant"):
                if query:
                    response = self.rag_cls_inst.run_query(query_engine, query)
                    st.markdown(response.response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
    def load_new_pdf(self, pdf_input):
        # Validate pdf input through pydantic
        validate_pdf_input(pdf_input)
        query_engine = self.rag_cls_inst.load_new_pdf(pdf_input)
        self._chat_with_pdf(query_engine)
    
    def previously_loaded_pdf(self, selected_pdf):
        query_engine = self.rag_cls_inst.load_existing_pdf(selected_pdf)        
        self._chat_with_pdf(query_engine)




    







