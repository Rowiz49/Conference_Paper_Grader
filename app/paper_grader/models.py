from django.db import models

# Create your models here.
class Conference(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name
    

class Question(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    question_text = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["conference"])
        ]

    def __str__(self):
        return self.question_text
    