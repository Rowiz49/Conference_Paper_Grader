from django.test import TestCase
from django.urls import reverse
from .models import Conference, Question


class ConferenceViewsTests(TestCase):
    def setUp(self):
        self.conference = Conference.objects.create(name="Existing Conference")
        self.create_url = reverse("conference_create")
        self.update_url = reverse("conference_update", args=[self.conference.id])
        self.delete_url = reverse("conference_delete", args=[self.conference.id])
        self.index_url = reverse("index")

    # -----------------------------
    # ConferenceCreateView
    # -----------------------------
    def test_conference_create_get(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_form.html")
        self.assertIn("conference_form", response.context)
        self.assertIn("formset", response.context)

    def test_conference_create_post_valid_with_questions(self):
        """POST valid conference + valid question formset creates both."""
        data = {
            "name": "Conference With Questions",
            "question_set-TOTAL_FORMS": "1",
            "question_set-INITIAL_FORMS": "0",
            "question_set-MIN_NUM_FORMS": "1",
            "question_set-MAX_NUM_FORMS": "1000",
            "question_set-0-id":"",
            "question_set-0-conference": "",
            "question_set-0-question_text": "What is AI?",
            "question_set-0-position": "0",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.index_url)

        conference = Conference.objects.get(name="Conference With Questions")
        questions = Question.objects.filter(conference=conference)
        self.assertEqual(questions.count(), 1)
        self.assertEqual(questions.first().question_text, "What is AI?")

    def test_conference_create_post_invalid_no_questions(self):
        """POST conference without questions should fail due to min_num=1."""
        data = {
            "name": "Conference With Questions",
            "question_set-TOTAL_FORMS": "0",
            "question_set-INITIAL_FORMS": "0",
            "question_set-MIN_NUM_FORMS": "1",
            "question_set-MAX_NUM_FORMS": "1000"
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_form.html")

        errors = response.context["formset"].non_form_errors()
        self.assertIn(" Please submit at least 1 question.", errors)
        self.assertFalse(Conference.objects.filter(name="Invalid Conference").exists())

    def test_conference_create_post_invalid_conference_form(self):
        """POST invalid conference name should re-render form with errors."""
        data = {
            "name": "",
            "question_set-TOTAL_FORMS": "1",
            "question_set-INITIAL_FORMS": "0",
            "question_set-MIN_NUM_FORMS": "1",
            "question_set-MAX_NUM_FORMS": "1000",
            "question_set-0-id":"",
            "question_set-0-conference": "",
            "question_set-0-question_text": "What is AI?",
            "question_set-0-position": "0",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_form.html")
        self.assertFormError(response.context["conference_form"], "name", "This field is required.")
        self.assertFalse(Conference.objects.exclude(name="Existing Conference").exists())

    # -----------------------------
    # ConferenceUpdateView
    # -----------------------------
    def test_conference_update_get(self):
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_form.html")
        self.assertTrue(response.context["is_edit"])
        self.assertEqual(response.context["conference"].id, self.conference.id)

    def test_conference_update_post_valid(self):
        """POST valid data should update name and replace questions."""
        data = {
            "name": "Updated Conference",
            "question_set-TOTAL_FORMS": "1",
            "question_set-INITIAL_FORMS": "0",
            "question_set-MIN_NUM_FORMS": "1",
            "question_set-MAX_NUM_FORMS": "1000",
            "question_set-0-id":"",
            "question_set-0-conference": "",
            "question_set-0-question_text": "Updated Question?",
            "question_set-0-position": "0",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.index_url)
        self.conference.refresh_from_db()
        self.assertEqual(self.conference.name, "Updated Conference")
        self.assertEqual(Question.objects.filter(conference=self.conference).count(), 1)

    def test_conference_update_post_invalid_no_questions(self):
        """POST update with no questions should fail validation."""
        data = {
            "name": "No Questions Conference",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_form.html")
        errors = response.context["formset"].non_form_errors()
        self.assertIn(" Please submit at least 1 question.", errors)
        self.conference.refresh_from_db()
        self.assertEqual(self.conference.name, "Existing Conference")

    # -----------------------------
    # conference_delete view
    # -----------------------------
    def test_conference_delete_get(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paper_grader/conference/conference_confirm_delete.html")
        self.assertEqual(response.context["conference"], self.conference)

    def test_conference_delete_post(self):
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.index_url)
        self.assertFalse(Conference.objects.filter(pk=self.conference.pk).exists())
