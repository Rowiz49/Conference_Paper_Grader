from django.db import models


class Conference(models.Model):
    name = models.CharField(max_length=255,unique=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    question_text = models.TextField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        indexes = [
            models.Index(fields=["conference"]),
        ]

    def __str__(self):
        return self.question_text
