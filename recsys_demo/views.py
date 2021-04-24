import pickle
import os
import random
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .methods import parse_movie_metadata, movies, init, cbf_recommender, svd_recommender, hybride_recommender, exp_generator
from .forms import MovieTitleForm
from collections import defaultdict
from django.views.generic import CreateView
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.conf import settings
from .models import UserInfo

init()
parse_movie_metadata()
movie_titles = [movies[m_id]['title'] for m_id in movies.keys()]
_NB_REC = 5


class UserLoginView(CreateView):
    template_name = 'recsys_demo/login.html'
    model = UserInfo
    fields = ('first_name', 'last_name', 'sex', 'email')

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
        self.request.session['user_inputs_ratings'] = dict()
        self.request.session['user_inputs'] = list()
        self.request.session['random_movie_ids'] = random.sample(movies.keys(), k=10)
        self.request.session['random_movies_dict'] = dict()
        self.request.session['random_movie_id_dict'] = dict()

        # user_inputs = list()
        # user_inputs_ratings = dict()
        # random_movie_ids = random.sample(movies.keys(), k=10)
        # random_movies_dict = dict()
        # random_movie_id_dict = dict()
        compteur = 0
        for m_id in self.request.session['random_movie_ids']:
            self.request.session['random_movies_dict'][m_id] = (movies[m_id], compteur)
            self.request.session['random_movie_id_dict'][compteur] = m_id
            compteur += 1
        # for m_id in random_movie_ids:
        #     random_movies_dict[m_id] = (movies[m_id], compteur)
        #     random_movie_id_dict[compteur] = m_id
        #     compteur += 1
        # print(self.request.session.keys())
        return HttpResponseRedirect('index')
        # return render(self.request, 'recsys_demo/index.html', context=context)


class IndexView(generic.TemplateView):

    template_name = 'recsys_demo/index.html'


class ThanksView(generic.TemplateView):
    template_name = 'recsys_demo/thanks.html'


@csrf_exempt
def movierec_view(request):

    template_name = 'recsys_demo/movie_rec.html'
    # movies = parse_movie_metadata()
    # movie_titles = [movies[m_id]['title'] for m_id in movies.keys()]

    if request.is_ajax():
        # print(request.session['user_inputs_ratings'])
        input_iid = request.POST.get('data_dict[movie_id]')
        # input_rating = request.POST.get('data_dict[movie_rating]')
        input_rating = 5
        if not input_iid is None:
            # user_inputs_ratings[input_iid] = input_rating
            request.session['user_inputs_ratings'][input_iid] = input_rating
            request.session.modified = True
            # print(request.session['user_inputs_ratings'])
            response = HttpResponse(input_rating, content_type="text/html")
            return response

    if request.method == 'POST':
        form = MovieTitleForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['movie_title']
            if not user_input in movie_titles:
                warning_msg = "Le film <" + str(user_input) + "> n'est pas dans la base de films, veuillez en rechercher un autre."
                messages.warning(request, warning_msg)
                return HttpResponseRedirect('movie_rec')
            movie_id = [iid for iid in movies.keys() if ('title', user_input) in movies[iid].items()][0]
            movie_info = movies[movie_id]
            request.session['user_inputs'].append(movie_id)
            request.session.modified = True
            # request.session['user_inputs'] = user_inputs
            context = {'user_input': user_input, 'movie_titles': movie_titles, 'movie_info': movie_info,
                       'movie_id': movie_id, 'random_movies_dict': request.session['random_movies_dict'], 'random_movie_id_dict': request.session['random_movie_id_dict']}
            return render(request, template_name, context=context)
        else:
            # print(form.errors.as_data())
            return HttpResponseRedirect('movie_rec')
    return render(request, template_name=template_name, context={'nb_movies_in_base': "{:,}".format(len(movies.keys())), 'movie_titles': movie_titles, 'random_movies_dict': request.session['random_movies_dict'], 'random_movie_id_dict': request.session['random_movie_id_dict']})


