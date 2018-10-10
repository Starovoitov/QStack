from django import template

from stack.models import Question, Answer

register = template.Library()


@register.simple_tag
def is_voted(obj, current_user):
    if obj.is_voted(current_user):
        return obj.check_vote(current_user)
    else:
        return


@register.simple_tag
def is_there_correct(answer):
    return answer.correctness


@register.simple_tag
def is_correct_answer_given(question):
    if Answer.objects.filter(correctness=True, question=question).count() > 0:
        return True
    return False


@register.simple_tag
def get_author(obj):
    print(obj.id)
    return obj.get_author()


@register.simple_tag
def trending_list():
    return Question.objects.order_by('-votes')[:10]
