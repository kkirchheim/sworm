from django.db import models
from django.contrib.auth.models import AbstractUser


class Journal(models.Model):
    issn = models.CharField(max_length=250, primary_key=True)
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Article(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    abstract = models.TextField(max_length=2000)
    publish_on = models.DateField()
    authors = models.TextField(max_length=1000, null=True)
    lda_topics = models.TextField(max_length=256, null=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    citations = models.PositiveSmallIntegerField(null=True)
    country = models.TextField(max_length=256, null=True)
    doi = models.TextField(max_length=256, null=True)
    x1 = models.FloatField(null=True)
    x2 = models.FloatField(null=True)

    def __str__(self):
        return self.title


class CustomUser(AbstractUser):

    articles = models.ManyToManyField(Article, related_name="marked_articles")

    def __str__(self):
        return self.username