@csrf_exempt
def profil_view(request):
    template_name = 'recsys_demo/profil.html'

    if request.is_ajax():
        removed_movie_id = request.POST.get('removed_movie_id')
        # print(removed_movie_id)
        # del request.session['user_inputs_ratings'][str(removed_movie_id)]
        # del user_inputs_ratings[str(removed_movie_id)]
        request.session['user_inputs_ratings'].pop(str(removed_movie_id), None)
        # user_inputs_ratings.pop(str(removed_movie_id), None)
        request.session.modified = True

    if not 'user_inputs_ratings' in request.session.keys():
        # print("here")
        return render(request, template_name=template_name, context={'nb_item': 0})
    else:
        data_dict = dict()
        # request.session.modified = True
        # print(request.session['user_inputs_ratings'])
        for iid in request.session['user_inputs_ratings'].keys():
            if iid in movies.keys():
                movie_info = movies[iid]
                movie_rating = request.session['user_inputs_ratings'][iid]
                # movie_rating = str(int(movie_rating) * 2)
                l = list()
                l.append(movie_info)
                l.append(movie_rating)
                data_dict[iid] = l
        # print(request.session['user_inputs_ratings'])
        return render(request, template_name=template_name, context={'data_dict': data_dict, 'nb_item': len(data_dict.keys())})


# @cache_page(60 * 15)
def recommendation_view(request):
    template_name = 'recsys_demo/recommendation.html'

    if 'user_inputs_ratings' not in request.session.keys() or len(request.session['user_inputs_ratings'].keys()) < 5:
        # warning_msg = 'Note that you have to choose at least 5 liked movies before asking for the recommendations'
        warning_msg = 'Notez que vous devrez choisir au moins 5 films préférés avant de pouvoir obtenir la recommandation'
        messages.warning(request, warning_msg)
        return HttpResponseRedirect('profil')
    else:
        recommenders = ['hybride']
        recommender = 'hybride'
        # print(recommender)
        # save the algo_config for user
        current_user_id = request.session['current_user_metadata']['user_id']
        user_info = UserInfo.objects.get(id=current_user_id)
        user_info.algo_config = str(recommender)
        user_info.save()

        rec_dicts = list()
        # for recommender in recommenders:
        rec_dict = dict()
        if recommender == 'cbf':
            recommended_items_cbf = cbf_recommender(_NB_REC, request.session['user_inputs_ratings'])
            # print("Content-based recommendations:" + str(recommended_items_cbf))
            # request.session['recommended_items_cbf'] = recommended_items_cbf
            request.session['recommended_items'] = recommended_items_cbf
            for iid in recommended_items_cbf[:3]:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            rec_dicts.append(rec_dict)

        if recommender == 'svd':
            recommended_items_svd = svd_recommender(_NB_REC, request.session['user_inputs_ratings'])
            # print("CF-based recommendations:" + str(recommended_items_svd))
            request.session['recommended_items'] = recommended_items_svd
            for iid in recommended_items_svd:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            rec_dicts.append(rec_dict)

        if recommender == 'hybride':
            recommended_items_hybride = hybride_recommender(_NB_REC, request.session['user_inputs_ratings'])
            # print("Hybrid recommendations:" + str(recommended_items_hybride))
            request.session['recommended_items'] = recommended_items_hybride
            for iid in recommended_items_hybride[:3]:
                if iid in movies.keys():
                    movie_info = movies[iid]
                    rec_dict[iid] = movie_info
            rec_dicts.append(rec_dict)

        user_info.profile_items = str(request.session['user_inputs_ratings'])
        user_info.save()
        user_info.recommended_items = str(request.session['recommended_items'])
        user_info.save()
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

    rec_dicts = list()
    # for recommendation_approach in recommendation_approaches:
    input_dict = request.session['user_inputs_ratings']
    recommended_items = [request.session['recommended_items'][0]]

    # random choice of explanation style and save to user configs
    explanation_styles = ['explod', 'pem']
    explanation_style = random.choice(explanation_styles)
    # print(explanation_style)
    request.session['explanation_style'] = explanation_style
    # save the algo_config for user
    current_user_id = request.session['current_user_metadata']['user_id']
    user_info = UserInfo.objects.get(id=current_user_id)
    user_info.exp_style_config = str(explanation_style)
    user_info.save()

    # Save slience for explod-5
    exp_output_dict_save = exp_generator(input_dict, request.session['recommended_items'], exp_style='explod')
    user_info.num_exp_top_5_list = str(len(exp_output_dict_save.keys()))
    user_info.save()
    # Fin save
    exp_output_dict = exp_generator(input_dict, recommended_items, exp_style=explanation_style)

    rec_dict = dict(dict())
    for iid in recommended_items:
        exp_dict = dict()
        if iid in movies.keys():
            movie_info = movies[iid]
            if iid in exp_output_dict.keys():
                explanation = exp_output_dict[iid]
                exp_dict['exp_style'] = (movie_info, explanation)
            else:
                explanation = "Hops, it seems that it is failed to generate explanation for this item."
                exp_dict['exp_style'] = (movie_info, explanation)

            rec_dict[iid] = exp_dict
    rec_dicts.append(rec_dict)

    request.session['exp_dicts_1'] = rec_dicts
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
        # print("feed_back_re_top_1: " + feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()
    rec_dict = dict()
    recommended_items = [request.session['recommended_items'][0]]
    for iid in recommended_items:
        if iid in movies.keys():
            movie_info = movies[iid]
            rec_dict[iid] = movie_info
    rec_dicts.append(rec_dict)
    exp_dicts_1 = request.session['exp_dicts_1']
    return render(request, template_name=template_name, context={'recomm_dicts': rec_dicts, 'exp_dicts_1': exp_dicts_1})


