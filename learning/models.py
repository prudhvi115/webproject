from django.db import models
from django.conf import settings

class Topic(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class LearningPath(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    topics = models.ManyToManyField(Topic, related_name='learning_paths')
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(max_length=20, choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')])
    
    def __str__(self):
        return self.title

class Resource(models.Model):
    learning_path = models.ManyToManyField(LearningPath, related_name='resources')
    title = models.CharField(max_length=200)
    url = models.URLField()
    RESOURCE_TYPES = [
        ('Video', 'Video'),
        ('Article', 'Article'),
        ('Quiz', 'Quiz'),
    ]
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    
    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'resource')

class CourseSchedule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200, default="General Learning")
    current_week = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.user.username}'s Schedule - Week {self.current_week}"

class WeeklyContent(models.Model):
    schedule = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField() # Markdown content from AI
    
    class Meta:
        unique_together = ('schedule', 'week_number')
        ordering = ['week_number']
        
    def __str__(self):
        return f"Week {self.week_number}: {self.title}"
