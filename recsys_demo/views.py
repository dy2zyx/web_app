import pickle
import os
import random
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.views import View
from .methods import parse_movie_metadata, movies, init, cbf_recommender, svd_recommender, hybride_recommender, basic_exp_generator, broader_exp_generator
from .forms import MovieTitleForm
from collections import defaultdict
from django.views.generic import CreateView
from django.contrib import messages

from django.conf import settings
from .models import UserInfo

# Views

user_inputs_ratings = dict()
user_inputs = list()
init()
parse_movie_metadata()
movie_titles = [movies[m_id]['title'] for m_id in movies.keys()]
random_movie_ids = random.sample(movies.keys(), k=10)
random_movies_dict = dict()
random_movie_id_dict = dict()
compteur = 0
for m_id in random_movie_ids:
    random_movies_dict[m_id] = (movies[m_id], compteur)
    random_movie_id_dict[compteur] = m_id
    compteur += 1




class UserLoginView(CreateView):
    template_name = 'recsys_demo/login.html'
    model = UserInfo
    fields = ('first_name', 'last_name', 'email', 'education')

    def form_valid(self, form):
        # if self.request.method == 'POST':
        self.request.session.flush()
        self.object = form.save(commit=False)
        # self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect('index')


class IndexView(generic.TemplateView):
    template_name = 'recsys_demo/index.html'


class ThanksView(generic.TemplateView):
    template_name = 'recsys_demo/thanks.html'


def movierec_view(request):
    template_name = 'recsys_demo/movie_rec.html'
    # movies = parse_movie_metadata()
    # movie_titles = [movies[m_id]['title'] for m_id in movies.keys()]

    if request.is_ajax():
        input_iid = request.POST.get('data_dict[movie_id]')
        input_rating = request.POST.get('data_dict[movie_rating]')
        if not input_iid is None:
            user_inputs_ratings[input_iid] = input_rating
            request.session['user_inputs_ratings'] = user_inputs_ratings
            # print(request.session['user_inputs'])
            # print(request.session['user_inputs_ratings'])
            # print(user_inputs_ratings)
            response = HttpResponse(input_rating, content_type="text/html")
            return response

    if request.method == 'POST':
        form = MovieTitleForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['movie_title']
            movie_id = [iid for iid in movies.keys() if ('title', user_input) in movies[iid].items()][0]
            movie_info = movies[movie_id]
            user_inputs.append(movie_id)
            request.session['user_inputs'] = user_inputs
            context = {'user_input': user_input, 'movie_titles': movie_titles, 'movie_info': movie_info,
                       'movie_id': movie_id, 'random_movies_dict': random_movies_dict, 'random_movie_id_dict': random_movie_id_dict}
            return render(request, template_name, context=context)
        else:
            print(form.errors.as_data())
            return render(request, template_name, {'form': form, 'movie_titles': movie_titles, 'random_movies_dict': random_movies_dict, 'random_movie_id_dict': random_movie_id_dict})
    return render(request, template_name=template_name, context={'movie_titles': movie_titles, 'random_movies_dict': random_movies_dict, 'random_movie_id_dict': random_movie_id_dict})


def profil_view(request):
    template_name = 'recsys_demo/profil.html'

    if request.is_ajax() and request.POST['action'] == 'first_call':
        movie_title = request.POST.get('movie_title')
        print(movie_title)
        movie_id = [iid for iid in movies.keys() if ('title', movie_title) in movies[iid].items()][0]

        response = HttpResponse(movie_id, content_type="text/html")
        return response

    if request.is_ajax() and request.POST['action'] == 'second_call':
        input_iid = request.POST.get('data_dict[movie_id]')
        input_rating = request.POST.get('data_dict[movie_rating]')
        if not input_iid is None:
            user_inputs_ratings[input_iid] = input_rating
            request.session['user_inputs_ratings'] = user_inputs_ratings
            response = HttpResponse(input_rating, content_type="text/html")
            return response

    if not 'user_inputs_ratings' in request.session.keys():
        return render(request, template_name=template_name, context={'nb_item': 0})
    else:
        data_dict = dict()
        for iid in request.session['user_inputs_ratings'].keys():
            if iid in movies.keys():
                movie_info = movies[iid]
                movie_rating = request.session['user_inputs_ratings'][iid]
                l = list()
                l.append(movie_info)
                l.append(movie_rating)
                data_dict[iid] = l
        print(request.session['user_inputs_ratings'])
        return render(request, template_name=template_name, context={'data_dict': data_dict, 'nb_item': len(data_dict.keys())})


