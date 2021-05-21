import heapq
import pandas as pd
import random

from scipy.spatial.distance import cosine
from surprise import SVD, Reader, Dataset

from .modules.explainer_v2 import *


movies = dict()
iid_uri_dict = dict()
uri_iid_dict = dict()


def init():
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_emb_v5.pickle'), 'rb') as file:
        global dict_item_embedding
        dict_item_embedding = pickle.load(file)

    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/svd_pretrain_demo.pickle'), 'rb') as svd_model:
        global pretrain_svd
        pretrain_svd = pickle.load(svd_model)

    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/Mapping_upgrated_v5.csv'), 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line != None and line != '':
                uri, iid = line.split('::')[0], line.split('::')[1]
                iid_uri_dict[iid] = uri
                uri_iid_dict[uri] = iid

    global loader
    loader = GraphLoader()

    global graph_for_explod
    graph_for_explod = GraphForExplod()

    global graph_for_proposed
    graph_for_proposed = GraphForProposed()


def parse_movie_metadata():
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/movies_v5.csv'), 'r') as movie_data:
        line = movie_data.readline()

        while line != None and line != '':
            movie = dict()
            id, title, release_date, poster_path, overview, french_title, en_fr_title = line.split("::::")[0], \
                                                             line.split("::::")[1], \
                                                             line.split("::::")[2], \
                                                             line.split("::::")[3], \
                                                             line.split("::::")[4], \
                                                             line.split("::::")[5], \
                                                             line.split("::::")[6]
            movie['title'] = title
            movie['release_date'] = release_date
            movie['poster_path'] = poster_path
            movie['overview'] = overview
            movie['french_title'] = french_title
            movie['en_fr_title'] = en_fr_title.strip("\n")
            movie['dbpedia_uri'] = iid_uri_dict[id]
            movies[id] = movie

            line = movie_data.readline()


def compute_sim(i, j):
    ITEM = 'http://example.org/rating_ontology/Item/Item_'
    i_emb = dict_item_embedding[ITEM + i]
    j_emb = dict_item_embedding[ITEM + j]
    return 1 - cosine(i_emb, j_emb)


def cbf_predict(input_dict, candidate):
    length_profil = len(input_dict.keys())
    rating = 0
    for item in input_dict.keys():
        sim_item_candidate = compute_sim(candidate, item)
        rating += sim_item_candidate
    return rating / length_profil


def cbf_recommender(n, input_dict):
    """Content-based recommender system
       parameters:
                n: number of recommendations to make
                input_dict: the user profil dictionnary
    """

    top_n = list()
    rated_items = input_dict.keys()
    candidate_items = [iid for iid in movies.keys() if iid not in rated_items]
    for candidate in candidate_items:
        predicted_r = cbf_predict(input_dict, candidate)
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    top_n = [item for item, pred in top_n]
    return top_n


def svd_predict(u_f, candidate):
    candidate_factor = pretrain_svd.qi[pretrain_svd.trainset.to_inner_iid(candidate)]

    rating = np.dot(candidate_factor, u_f)

    return rating


def svd_recommender(n, input_dict):
    """Matrix factorization model based recommender system
       parameters:
                n: number of recommendations to make
                input_dict: the user profil dictionnary
    """
    user = '99999'
    list_ratings = list()
    for iid, r in input_dict.items():
        list_ratings.append((user, iid, str(int(r)*2)))
    # print(list_ratings)
    df = pd.DataFrame(list_ratings, columns =['userID', 'itemID', 'rating'])
    reader = Reader(rating_scale=(0, 10))
    data = Dataset.load_from_df(df=df, reader=reader)
    train = data.build_full_trainset()

    lr_all, n_epochs, n_factors, reg_all = 0.0019, 50, 199, 0.0132
    svd = SVD(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all, reg_all=reg_all)
    # svd = SVD()
    svd.fit(train)
    user_factor = svd.pu[svd.trainset.to_inner_uid(user)]

    top_n = list()
    rated_items = input_dict.keys()
    candidate_items = [iid for iid in movies.keys() if iid not in rated_items]
    for candidate in candidate_items:
        predicted_r = svd_predict(user_factor, candidate)
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    top_n = [item for item, pred in top_n]
    return top_n


