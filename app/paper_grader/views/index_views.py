from django.shortcuts import render
from ..forms import PaperUploadForm
from pydantic import BaseModel, RootModel
import pymupdf4llm
import pymupdf.layout
from django.views import View
import ollama
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests

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
        message += f'You must answer in json format, following the provided template: {str(RatingList.model_json_schema())}. Make sure your output is a valid json and do not use any special characters that may break the json. \n'
        message += f'Here is the paper you must rate in markdown format: {paper_text}'
        
        content = client.chat(
            model=ollama_model,
            messages=[{'role':'user', 'content':message}],
            format=RatingList.model_json_schema()        
            ).message.content
        return content


    def post(self, request):
        form = PaperUploadForm(request.POST, request.FILES)
        result_template = 'paper_grader/results.html'
        if form.is_valid():
            conference = form.cleaned_data['conference']
            ollama_url = form.cleaned_data['ollama_url']
            ollama_model = form.cleaned_data['ollama_model']
            ollama_api_key = form.cleaned_data['ollama_api_key']
            pdf_file = form.cleaned_data['files']
            
            try:
                # Process to markdown
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

                # Remove all wrapping content that the llm may have generated
                start = llm_response.find('[')
                end = llm_response.rfind(']')

                if start == -1 or end == -1 or start >= end:
                    raise json.JSONDecodeError("No valid JSON array found in input", "", 0)

                # Extract the JSON content
                llm_response = llm_response[start:end + 1]

                # Parse the JSON string
                ratings_data = json.loads(llm_response)
                
                # Sort by position to ensure correct order
                ratings_data.sort(key=lambda x: x.get('position', 0))
                
                # Build lookup: position -> actual question text
                actual_questions = {
                    q.position: q.question_text 
                    for q in conference.question_set.all()
                }

                for rating in ratings_data:
                    pos = rating.get('position')
                    actual = actual_questions.get(pos, '')
                    llm_question = rating.get('question', '').strip()
                    if actual and llm_question != actual.strip():
                        rating['question_mismatch'] = True
                        rating['actual_question'] = actual
                    else:
                        rating['question_mismatch'] = False
                        rating['actual_question'] = actual  # pass through for clarity

                return render(request, result_template, {
                    "ratings": ratings_data,
                    "conference": conference
                })
                
            except json.JSONDecodeError as e:
                return render(request, result_template, {
                    "ratings": [],
                    "error": f"Failed to parse LLM response: {str(e)}",
                    "raw_text": llm_response if 'llm_response' in locals() else "No response"
                })
            except Exception as e:
                # Catch all other errors (Ollama connection, etc.)
                return render(request, result_template, {
                    "ratings": [],
                    "error": f"Error processing paper: {str(e)}",
                    "raw_text": ""
                })
        
        # If form is not valid, re-render the form with errors
        return render(request, 'paper_grader/index.html', {'form': form})


@require_http_methods(["GET"])
def ollama_models_proxy_view(request):
    """Proxy endpoint to fetch Ollama models and avoid CORS issues"""
    ollama_url = request.GET.get('url', '').strip().rstrip('/')
    
    if not ollama_url:
        return JsonResponse({'error': 'URL parameter is required'}, status=400)
    
    try:
        # Make request to Ollama API
        response = requests.get(
            f"{ollama_url}/api/tags",
            timeout=10
        )
        response.raise_for_status()
        
        # Return the JSON response
        return JsonResponse(response.json(), safe=False)
    
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Request timeout'}, status=504)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Cannot connect to Ollama server'}, status=503)
    
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'error': f'HTTP {e.response.status_code}'}, status=e.response.status_code)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


    


