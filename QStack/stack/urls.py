from django.conf.urls import url
from django.urls import path

from . import views
from .apps import StackConfig

app_name = StackConfig.name
urlpatterns = [
    url(r'^$', views.index, name='index'),
    path('<int:question_id>/', views.detail, name='detail'),
    path('<int:question_id>/vote', views.vote_question, name='vote'),
    path('<int:question_id>/vote/<int:answer_id>', views.vote_answer, name='vote'),
    path('<int:question_id>/mark_answer/<int:answer_id>', views.mark_answer, name='mark_answer'),
    path('<int:question_id>/give_answer/', views.give_answer, name='give_answer'),
    path('profile/', views.Profile.as_view(), name='profile'),
    path('ask/', views.ask, name='ask'),
    path('tags/', views.tags, name='tags'),
    path('ask_question/', views.ask_question, name='ask_question'),
    url(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    url(r'^activate/(?P<uidb64>.+)/(?P<token>.+)/$',
        views.activate, name='activate'),
]
