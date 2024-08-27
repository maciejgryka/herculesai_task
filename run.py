import docx

def get_text_from_docx(file_path):
    try:
        # Open the .docx file
        doc = docx.Document(file_path)

        # Initialize an empty list to store paragraphs
        full_text = []

        # Iterate through paragraphs in the document
        for para in doc.paragraphs:
            full_text.append(para.text)

        # Join all paragraphs into a single string
        return '\n'.join(full_text)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

file_path = 'data/Contract + Amendment example v3 .docx'
text_content = get_text_from_docx(file_path)
print(text_content)