# @cache_page(60 * 15)
def top_1_explanation_view2(request):
    template_name = 'recsys_demo/exp_for_top_1_recommendation_2.html'

    current_user_id = request.session['current_user_metadata']['user_id']
    # save the feedback of the current user to the database
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1')
        # print("feedback_dict_1: " + feedback_dict)
        user_info.feed_back_top_1_2 = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()
    # for recommendation_approach in recommendation_approaches:
    input_dict = request.session['user_inputs_ratings']
    recommended_items = [request.session['recommended_items'][1]]

    explanation_style = request.session['explanation_style']
    # print(explanation_style)

    exp_output_dict = exp_generator(input_dict, recommended_items, exp_style=explanation_style)

    rec_dict = dict(dict())
    for iid in recommended_items:
        exp_dict = dict()
        if iid in movies.keys():
            movie_info = movies[iid]
            if iid in exp_output_dict.keys():
                explanation = exp_output_dict[iid]
                exp_dict['exp_style'] = (movie_info, explanation)
            else:
                explanation = "Hops, it seems that it is failed to generate explanation for this item."
                exp_dict['exp_style'] = (movie_info, explanation)

            rec_dict[iid] = exp_dict
    rec_dicts.append(rec_dict)
    request.session['exp_dicts_2'] = rec_dicts
    return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})


# @cache_page(60 * 15)
def re_eval_view2(request):
    template_name = 'recsys_demo/re_eval_2.html'
    current_user_id = request.session['current_user_metadata']['user_id']
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1_2')
        user_info.feed_back_re_top_1_2 = str(feedback_dict)
        # print("feed_back_re_top_1: " + feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()

    # recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']
    # for recommendation_approach in recommendation_approaches:
    rec_dict = dict()
    recommended_items = [request.session['recommended_items'][1]]
    for iid in recommended_items:
        if iid in movies.keys():
            movie_info = movies[iid]
            rec_dict[iid] = movie_info
    rec_dicts.append(rec_dict)
    exp_dicts_2 = request.session['exp_dicts_2']
    return render(request, template_name=template_name, context={'recomm_dicts': rec_dicts, 'exp_dicts_2': exp_dicts_2})


