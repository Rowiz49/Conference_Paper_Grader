from django.shortcuts import render
from ..forms import PaperUploadForm
from pydantic import BaseModel, RootModel
import pymupdf4llm
import pymupdf.layout
from django.views import View
import ollama
import json

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
        
        # Classes for json format enforcment
        class Rating(BaseModel):
            position: int
            question: str
            rating: str
            explanation: str

        class RatingList(RootModel):
            root: list[Rating] 

        message =  f'You are a paper rater for the conference {conference.name}, you have been given the following questions that you must answer in order to evaluate the paper: \n'
        for question in conference.question_set.all():
            message += f'{question.position}. {question.question_text}\n'
        message += 'Following these guidelines, evaluate each question for the following paper, you may answer with yes, partial, no and NA if not applicable. Add an explanation of your answer to each question.\n'
        message += f'You must answer in json format, following the provided template: {str(RatingList.model_json_schema())}\n'
        message += f'Here is the paper you must rate in markdown format: {paper_text}'
        
        content = client.chat(
            model=ollama_model,
            messages=[{'role':'user', 'content':message}],
            format=RatingList.model_json_schema()        
            ).message.content

        return content


    def post(self, request):
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            conference = form.cleaned_data['conference']
            ollama_url = form.cleaned_data['ollama_url']
            ollama_model = form.cleaned_data['ollama_model']
            ollama_api_key = form.cleaned_data['ollama_api_key']
            pdf_file = form.cleaned_data['files']
            
            #Process to markdown
            pdf_file.seek(0)
            doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
            md_text = pymupdf4llm.to_markdown(doc)
            doc.close()

            # Get LLM response
            llm_response = self.llm_processing(
                conference, 
                ollama_url, 
                ollama_model, 
                ollama_api_key, 
                md_text
            )

            try:
                # Parse the JSON string
                ratings_data = json.loads(llm_response)
                
                # Sort by position to ensure correct order
                ratings_data.sort(key=lambda x: x.get('position', 0))
                
                return render(request, 'paper_grader/results.html', {
                    "ratings": ratings_data,
                    "conference": conference
                })
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, show error
                return render(request, 'paper_grader/results.html', {
                    "ratings": [],
                    "error": f"Failed to parse LLM response: {str(e)}",
                    "raw_text": llm_response
                })
        
            # If form is not valid, re-render the form with errors
            return render(request, 'paper_grader/index.html', {'form': form})
       


