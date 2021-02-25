import pickle
import os
import random
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .methods import parse_movie_metadata, movies, init, cbf_recommender, svd_recommender, hybride_recommender, broader_exp_generator, exp_generator
from .forms import MovieTitleForm
from collections import defaultdict
from django.views.generic import CreateView
from django.contrib import messages
from django.views.decorators.cache import cache_page
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
_NB_REC = 2

for m_id in random_movie_ids:
    random_movies_dict[m_id] = (movies[m_id], compteur)
    random_movie_id_dict[compteur] = m_id
    compteur += 1


class UserLoginView(CreateView):
    template_name = 'recsys_demo/login.html'
    model = UserInfo
    fields = ('first_name', 'last_name', 'sex', 'email', 'education')

    def form_valid(self, form):
        # if self.request.method == 'POST':
        self.request.session.flush()
        self.object = form.save(commit=False)
        # self.object.user = self.request.user
        self.object.save()
        context = {'user_first_name': self.object.first_name,
                   'user_last_name': self.object.last_name,
                   'user_id': self.object.id}
        self.request.session['current_user_metadata'] = context
        # print(self.request.session.keys())
        # print(self.object.first_name)
        return HttpResponseRedirect('index')
        # return render(self.request, 'recsys_demo/index.html', context=context)


class IndexView(generic.TemplateView):

    template_name = 'recsys_demo/index.html'


class ThanksView(generic.TemplateView):
    template_name = 'recsys_demo/thanks.html'

@csrf_exempt
def movierec_view(request):
    # print(request.session['user_inputs_ratings'])

    template_name = 'recsys_demo/movie_rec.html'
    # movies = parse_movie_metadata()
    # movie_titles = [movies[m_id]['title'] for m_id in movies.keys()]

    if request.is_ajax():
        # print(request.session['user_inputs_ratings'])
        input_iid = request.POST.get('data_dict[movie_id]')
        # input_rating = request.POST.get('data_dict[movie_rating]')
        input_rating = 5
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
    return render(request, template_name=template_name, context={'nb_movies_in_base': len(movies.keys()), 'movie_titles': movie_titles, 'random_movies_dict': random_movies_dict, 'random_movie_id_dict': random_movie_id_dict})


def profil_view(request):
    template_name = 'recsys_demo/profil.html'

    if request.is_ajax():
        removed_movie_id = request.POST.get('removed_movie_id')
        print(removed_movie_id)
        del request.session['user_inputs_ratings'][str(removed_movie_id)]
        request.session.modified = True
        # response = HttpResponse(removed_movie_id, content_type="text/html")
        # return response
        # if not 'user_inputs_ratings' in request.session.keys():
        #     return render(request, template_name=template_name, context={'nb_item': 0})
        # else:
        #     data_dict = dict()
        #     print(request.session['user_inputs_ratings'])
        #     for iid in request.session['user_inputs_ratings'].keys():
        #         if iid in movies.keys():
        #             movie_info = movies[iid]
        #             movie_rating = request.session['user_inputs_ratings'][iid]
        #             # movie_rating = str(int(movie_rating) * 2)
        #             l = list()
        #             l.append(movie_info)
        #             l.append(movie_rating)
        #             data_dict[iid] = l
        #     print(request.session['user_inputs_ratings'])
        #     return render(request, template_name=template_name, context={'data_dict': data_dict, 'nb_item': len(data_dict.keys())})
    #
    # if request.is_ajax() and request.POST['action'] == 'second_call':
    #     input_iid = request.POST.get('data_dict[movie_id]')
    #     input_rating = request.POST.get('data_dict[movie_rating]')
    #     if not input_iid is None:
    #         user_inputs_ratings[input_iid] = input_rating
    #         request.session['user_inputs_ratings'] = user_inputs_ratings
    #         response = HttpResponse(input_rating, content_type="text/html")
    #         return response
    if not 'user_inputs_ratings' in request.session.keys():
        return render(request, template_name=template_name, context={'nb_item': 0})
    else:
        data_dict = dict()
        # request.session.modified = True
        print(request.session['user_inputs_ratings'])
        for iid in request.session['user_inputs_ratings'].keys():
            if iid in movies.keys():
                movie_info = movies[iid]
                movie_rating = request.session['user_inputs_ratings'][iid]
                # movie_rating = str(int(movie_rating) * 2)
                l = list()
                l.append(movie_info)
                l.append(movie_rating)
                data_dict[iid] = l
        print(request.session['user_inputs_ratings'])
        return render(request, template_name=template_name, context={'data_dict': data_dict, 'nb_item': len(data_dict.keys())})

