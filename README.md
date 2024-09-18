##  ChatPDF
This is a simple application built with Streamlit that uses Retrieval-Augmented Generation (RAG) 
and Ollama to enable users to interact with a PDF file.

### Features
Upload a PDF file.
Ask any questions related to the content of the uploaded PDF.
Get responses generated from the PDF content using RAG and Ollama.
### How It Works
Input: The user uploads a PDF file.
Query: The user asks questions about the content of the PDF.
Response: The application uses RAG and Ollama to generate responses based on the content of the uploaded PDF.
### Run
#### Create the python environment
``` 
python3 -m venv venv
```
#### Activate the python environment
``` 
python3 source/bin/activate
```
#### Install the dependencies
``` 
pip3 install -r requirements.txt
```
#### Run the app
``` 
streamlit run app.py
```