def recommendation_view(request):
    template_name = 'recsys_demo/recommendation.html'

    if 'user_inputs_ratings' not in request.session.keys() or len(request.session['user_inputs_ratings'].keys()) < 3:
        warning_msg = 'Note that you have to rate at least 3 items before asking for recommendations'
        messages.warning(request, warning_msg)
        return HttpResponseRedirect('profil')
    else:
        recommender = random.choice(['cbf', 'svd', 'hybride'])
        print(recommender)
        if recommender == 'cbf':
            recommended_items = cbf_recommender(2, request.session['user_inputs_ratings'])
            request.session['recommended_items'] = recommended_items
            rec_dict = dict()
            for iid, predicted_r in recommended_items:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            # print(rec_dict)
            return render(request, template_name=template_name, context={'rec_dict': rec_dict})
        if recommender == 'svd':
            recommended_items = svd_recommender(2, request.session['user_inputs_ratings'])
            request.session['recommended_items'] = recommended_items
            rec_dict = dict()
            for iid, predicted_r in recommended_items:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            # print(recommended_items)
            return render(request, template_name=template_name, context={'rec_dict': rec_dict})
        if recommender == 'hybride':
            recommended_items = hybride_recommender(2, request.session['user_inputs_ratings'])
            request.session['recommended_items'] = recommended_items
            rec_dict = dict()
            for iid, predicted_r in recommended_items:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            # print(recommended_items)
            return render(request, template_name=template_name, context={'rec_dict': rec_dict})


def explanation_view(request):
    template_name = 'recsys_demo/explanation.html'
    if request.is_ajax():
        user_info = UserInfo.objects.get()
        feedback_dict = request.POST.get('feedback')
        print(feedback_dict)
        user_info.feed_back_1 = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    explanation_style = random.choice(['basic', 'broader'])
    print(explanation_style)
    if explanation_style == 'basic':
        input_dict = request.session['user_inputs_ratings']
        recommended_items = request.session['recommended_items']

        exp_output_dict = basic_exp_generator(input_dict, recommended_items, alpha=0.5, beta=0.5, k=3)
        # print(exp_output_dict)
        rec_dict = dict()
        for iid, predicted_r in recommended_items:
            if iid in movies.keys():
                movie_info = movies[iid]
                if iid in exp_output_dict.keys():
                    explanation = exp_output_dict[iid]
                    rec_dict[iid] = (movie_info, explanation)
                else:
                    explanation = "Hops, it seems that it is failed to generate explanation for this item"
                    rec_dict[iid] = (movie_info, explanation)
        return render(request, template_name=template_name, context={'rec_dict': rec_dict})
    elif explanation_style == 'broader':
        input_dict = request.session['user_inputs_ratings']
        recommended_items = request.session['recommended_items']

        exp_output_dict = broader_exp_generator(input_dict, recommended_items, alpha=0.5, beta=0.5, k=3)
        # print(exp_output_dict)
        rec_dict = dict()
        for iid, predicted_r in recommended_items:
            if iid in movies.keys():
                movie_info = movies[iid]
                if iid in exp_output_dict.keys():
                    explanation = exp_output_dict[iid]
                    rec_dict[iid] = (movie_info, explanation)
                else:
                    explanation = "Hops, it seems that it is failed to generate explanation for this item"
                    rec_dict[iid] = (movie_info, explanation)
        return render(request, template_name=template_name, context={'rec_dict': rec_dict})


def re_eval_view(request):
    template_name = 'recsys_demo/re_eval.html'

    if request.is_ajax():
        user_info = UserInfo.objects.get()
        feedback_dict = request.POST.get('feedback_2')
        user_info.feed_back_2 = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dict = dict()
    recommended_items = request.session['recommended_items']
    # print(recommended_items)
    for iid, predicted_r in recommended_items:
        if iid in movies.keys():
            movie_info = movies[iid]
            rec_dict[iid] = movie_info
            # print(recommended_items)
    return render(request, template_name=template_name, context={'recomm_dict': rec_dict})
