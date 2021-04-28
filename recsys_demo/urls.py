from django.urls import path

from . import views

app_name = 'recsys_demo'

urlpatterns = [
    path('login', views.UserLoginView.as_view(), name='login'),
    path('index', views.IndexView.as_view(), name='index'),
    # path('thanks', views.ThanksView.as_view(), name='thanks'),
    path('thanks', views.thanks_view, name='thanks'),
    path('movie_rec', views.movierec_view, name='movie_rec'),
    path('movie_rec/profil', views.profil_view, name='profil'),
    path('movie_rec/recommendation', views.recommendation_view, name='movie_recommendation'),
    path('movie_rec/recommendation/explanation_top1_rec', views.top_1_explanation_view, name='movie_exp_top1'),
    path('movie_rec/recommendation/re_eval', views.re_eval_view, name='re_eval'),
    path('movie_rec/recommendation/explanation_top1_rec_2', views.top_1_explanation_view2, name='movie_exp_top1_2'),
    path('movie_rec/recommendation/re_eval_2', views.re_eval_view2, name='re_eval_2'),
    path('movie_rec/recommendation/explanation_top1_rec_3', views.top_1_explanation_view3, name='movie_exp_top1_3'),
    path('movie_rec/recommendation/re_eval_3', views.re_eval_view3, name='re_eval_3'),
    path('movie_rec/recommendation/explanation', views.explanation_view, name='movie_exp'),
]