def hybride_recommender(n, input_dict):
    """Hybrid recommendation system which combines CBF and SVD
        parameters:
            n: number of recommendations to make
            input_dict: user input for building user profile
    """

    user = '99999'
    list_ratings = list()
    for iid, r in input_dict.items():
        list_ratings.append((user, iid, str(int(r)*2)))
    # print(list_ratings)
    df = pd.DataFrame(list_ratings, columns =['userID', 'itemID', 'rating'])
    reader = Reader(rating_scale=(0, 10))
    data = Dataset.load_from_df(df=df, reader=reader)
    train = data.build_full_trainset()
    lr_all, n_epochs, n_factors, reg_all = 0.0019, 50, 199, 0.0132
    svd = SVD(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all, reg_all=reg_all)
    svd.fit(train)
    user_factor = svd.pu[svd.trainset.to_inner_uid(user)]

    top_n = list()
    rated_items = input_dict.keys()
    candidate_items = [iid for iid in movies.keys() if iid not in rated_items]

    for candidate in candidate_items:
        predicted_r_svd = svd_predict(user_factor, candidate)
        predicted_r_cbf = cbf_predict(input_dict, candidate)
        predicted_r = (predicted_r_cbf + predicted_r_svd) / 2
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    top_n = [item for item, pred in top_n]
    return top_n


def generate_exp_from_pattern_pem(pattern):
    explanation = ""
    if len(pattern) == 0:
        explanation = 'Hops, it seems that it is failed to generate explanation for this item.'
        return explanation
    else:
        count = 1
        for pattern_item in pattern:
            ppt = pattern_item[5]
            items_profile = list(pattern_item[4])
            if len(items_profile) > 5:
                if count == 1:
                    explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['because', 'since', 'as'])
                    explanation += " you " + random.choice(['love', 'like', 'prefer']) + " movies whose category is " + "<b>" + str(ppt) + "</b>" + " as " + str(len(items_profile)) + " of your profile items."
                    count += 1
                else:
                    explanation += random.choice([' Furthermore', ' Moreover', ' In addition']) + ", we " + random.choice(['recommend', 'suggest', 'provide']) + " you it " + random.choice(['because', 'since', 'as'])
                    explanation += " you " + random.choice(['love', 'like', 'prefer']) + " movies whose category is " + "<b>" + str(ppt) + "</b>" + " as " + str(len(items_profile)) + " of your profile items."
            else:
                if count == 1:
                    explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['because', 'since', 'as'])
                else:
                    explanation += random.choice([' Furthermore', ' Moreover', ' In addition']) + ", we " + random.choice(['recommend', 'suggest', 'provide']) + " you it " + random.choice(['because', 'since', 'as'])

                movies_exp = " movies" if len(items_profile) > 1 else " movie"

                if len(items_profile) == 1:
                    m_titles_exp = "<i>" + movies[items_profile[0]]['title'] + "</i>"
                elif len(items_profile) == 2:
                    m_titles_exp = "<i>" + movies[items_profile[0]]['title'] + "</i>" + " and " + "<i>" + movies[items_profile[1]]['title'] + "</i>"
                else:
                    m_titles_exp = ""
                    for m in items_profile[:(len(items_profile) - 2)]:
                        m_titles_exp += "<i>" + movies[m]['title'] + "</i>" + ", "
                    m_titles_exp += "<i>" + movies[items_profile[-2]]['title'] + "</i>" + " and " + "<i>" + movies[items_profile[-1]]['title'] + "</i>"
                explanation += " you " + random.choice(['love', 'like', 'prefer']) + movies_exp + " whose " + random.choice(['category', 'genre']) + " is " + "<b>" + str(ppt) + "</b>" + " as " + m_titles_exp + "."
                count += 1
        return explanation


