import operator

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Q
from functools import reduce

from .models import Question, Answer, Tag


def set_list_order(request):
    """Switches order od rendered questions (either by date or by votes number)"""
    if "current_order" not in request.session:
        request.session['current_order'] = '-pub_date'

    if request.method == "GET":
        if 'order' in request.GET:
            if request.GET['order'] == 'date':
                request.session['current_order'] = '-pub_date'
            elif request.GET['order'] == 'vote':
                request.session['current_order'] = '-votes'


def fetch_questions(user_query, order, by_tag=False):
    """Returns list of question matching against search query (either by key words or by tag)"""
    try:
        if user_query:
            tag_query = user_query.split(':')
            if len(tag_query) == 2 and tag_query[0] == 'tag':
                by_tag = True
                key_words = [tag_query[1]]
            else:
                key_words = user_query.replace(';', ' ').replace(',', ' ').split()
            if by_tag:
                question_list = Question.objects.filter(tag__tag__in=key_words)
            else:
                query = reduce(operator.or_, (Q(header__icontains=word) |
                                              Q(content__icontains=word) for word in key_words))
                question_list = Question.objects.filter(query)
            question_list = question_list.order_by(order)
            return question_list
    except KeyError:
        pass


def paginate(request, paginator, item_list):
    """Returns list of items (questions or answers) should be rendered on given page"""

    def get_page_range():
        """Returns range of pages rendered at the bottom"""
        index = item_list.number - 1
        max_index = len(paginator.page_range)
        start_index = index - 3 if index >= 3 else 0
        end_index = index + 3 if index <= max_index - 3 else max_index
        return list(paginator.page_range)[start_index:end_index]

    try:
        page_num = request.GET["page_number"]
        item_list = paginator.page(page_num)
    except (KeyError, EmptyPage, PageNotAnInteger, MultiValueDictKeyError) as e:
        page_num = 1
        item_list = paginator.page(page_num)
    finally:
        return item_list, get_page_range()


def vote(request, message):
    """Either upvotes or downvotes questions, answers"""
    if request.method == "POST" and request.user.is_authenticated:
        if 'upvote' in request.POST:
                if message.upvote(request.user) == 'already_upvoted':
                    message.cancel_vote(request.user)
        elif 'downvote' in request.POST:
                if message.downvote(request.user) == 'already_downvoted':
                    message.cancel_vote(request.user)


def add_tag(new_tag, question):
    """Puts tag into given question"""
    if not Tag.objects.filter(tag=new_tag).exists():
        tag = Tag(tag=new_tag)
        tag.save()
    else:
        tag = Tag.objects.get(tag=new_tag)
    question.tag.add(tag)


def is_correct_answer_given(question):
    """Returns true if question already has acceoted answer"""
    if Answer.objects.filter(correctness=True, question=question).count() > 0:
        return True
    return False
