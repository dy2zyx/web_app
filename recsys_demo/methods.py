import requests
import os
import heapq
import pickle
import pandas as pd
import numpy as np

from django.conf import settings
from scipy.spatial.distance import cosine
from surprise import SVD, Reader, Dataset

movies = dict()


def init():
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_emb_v3.pickle'), 'rb') as file:
        global dict_item_embedding
        dict_item_embedding = pickle.load(file)

    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/svd_pretrain_demo.pickle'), 'rb') as svd_model:
        global pretrain_svd
        pretrain_svd = pickle.load(svd_model)


def parse_movie_metadata():
    # movies_by_id = dict()
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/movies_v3.csv'), 'r') as movie_data:
        line = movie_data.readline()

        while line != None and line != '':
            # print(line)
            movie = dict()
            id, title, release_date, poster_path, overview = line.split("::::")[0], \
                                                             line.split("::::")[1], \
                                                             line.split("::::")[2], \
                                                             line.split("::::")[3], \
                                                             line.split("::::")[4]
            movie['title'] = title
            movie['release_date'] = release_date
            movie['poster_path'] = poster_path
            movie['overview'] = overview
            movies[id] = movie

            line = movie_data.readline()
    # return movies_by_id


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
        if int(input_dict[item]) > 6:
            rating += sim_item_candidate
        else:
            rating -= sim_item_candidate
    return rating / length_profil


def cbf_recommender(n, input_dict):
    top_n = list()
    rated_items = input_dict.keys()
    candidate_items = [iid for iid in movies.keys() if iid not in rated_items]
    for candidate in candidate_items:
        predicted_r = cbf_predict(input_dict, candidate)
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    return top_n


def svd_predict(u_f, candidate):
    candidate_factor = pretrain_svd.qi[pretrain_svd.trainset.to_inner_iid(candidate)]

    rating =np.dot(candidate_factor, u_f)

    return rating


def svd_recommender(n, input_dict):
    user = '99999'
    list_ratings = list()
    for iid, r in input_dict.items():
        list_ratings.append((user, iid, r))
    df = pd.DataFrame(list_ratings, columns =['userID', 'itemID', 'rating'])
    reader = Reader(rating_scale=(0, 10))
    data = Dataset.load_from_df(df=df, reader=reader)
    train = data.build_full_trainset()
    svd = SVD()
    svd.fit(train)
    user_factor = svd.pu[svd.trainset.to_inner_uid(user)]

    top_n = list()
    rated_items = input_dict.keys()
    candidate_items = [iid for iid in movies.keys() if iid not in rated_items]
    for candidate in candidate_items:
        predicted_r = svd_predict(user_factor, candidate)
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    return top_n