def generate_exp_from_pattern_explod(pattern):
    explanation = ""
    if len(pattern) == 0:
        explanation = 'Hops, it seems that it is failed to generate explanation for this item.'
        return explanation
    else:
        count = 1
        for pattern_item in pattern:
            ppt = pattern_item[3]
            items_profile = pattern_item[2]
            if count == 1:
                explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['because', 'since', 'as'])
            else:
                explanation += random.choice([' Furthermore', ' Moreover', ' In addition']) + ", we " + random.choice(['recommend', 'suggest', 'provide']) + " you it " + random.choice(['because', 'since', 'as'])

            movies_exp = " movies" if len(items_profile) > 1 else " movie"

            if len(items_profile) == 1:
                m_titles_exp = "<i>" + movies[items_profile[0]]['title'] + "</i>"
            elif len(items_profile) == 2:
                m_titles_exp = "<i>" + movies[items_profile[0]]['title'] + "</i>" + " and " + "<i>" + movies[items_profile[1]]['title'] + "</i>"
            else:
                m_titles_exp = ""
                for m in items_profile[:(len(items_profile) - 2)]:
                    m_titles_exp += "<i>" + movies[m]['title'] + "</i>" + ", "
                m_titles_exp += "<i>" + movies[items_profile[-2]]['title'] + "</i>" + " and " + "<i>" + movies[items_profile[-1]]['title'] + "</i>"
            explanation += " you " + random.choice(['love', 'like', 'prefer']) + movies_exp + " whose " + random.choice(['category', 'genre']) + " is " + "<b>" + str(ppt) + "</b>" + " as " + m_titles_exp + "."
            count += 1
        return explanation


def generate_exp_from_pattern_cem(pattern_dict):
    explanation = ""
    explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['because', 'since', 'as'])
    if len(pattern_dict.keys()) == 1:
        for key, value in pattern_dict.items():
            percentage = round(value * 100, 2)
            m_title = " <b>" + movies[key]['title'] + "</b> "
            explanation += " <b>" + str(percentage) + "%" + "</b> " + "of users interested by " + m_title
        explanation += " are likely to enjoy this movie."
    else:
        for key, value in pattern_dict.items():
            percentage = round(value * 100, 2)
            m_title = " <b>" + movies[key]['title'] + "</b> " + ", "
            explanation += " <b>" + str(percentage) + "%" + "</b> " + "of users interested by " + m_title
        explanation = explanation[:(len(explanation)-2)]
        explanation += " are likely to enjoy this movie."
    if "of users interested by" in explanation:
        return explanation
    else:
        return "not possible"


def exp_generator(input_dict, recommended_items, exp_style):

    if exp_style == 'explod':
        explainer_explod = ExpLodBroader(loader, graph_for_explod, recommended_items=recommended_items, profile_items=input_dict)
        pattern_dict_explod = explainer_explod.explain()
        exp_output_dict_explod = dict()

        for rec_item in pattern_dict_explod.keys():
            pattern = pattern_dict_explod[rec_item]
            explantion = generate_exp_from_pattern_explod(pattern)
            exp_output_dict_explod[rec_item] = explantion
        return exp_output_dict_explod

    if exp_style == 'pem':
        explainer_proposed = ExpProposed(loader, graph_for_proposed, recommended_items=recommended_items, profile_items=input_dict)
        pattern_dict_pem, patterns_dict_cem = explainer_proposed.explain()
        exp_output_dict_pem = dict()

        for rec_item in pattern_dict_pem.keys():
            pattern = pattern_dict_pem[rec_item]
            explantion = generate_exp_from_pattern_pem(pattern)
            exp_output_dict_pem[rec_item] = explantion
        return exp_output_dict_pem

    if exp_style == 'cem':
        explainer_proposed = ExpProposed(loader, graph_for_proposed, recommended_items=recommended_items, profile_items=input_dict)
        pattern_dict_pem, patterns_dict_cem = explainer_proposed.explain()
        exp_output_dict_cem = dict()
        for rec_item in patterns_dict_cem.keys():
            pattern = patterns_dict_cem[rec_item]
            explantion = generate_exp_from_pattern_cem(pattern)
            if not explantion == "not possible":
                exp_output_dict_cem[rec_item] = explantion
        return exp_output_dict_cem