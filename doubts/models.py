from django.db import models
from django.conf import settings

class PeerDoubt(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    subject = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='peer_doubts')

    def __str__(self):
        return self.title

class Answer(models.Model):
    doubt = models.ForeignKey(PeerDoubt, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='peer_answers')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.doubt.title} by {self.author.username}"