# @cache_page(60 * 15)
def recommendation_view(request):
    template_name = 'recsys_demo/recommendation.html'

    if 'user_inputs_ratings' not in request.session.keys() or len(request.session['user_inputs_ratings'].keys()) < 5:
        warning_msg = 'Note that you have to choose at least 5 liked movies before asking for recommendations'
        messages.warning(request, warning_msg)
        return HttpResponseRedirect('profil')
    else:
        recommenders = ['cbf', 'svd', 'hybride']
        rec_dicts = list()
        for recommender in recommenders:
            print(recommender)
            rec_dict = dict()
            if recommender == 'cbf':
                recommended_items_cbf = cbf_recommender(_NB_REC, request.session['user_inputs_ratings'])
                request.session['recommended_items_cbf'] = recommended_items_cbf
                for iid, predicted_r in recommended_items_cbf:
                    if iid in movies.keys():
                        movie_info = movies[iid]
                        rec_dict[iid] = movie_info
                rec_dicts.append(rec_dict)

            if recommender == 'svd':
                recommended_items_svd = svd_recommender(_NB_REC, request.session['user_inputs_ratings'])
                request.session['recommended_items_svd'] = recommended_items_svd
                for iid, predicted_r in recommended_items_svd:
                    if iid in movies.keys():
                        movie_info = movies[iid]
                        rec_dict[iid] = movie_info
                rec_dicts.append(rec_dict)

            if recommender == 'hybride':
                recommended_items_hybride = hybride_recommender(_NB_REC, request.session['user_inputs_ratings'])
                request.session['recommended_items_hybride'] = recommended_items_hybride
                for iid, predicted_r in recommended_items_hybride:
                    if iid in movies.keys():
                        movie_info = movies[iid]
                        rec_dict[iid] = movie_info
                rec_dicts.append(rec_dict)
        return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})

# @cache_page(60 * 15)
def top_1_explanation_view(request):
    template_name = 'recsys_demo/exp_for_top_1_recommendation.html'

    current_user_id = request.session['current_user_metadata']['user_id']
    # save the feedback of the current user to the database
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1')
        # print("feedback_dict_1: " + feedback_dict)
        user_info.feed_back_top_1 = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    # explanation_styles = ['basic', 'pem_cem']
    recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']
    rec_dicts = list()
    for recommendation_approach in recommendation_approaches:
        input_dict = request.session['user_inputs_ratings']
        recommended_items = request.session[recommendation_approach][:1]
        exp_output_dict_explod, exp_output_dict_pem, exp_output_dict_cem = exp_generator(input_dict, recommended_items)

        rec_dict = dict(dict())
        for iid, predicted_r in recommended_items:
            exp_dict = dict()
            if iid in movies.keys():
                movie_info = movies[iid]
                if iid in exp_output_dict_explod.keys():
                    explanation_explod = exp_output_dict_explod[iid]
                    exp_dict['explod'] = (movie_info, explanation_explod)
                else:
                    explanation_explod = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['explod'] = (movie_info, explanation_explod)

                if iid in exp_output_dict_pem.keys():
                    explanation_pem = exp_output_dict_pem[iid]
                    exp_dict['pem'] = (movie_info, explanation_pem)
                else:
                    explanation_pem = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['pem'] = (movie_info, explanation_pem)

                if iid in exp_output_dict_cem.keys():
                    explanation_cem = exp_output_dict_cem[iid]
                    exp_dict['cem'] = (movie_info, explanation_cem)
                else:
                    explanation_cem = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['cem'] = (movie_info, explanation_cem)
                rec_dict[iid] = exp_dict
        rec_dicts.append(rec_dict)
    return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})

# @cache_page(60 * 15)
def re_eval_view(request):
    template_name = 'recsys_demo/re_eval.html'
    current_user_id = request.session['current_user_metadata']['user_id']
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1_2')
        user_info.feed_back_re_top_1 = str(feedback_dict)
        print("feed_back_re_top_1: " + feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()

    recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']
    for recommendation_approach in recommendation_approaches:
        rec_dict = dict()
        recommended_items = request.session[recommendation_approach][:1]
        for iid, predicted_r in recommended_items:
            if iid in movies.keys():
                movie_info = movies[iid]
                rec_dict[iid] = movie_info
        rec_dicts.append(rec_dict)

    return render(request, template_name=template_name, context={'recomm_dicts': rec_dicts})

@cache_page(60 * 15)
def explanation_view(request):
    template_name = 'recsys_demo/explanation.html'

    current_user_id = request.session['current_user_metadata']['user_id']
    # save the feedback of the current user to the database
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback')
        print("feedback_dict_1: " + feedback_dict)
        user_info.feed_back_list = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    # explanation_styles = ['basic', 'pem_cem']
    recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']

    rec_dicts = list()
    for recommendation_approach in recommendation_approaches:
        input_dict = request.session['user_inputs_ratings']
        recommended_items = request.session[recommendation_approach]
        exp_output_dict_explod, exp_output_dict_pem, exp_output_dict_cem = exp_generator(input_dict, recommended_items)

        rec_dict = dict(dict())
        for iid, predicted_r in recommended_items:
            exp_dict = dict()
            if iid in movies.keys():
                movie_info = movies[iid]
                if iid in exp_output_dict_explod.keys():
                    explanation_explod = exp_output_dict_explod[iid]
                    exp_dict['explod'] = (movie_info, explanation_explod)
                else:
                    explanation_explod = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['explod'] = (movie_info, explanation_explod)

                if iid in exp_output_dict_pem.keys():
                    explanation_pem = exp_output_dict_pem[iid]
                    exp_dict['pem'] = (movie_info, explanation_pem)
                else:
                    explanation_pem = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['pem'] = (movie_info, explanation_pem)

                if iid in exp_output_dict_cem.keys():
                    explanation_cem = exp_output_dict_cem[iid]
                    exp_dict['cem'] = (movie_info, explanation_cem)
                else:
                    explanation_cem = "Hops, it seems that it is failed to generate explanation for this item."
                    exp_dict['cem'] = (movie_info, explanation_cem)
                rec_dict[iid] = exp_dict
        rec_dicts.append(rec_dict)
    return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})
