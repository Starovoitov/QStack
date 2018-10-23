from django import template

from stack.models import Question, Answer

register = template.Library()


@register.simple_tag
def is_voted(obj, current_user):
    """Returns vote sign if question/answer already got vote from current user"""
    if obj.is_voted(current_user):
        return obj.check_vote(current_user)
    else:
        return


@register.simple_tag
def is_there_correct(answer):
    """Returns True if given answer is accepted"""
    return answer.correctness


@register.simple_tag
def is_correct_answer_given(question):
    """Returns True if given question already has accepted answer"""
    if Answer.objects.filter(correctness=True, question=question).count() > 0:
        return True
    return False


@register.simple_tag
def get_author(obj):
    """returns author of question/answer"""
    return obj.get_author()


@register.simple_tag
def trending_list():
    """Returns top 10 questions by number of votes"""
    return Question.objects.order_by('-votes')[:10]
