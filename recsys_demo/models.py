from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
# Create your models here.


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class UserInfo(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=False)

    master, phd, postdoc, higher = 'master student', 'phd student', 'post doc student', 'higher'
    education_levels = [
        (master, 'Master'),
        (phd, 'Ph.D'),
        (postdoc, 'Post Ph.D'),
        (higher, 'Professor'),
    ]

    education = models.CharField(choices=education_levels, default=None, max_length=20)

    male, female = 'male', 'female'
    sex = [
        (male, 'Male'),
        (female, 'Female'),
    ]

    sex = models.CharField(choices=sex, default=None, max_length=20, null=True)
    feed_back_top_1 = models.CharField(max_length=10000, default="Nothing yet")
    feed_back_re_top_1 = models.CharField(max_length=10000, default="Nothing yet")
    feed_back_list = models.CharField(max_length=10000, default="Nothing yet")

    def get_absolute_url(self):
        return reverse('index')