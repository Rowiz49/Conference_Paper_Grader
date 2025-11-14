from django.shortcuts import render
from ..forms import PaperUploadForm
import pymupdf4llm
import pymupdf.layout
from django.views import View
import ollama


class IndexView(View):
    template_name = "paper_grader/index.html"

    def get(self, request):
        form = PaperUploadForm()
        return render(request, self.template_name, {
        'form': form,
        })

    def llm_processing(self, conference, ollama_url, ollama_model, ollama_api_key, paper_text):
        if ollama_api_key:  
            client = ollama.Client(
                host=ollama_url,
                headers={'Authorization': 'Bearer ' + ollama_api_key}
            )
        else: 
            client = ollama.Client(
                host=ollama_url
            )
        messages = [
            {'role': 'user',
             'content': 'Tell me about this paper: ' + paper_text}
        ]
        print("chat started")
        return client.chat(ollama_model, messages=messages).message.content


    def post(self, request):
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            conference = form.cleaned_data['conference']
            ollama_url = form.cleaned_data['ollama_url']
            ollama_model = form.cleaned_data['ollama_model']
            ollama_api_key = form.cleaned_data['ollama_api_key']
            pdf_file = form.cleaned_data['files']
            
            pdf_file.seek(0)
            doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
            md_text = pymupdf4llm.to_markdown(doc)
            doc.close()
            return render(request, 'paper_grader/pdf.html', {"text": self.llm_processing(conference,ollama_url,ollama_model,ollama_api_key,md_text)})
       


