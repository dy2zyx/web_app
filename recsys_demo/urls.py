from django.urls import path

from . import views

app_name = 'recsys_demo'

urlpatterns = [
    path('login', views.UserLoginView.as_view(), name='login'),
    path('index', views.IndexView.as_view(), name='index'),
    path('movie_rec', views.movierec_view, name='movie_rec'),
    path('movie_rec/profil', views.profil_view, name='profil'),
    path('movie_rec/recommendation', views.recommendation_view, name='movie_recommendation'),
]