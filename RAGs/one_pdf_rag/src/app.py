import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from pydantic_valids import validate_pdf_input



    
class RAGPDFapp():
    def __init__(self):
        st.title("RAGSinglePDF")
        st.write("This app enables you to talk to your favorite PDF.")
        
        # Create instance of RAGSinglePDF class
        self.rag_cls_inst = RAGSinglePDF()
        # Get the cookie manager key
        secret_key = self.rag_cls_inst.get_cookie_manager_secret_key()
        # Create a cookie manager
        cookies = EncryptedCookieManager(prefix="streamlit_", key=secret_key)
        if not cookies.ready():
            st.stop()
        # Retrieve or create the user ID
        self.user_id = self.rag_cls_inst.get_user_id(cookies)
        # Add user ID as a query parameter in the URL
        st.experimental_set_query_params(user_id=self.user_id)
        

        # Option to select input source
        self.input_source = st.radio("Select input source:", ('load_new_pdf', 'previously_loaded_pdf'))
        self._ask_inputs()

    def _ask_inputs(self):
        if self.input_source == 'load_new_pdf':
            pdf_input = st.file_uploader("Please upload your PDF file", type="pdf")
            self.load_new_pdf(pdf_input)
            
        elif self.input_source == 'previously_loaded_pdf':
            pdfs = self.rag_cls_inst.get_users_pdf(self.user_id)
            
            # If user already loaded pdf in the past, talk to preexiting embbedings
            if pdfs:
                selected_pdf = st.selectbox("Select a pre-existing PDF", pdfs)
                self.previously_loaded_pdf(selected_pdf)
            # If not, user needs to upload a pdf, carry out embbedings etc..
            else:
                st.write('You currently do not have loaded any pdf yet.')
                pdf_input = st.file_uploader("Please upload your PDF file", type="pdf")
                self.load_new_pdf(pdf_input)
        
           
    def load_new_pdf(self, pdf_input):
        # Validate pdf input through pydantic
        pdf_input = validate_pdf_input(pdf_input)
        # Add input pdf name to corresponding user ID in 
        self.rag_cls_inst.add_new_json_data(id=self.user_id, file_name=pdf_input.name)

        LOAD THE PDF AND EMBEDD IT + STORE CHROMA
    
    def previously_loaded_pdf(self, selected_pdf):
        if selected_pdf:
            RETRIEVE THE EMBEDDINF FOR THIS PDF FOR USER TO TALK TO IT
    









