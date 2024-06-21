from pydantic import BaseModel, ValidationError, StringConstraints
from typing_extensions import Annotated

class PDFFile(BaseModel):
    filename: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    content_type: Annotated[str, StringConstraints(pattern=r'application/pdf')]
    
    class Config:
        orm_mode = True

def validate_pdf_input(file):
    try:
        pdf_file = PDFFile(filename=file.name, content_type=file.type)
        return pdf_file
    except ValidationError as e:
        raise ValueError(f"Invalid PDF file: {e}")