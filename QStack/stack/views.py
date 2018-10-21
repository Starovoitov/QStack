from django.template import loader
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.utils.http import urlsafe_base64_decode

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .tokens import account_activation_token
from .utils import *


def index(request):
    question_list = []
    set_list_order(request)

    if 'search' in request.GET:
        question_list = fetch_questions(request.GET['search'], request.session['current_order'])
    elif 'tag' in request.GET:
        question_list = fetch_questions(request.GET['tag'], request.session['current_order'], by_tag=True)

    if not question_list and not any(param in ['search', 'tag'] for param in request.GET):
        question_list = Question.objects.order_by(request.session['current_order'])

    pag = Paginator(question_list, 5, orphans=0, allow_empty_first_page=True)
    question_list, page_range = paginate(request, pag, question_list)

    template = loader.get_template('stack/index.html')
    context = {
            'question_list': question_list,
            'page_range': page_range,
            'list_order': request.session['current_order'],
        }
    return HttpResponse(template.render(context, request))


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    answer_list = question.answer_set.get_queryset().order_by('-votes', '-pub_date')
    pag = Paginator(answer_list, 2, orphans=0, allow_empty_first_page=True)
    answer_list, page_range = paginate(request, pag, answer_list)
    return render(request, 'stack/detail.html', {'question': question,
                                                 'answer_list': answer_list, 'page_range': page_range,
                                                 'question_resolved': is_correct_answer_given(question)})


def vote_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    vote(request, question)
    return HttpResponseRedirect(reverse('stack:detail', args=(question_id,)))


def vote_answer(request, question_id, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    vote(request, answer)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def mark_answer(request, question_id, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    answer.change_mark()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def give_answer(request, question_id):

    if not request.POST['answer'] or request.POST['answer'] == "":
        return HttpResponseRedirect(reverse('stack:detail', args=(question_id,)))

    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST' and request.user.is_authenticated:
        answer = Answer(content=request.POST['answer'].rstrip(), question=question, author=request.user)
        answer.save()

        send_mail('New answer', 'You have gotten a new answer to your question: '
                  + request.build_absolute_uri().replace('give_answer/', ''),
                  'test@example.com', [request.user.email], fail_silently=True)

    return HttpResponseRedirect(reverse('stack:detail', args=(question_id,)))


def ask_question(request):

    def get_tags(tag_string):
        return tag_string.lower().strip().replace(';', ' ').replace(',', ' ').split()

    entered_tags = []

    if request.method == 'POST' and request.user.is_authenticated:

        if not request.POST['q_header'] or request.POST['q_header'] == "":
            return HttpResponseRedirect(reverse('stack:ask'))

        if request.POST['q_tags']:
            entered_tags = get_tags(request.POST['q_tags'])

            if len(entered_tags) > 3:
                return render(request, 'stack/ask.html', {'q_header': request.POST['q_header'],
                                                          'q_content': request.POST['q_content'],
                                                          'q_tags': request.POST['q_tags'],
                                                          'error': 'should be used no more than 3 tags'})

        new_question = Question(content=request.POST['q_content'].strip(),
                                header=request.POST['q_header'].strip(),
                                user=request.user)
        new_question.save()

        if entered_tags:
            for entered_tag in entered_tags:
                add_tag(entered_tag, new_question)

        return detail(request, new_question.id)

    return index(request)


def ask(request):
    template = loader.get_template('stack/ask.html')
    return HttpResponse(template.render({}, request))


def tags(request):
    template = loader.get_template('stack/tags.html')
    tag_list = Tag.objects.order_by('tag')
    return HttpResponse(template.render({'tags': tag_list}, request))


class SignUp(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class Profile(generic.UpdateView):
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('profile')
    template_name = 'registration/profile.html'
    last_file = None

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.last_file = self.request.FILES.get('image')
        messages.add_message(request, messages.INFO, self.last_file)
        return super().post(request, *args, **kwargs)


def account_activation_sent(request):
    return render(request, 'registration/account_activation_email.html')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return index(request)
    else:
        return render(request, 'registration/account_activation_invalid.html')
