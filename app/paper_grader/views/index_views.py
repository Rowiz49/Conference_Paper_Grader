from django.shortcuts import render
from ..models import Conference


def index(request):
    conferences = Conference.objects.all()
    context = {"conferences": conferences}
    return render(request, "paper_grader/index.html", context)