# @cache_page(60 * 15)
def top_1_explanation_view3(request):
    template_name = 'recsys_demo/exp_for_top_1_recommendation_3.html'

    current_user_id = request.session['current_user_metadata']['user_id']
    # save the feedback of the current user to the database
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1')
        # print("feedback_dict_1: " + feedback_dict)
        user_info.feed_back_top_1_3 = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()
    # for recommendation_approach in recommendation_approaches:
    input_dict = request.session['user_inputs_ratings']
    recommended_items = [request.session['recommended_items'][2]]

    explanation_style = request.session['explanation_style']
    # print(explanation_style)

    exp_output_dict = exp_generator(input_dict, recommended_items, exp_style=explanation_style)

    rec_dict = dict(dict())
    for iid in recommended_items:
        exp_dict = dict()
        if iid in movies.keys():
            movie_info = movies[iid]
            if iid in exp_output_dict.keys():
                explanation = exp_output_dict[iid]
                exp_dict['exp_style'] = (movie_info, explanation)
            else:
                explanation = "Hops, it seems that it is failed to generate explanation for this item."
                exp_dict['exp_style'] = (movie_info, explanation)

            rec_dict[iid] = exp_dict
    rec_dicts.append(rec_dict)
    request.session['exp_dicts_3'] = rec_dicts
    return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})


# @cache_page(60 * 15)
def re_eval_view3(request):
    template_name = 'recsys_demo/re_eval_3.html'
    current_user_id = request.session['current_user_metadata']['user_id']
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback_top1_2')
        user_info.feed_back_re_top_1_3 = str(feedback_dict)
        # print("feed_back_re_top_1: " + feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    rec_dicts = list()

    # recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']
    # for recommendation_approach in recommendation_approaches:
    rec_dict = dict()
    recommended_items = [request.session['recommended_items'][2]]
    for iid in recommended_items:
        if iid in movies.keys():
            movie_info = movies[iid]
            rec_dict[iid] = movie_info
    rec_dicts.append(rec_dict)
    exp_dicts_3 = request.session['exp_dicts_3']
    return render(request, template_name=template_name, context={'recomm_dicts': rec_dicts, 'exp_dicts_3': exp_dicts_3})


# @cache_page(60 * 15)
def explanation_view(request):
    template_name = 'recsys_demo/explanation.html'

    current_user_id = request.session['current_user_metadata']['user_id']
    # save the feedback of the current user to the database
    if request.is_ajax():
        user_info = UserInfo.objects.get(id=current_user_id)
        # print(user_info)
        feedback_dict = request.POST.get('feedback')
        # print("feedback_dict_1: " + feedback_dict)
        user_info.feed_back_list = str(feedback_dict)
        user_info.save()
        message = 'update successful'
        response = HttpResponse(message, content_type="text/html")
        return response

    # explanation_styles = ['basic', 'pem_cem']
    # recommendation_approaches = ['recommended_items_cbf', 'recommended_items_svd', 'recommended_items_hybride']

    rec_dicts = list()
    # for recommendation_approach in recommendation_approaches:
    input_dict = request.session['user_inputs_ratings']
    recommended_items = request.session['recommended_items']
    explanation_style = request.session['explanation_style']
    exp_output_dict = exp_generator(input_dict, recommended_items, exp_style=explanation_style)

    user_info = UserInfo.objects.get(id=current_user_id)
    user_info.num_exp_top_5_list = str(len(exp_output_dict.keys()))
    user_info.save()

    rec_dict = dict(dict())
    for iid in recommended_items:
        exp_dict = dict()
        if iid in movies.keys():
            movie_info = movies[iid]
            if iid in exp_output_dict.keys():
                explanation = exp_output_dict[iid]
                exp_dict['exp_style'] = (movie_info, explanation)
            else:
                explanation = "Hops, it seems that it is failed to generate explanation for this item."
                exp_dict['exp_style'] = (movie_info, explanation)
            rec_dict[iid] = exp_dict
    rec_dicts.append(rec_dict)
    return render(request, template_name=template_name, context={'rec_dicts': rec_dicts})
