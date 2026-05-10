import PyPDF2
import io

def extract_text_from_pdf(file_input):
    """Extracts text from a PDF file path or file-like object."""
    text = ""
    try:
        # Check if it's a file path (string) or an uploaded file object
        if isinstance(file_input, str):
            with open(file_input, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        else:
            reader = PyPDF2.PdfReader(file_input)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"