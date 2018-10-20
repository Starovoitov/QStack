import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import os


class NewUserManager(UserManager):
    def create_user(self, username, email=None, password=None, image=None):
        """
                Creates and saves a User with the given email, date of
                birth and password.
                """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            image=image
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, image=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            password=password,
            image=image,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


def get_image_path(instance, filename):
    return os.path.join('photos', str(instance.id), filename)


def prohibit_empty(val):
    if not val or val == '':
        raise ValidationError("Please insert a text before submitting")


class User(AbstractUser):

    image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    objects = NewUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email


class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.CharField(max_length=15000, null=False, blank=False, validators=[prohibit_empty])
    pub_date = models.DateTimeField(auto_now_add=True)
    correctness = models.BooleanField(default=False)
    question = models.ForeignKey("Question", null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.content

    def get_author(self):
        return self.user.username

    def get_author_image(self):
        if self.user.image:
            return self.user.image.url

    def change_mark(self):
        self.correctness = not self.correctness
        self.save()
        return self.correctness

    def upvote(self, user):
        try:
            self.answer_vote.create(user=user, answer=self, rate_sign=True)
            self.votes += 1
            self.save()
        except IntegrityError:
            return 'already_upvoted'
        return 'ok'

    def downvote(self, user):
        try:
            self.answer_vote.create(user=user, answer=self, rate_sign=False)
            self.votes -= 1
            self.save()
        except IntegrityError:
            return 'already_downvoted'
        return 'ok'

    def cancel_vote(self, user):
        try:
            vote = self.answer_vote.filter(user=user, answer=self).first()
            if vote.rate_sign:
                self.votes -= 1
            else:
                self.votes += 1
            self.save()
            vote.delete()

        except IntegrityError:
            return 'was not voted'
        return 'ok'

    def is_voted(self, user):
        votes = self.answer_vote.filter(user=user, answer=self).count()
        if votes == 0:
            return False
        else:
            return True

    def check_vote(self, user):
        try:
            vote = self.answer_vote.filter(user=user, answer=self).first()
            if vote.rate_sign:
                return "up"
            else:
                return "down"
        except IntegrityError:
            return 'was not voted or the vote has been cancelled'

    def get_votes_count(self):
        return self.answer_vote.all().count()


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    header = models.CharField(max_length=200, null=False, blank=False, validators=[prohibit_empty])
    content = models.CharField(max_length=5000, null=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    tag = models.ManyToManyField("Tag", blank=True)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.header

    def get_tags(self):
        return [str(tag) for tag in self.tag.all()]

    def get_answers_count(self):
        return Answer.objects.filter(question__id=self.id).count()

    def get_author(self):
        return self.user.username

    def get_author_image(self):
        if self.user.image:
            return self.user.image.url

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def upvote(self, user):
        try:
            self.question_vote.create(user=user, question=self, rate_sign=True)
            self.votes += 1
            self.save()
        except IntegrityError as e:
            print(str(e))
            return 'already_upvoted'
        return 'ok'

    def downvote(self, user):
        try:
            self.question_vote.create(user=user, question=self, rate_sign=False)
            self.votes -= 1
            self.save()
        except IntegrityError:
            return 'already_downvoted'
        return 'ok'

    def cancel_vote(self, user):
        try:
            vote = self.question_vote.filter(user=user, question=self).first()
            if vote.rate_sign:
                self.votes -= 1
            else:
                self.votes += 1

            self.save()
            vote.delete()

        except IntegrityError:
            return 'was not voted'
        return 'ok'

    def is_voted(self, user):
        votes = self.question_vote.filter(user=user, question=self).count()
        if votes == 0:
            return False
        else:
            return True

    def check_vote(self, user):
        try:
            vote = self.question_vote.filter(user=user, question=self).first()
            if vote.rate_sign:
                return "up"
            else:
                return "down"
        except IntegrityError:
            return 'was not voted or the vote has been cancelled'

    def get_votes_count(self):
        return self.question_vote.all().count()


class VoteQuestion(models.Model):

    question = models.ForeignKey("Question", related_name='question_vote', on_delete=models.PROTECT)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    rate_sign = models.BooleanField()

    def __str__(self):
        if self.rate_sign:
            rate = "up"
        else:
            rate = "down"
        return str(self.question.id) + '(id): ' + str(self.question)[:50] + ' --- ' + str(self.user) + ' (' + rate + ')'

    class Meta:
        unique_together = [('question', 'user'), ]


class VoteAnswer(models.Model):

    answer = models.ForeignKey("Answer", related_name='answer_vote', on_delete=models.PROTECT)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    rate_sign = models.BooleanField()

    def __str__(self):
        if self.rate_sign:
            rate = "up"
        else:
            rate = "down"
        return str(self.answer.id) + '(id): ' + str(self.answer)[:50] + ' --- ' + str(self.user) + ' (' + rate + ')'

    class Meta:
        unique_together = [('answer', 'user'), ]


class Tag(models.Model):
    tag = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tag

