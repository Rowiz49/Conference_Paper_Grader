from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from ..models import Conference
from ..forms import ConferenceForm, QuestionFormSet

class ConferenceCreateView(View):
    template_name = "paper_grader/conference/conference_form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "conference_form": ConferenceForm(),
            "formset": QuestionFormSet(),
        })

    def post(self, request):
        conference_form = ConferenceForm(request.POST)
        formset = QuestionFormSet(request.POST)

        if conference_form.is_valid() and formset.is_valid():
            conference = conference_form.save()
            formset.instance = conference
            formset.save()
            return redirect("index")

        return render(request, self.template_name, {
            "conference_form": conference_form,
            "formset": formset,
        })
    

class ConferenceUpdateView(View):
    template_name = "paper_grader/conference/conference_form.html"

    def get(self, request, conference_id):
        conference = get_object_or_404(Conference, pk=conference_id)
        conference_form = ConferenceForm(instance=conference)
        formset = QuestionFormSet(instance=conference)
        return render(request, self.template_name, {
            "conference_form": conference_form,
            "formset": formset,
            "is_edit": True,
            "conference": conference,
        })

    def post(self, request, conference_id):
        conference = get_object_or_404(Conference, pk=conference_id)
        conference_form = ConferenceForm(request.POST, instance=conference)
        formset = QuestionFormSet(request.POST, instance=conference)

        if conference_form.is_valid() and formset.is_valid():
            conference_form.save()
            formset.save()
            return redirect("index")

        return render(request, self.template_name, {
            "conference_form": conference_form,
            "formset": formset,
            "is_edit": True,
            "conference": conference,
        })


def conference_delete(request, conference_id):
    conference = get_object_or_404(Conference, pk=conference_id)

    if request.method == "POST":
        conference.delete()
        return redirect("index")

    return render(request, "paper_grader/conference/conference_confirm_delete.html", {
        "conference": conference
    })
