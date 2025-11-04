from django import forms
from django.forms import inlineformset_factory
from .models import Conference, Question


class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Conference name"}
            ),
        }


QuestionFormSet = inlineformset_factory(
    Conference,
    Question,
    fields=["question_text"],
    exclude=["id"], 
    widgets={
        "question_text": forms.Textarea(
            attrs={
                "class": "textarea textarea-sm w-full",
                "rows": 1,
                "placeholder": "Enter a question...",
            }
        )
    },
    extra=1,
    can_delete=True
)
