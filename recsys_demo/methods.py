import requests
import os
import heapq
import pickle
import pandas as pd
import numpy as np
import random
import math

from django.conf import settings
from scipy.spatial.distance import cosine
from surprise import SVD, Reader, Dataset
from SPARQLWrapper import SPARQLWrapper2
from collections import defaultdict

movies = dict()
iid_uri_dict = dict()
uri_iid_dict = dict()

PROPERTIE_LABEL_DICT = {
    'http://purl.org/dc/terms/subject': 'category',
    'http://dbpedia.org/ontology/musicComposer': 'music composer',
    'http://dbpedia.org/ontology/starring': 'actor',
    'http://dbpedia.org/ontology/director': 'director',
    'http://dbpedia.org/ontology/distributor': 'distributor',
    'http://dbpedia.org/ontology/writer': 'writer',
    'http://dbpedia.org/ontology/producer': 'producer',
    'http://dbpedia.org/ontology/cinematography': 'cinematography',
    'http://dbpedia.org/ontology/editing': 'editing',
}


def init():
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_emb_v4.pickle'), 'rb') as file:
        global dict_item_embedding
        dict_item_embedding = pickle.load(file)

    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/svd_pretrain_demo.pickle'), 'rb') as svd_model:
        global pretrain_svd
        pretrain_svd = pickle.load(svd_model)

    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/Mapping_upgrated_v4.csv'), 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line != None and line != '':
                uri, iid = line.split('::')[0], line.split('::')[1]
                iid_uri_dict[iid] = uri
                uri_iid_dict[uri] = iid

    global nb_movie
    query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        select (count(distinct ?s) as ?nb_movie)
        where {
        ?s rdf:type dbo:Film .
        }
    """
#     sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        nb_movie = int(result["nb_movie"].value)


def parse_movie_metadata():
    # movies_by_id = dict()
    with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/movies_v4.csv'), 'r') as movie_data:
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
        # global nb_movie
        # nb_movie = len(movies.keys())
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
    return top_n


def svd_predict(u_f, candidate):
    candidate_factor = pretrain_svd.qi[pretrain_svd.trainset.to_inner_iid(candidate)]

    rating =np.dot(candidate_factor, u_f)

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


def hybride_recommender(n, input_dict):
    """Hybrid recommendation system which combines CBF and SVD
        parameters:
            n: number of recommendations to make
            input_dict: user input for building user profile
    """

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
        predicted_r_svd = svd_predict(user_factor, candidate)
        predicted_r_cbf = cbf_predict(input_dict, candidate)
        predicted_r = (predicted_r_cbf + predicted_r_svd) / 2
        top_n.append((candidate, predicted_r))
    top_n = heapq.nlargest(n, top_n, key=lambda x:x[1])
    return top_n


def generate_queries(input_dict, recommended_items):
    items_profil = [iid_uri_dict[iid] for iid in input_dict.keys()]
    items_rec = [iid_uri_dict[iid] for iid in [rec_item for rec_item, pred_r in recommended_items]]

    filter_profil = "filter ("
    for item in items_profil:
        item = "<" + item + ">"
        filter_profil += "?i_prof = " + item + " || "
    filter_profil = filter_profil[:-3]
    filter_profil += ")"

    filter_rec = "filter ("
    for item in items_rec:
        item = "<" + item + ">"
        filter_rec += "?i_rec = " + item + " || "
    filter_rec = filter_rec[:-3]
    filter_rec += ")"

    query_basic_builder = """
        select distinct ?o
        where {
         ?i_prof ?p ?o .
         ?i_rec ?p ?o .
         """ + filter_profil + "\n" + filter_rec + """
         filter regex(str(?o), \"http://dbpedia.org/resource\") filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
        }
        """

    query_broader_builder = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        select distinct ?o3 ?o1 ?o2
        where {
         ?i_prof ?p ?o1 .
         ?i_rec ?p ?o2 .
         ?o1 ?p1 ?o3 .
         ?o2 ?p1 ?o3 .
         """ + filter_profil + "\n" + filter_rec + """
         filter regex(str(?o3), \"http://dbpedia.org/resource\") 
         filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
         filter (?p1 = dct:subject || ?p1 = skos:broader)
        }
        """

    return filter_profil, filter_rec, query_basic_builder, query_broader_builder


def basic_builder(query):
    candidate_properties = list()
#     sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        o = result["o"].value
        candidate_properties.append(o)
    return candidate_properties


def broader_builder(query):
    candidate_properties = defaultdict(set)
#     sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        o3 = result["o3"].value
        o1 = result["o1"].value
        o2 = result["o2"].value
        candidate_properties[o3].add(o1)
        candidate_properties[o3].add(o2)
    return candidate_properties


def compute_p_score(p, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec):
    i_u = len(input_dict.keys())
    i_r = len(recommended_items)
    query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        select (count(distinct ?i_prof) as ?nb_i_prof) (count(distinct ?i_rec) as ?nb_i_rec) (count(distinct ?movie) as ?nb_movie)
        where {
            ?movie rdf:type dbo:Film .
            ?movie ?p <""" + p + """> .
            ?i_prof ?p <""" + p + """> . 
            ?i_rec ?p <""" + p + """> .""" + "\n" + filter_profil + "\n" + filter_rec + """
        }
    """
#         sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        nb_i_prof = int(result["nb_i_prof"].value)
        nb_i_rec = int(result["nb_i_rec"].value)
        p_freq = int(result["nb_movie"].value)

    idf_p = 0 if p_freq == 0 else math.log(nb_movie / p_freq)
    p_score = (alpha * nb_i_prof / i_u + beta * nb_i_rec / i_r) * idf_p
    return p_score


def rank_p_basic(candidate_properties, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec):
    basic_p_scores = dict()
    for p in candidate_properties:
        p_score = compute_p_score(p, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec)

        basic_p_scores[p] = p_score
    return basic_p_scores


def rank_p_broader(candidate_properties_broader, basic_p_scores, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec):
    broader_p_scores = dict()
    for b in candidate_properties_broader.keys():
        basic_properties = candidate_properties_broader[b]
        b_score = 0

        for basic_p in basic_properties:
            if basic_p not in basic_p_scores.keys():
                b_score += compute_p_score(basic_p, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec)
            else:
                b_score += basic_p_scores[basic_p]

        query1 = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dct: <http://purl.org/dc/terms/>
            
            select (count(distinct ?movie) as ?nb_movie)
            where {
                ?movie rdf:type dbo:Film .
                ?movie ?p ?po .
                ?po ?p1 <""" + b + """> .
                filter (?p1 = dct:subject || ?p1 = skos:broader)
            }
        """
#         sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
        sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
        sparql.setQuery(query1)
        for result in sparql.query().bindings:
            b_freq = int(result["nb_movie"].value)

        idf_b = 0 if b_freq == 0 else math.log(nb_movie / b_freq)
        b_score = b_score * idf_b
        broader_p_scores[b] = b_score
    return broader_p_scores


def basic_patterns(top_k_properties, filter_profil, filter_rec):
    patterns_dict = dict()

    filter_top_k_p = "filter ("
    for item in top_k_properties:
        item = "<" + item + ">"
        filter_top_k_p += "?o = " + item + " || "
    filter_top_k_p = filter_top_k_p[:-3]
    filter_top_k_p += ")"

    query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select distinct ?i_prof ?p ?label_o ?i_rec
        where {
            ?i_prof ?p ?o .
            ?i_rec ?p ?o . """ + "\n" + filter_profil + "\n" + filter_rec + "\n" + filter_top_k_p + """\n
            ?o rdfs:label ?label_o .
            filter (lang(?label_o) = 'en')
            filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
            }
    """
#     print(query)
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        i_prof = result["i_prof"].value
        p = result["p"].value
        o = result["label_o"].value
        i_rec = result["i_rec"].value
        if i_rec not in patterns_dict.keys():
            predicate_dict = dict()
            if p not in predicate_dict.keys():
                po_dict = defaultdict(list)
                po_dict[o].append(i_prof)
                predicate_dict[p] = po_dict
                patterns_dict[i_rec] = predicate_dict
            else:
                predicate_dict[p][o].append(i_prof)
                patterns_dict[i_rec] = predicate_dict
        else:
            predicate_dict = patterns_dict[i_rec]
            if p not in predicate_dict.keys():
                po_dict = defaultdict(list)
                po_dict[o].append(i_prof)
                predicate_dict[p] = po_dict
                patterns_dict[i_rec] = predicate_dict
            else:
                predicate_dict[p][o].append(i_prof)
                patterns_dict[i_rec] = predicate_dict
    return patterns_dict


def broader_patterns(top_k_properties, filter_profil, filter_rec):
    patterns_dict = dict()

    filter_top_k_p = "filter ("
    for item in top_k_properties:
        item = "<" + item + ">"
        filter_top_k_p += "?o3 = " + item + " || "
    filter_top_k_p = filter_top_k_p[:-3]
    filter_top_k_p += ")"

    query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        select distinct ?i_prof ?p ?label_o ?i_rec
        where {
            ?i_prof ?p ?o1 .
            ?i_rec ?p ?o2 .
            ?o1 ?p1 ?o3 .
            ?o2 ?p1 ?o3 .
            """ + "\n" + filter_profil + "\n" + filter_rec + "\n" + filter_top_k_p + """\n
            ?o3 rdfs:label ?label_o .
            filter (lang(?label_o) = 'en')
            filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
            filter (?p1 = dct:subject || ?p1 = skos:broader)
            }
    """
#     print(query)
    sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    for result in sparql.query().bindings:
        i_prof = result["i_prof"].value
        p = result["p"].value
        o = result["label_o"].value
        i_rec = result["i_rec"].value
        if i_rec not in patterns_dict.keys():
            predicate_dict = dict()
            if p not in predicate_dict.keys():
                po_dict = defaultdict(list)
                po_dict[o].append(i_prof)
                predicate_dict[p] = po_dict
                patterns_dict[i_rec] = predicate_dict
            else:
                predicate_dict[p][o].append(i_prof)
                patterns_dict[i_rec] = predicate_dict
        else:
            predicate_dict = patterns_dict[i_rec]
            if p not in predicate_dict.keys():
                po_dict = defaultdict(list)
                po_dict[o].append(i_prof)
                predicate_dict[p] = po_dict
                patterns_dict[i_rec] = predicate_dict
            else:
                predicate_dict[p][o].append(i_prof)
                patterns_dict[i_rec] = predicate_dict
    return patterns_dict


def generate_exp_from_pattern(pattern_dict):
    explanation = ""
    if len(pattern_dict.keys()) == 1:
        explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['beacause', 'since'])

        ppt = next(iter(pattern_dict))
        po_dict = pattern_dict[ppt]
        ppt = PROPERTIE_LABEL_DICT[ppt] if ppt in PROPERTIE_LABEL_DICT.keys() else ppt
        for key, value in po_dict.items():
            movies_exp = " movies" if len(value) > 1 else " movie"
            if len(value) == 1:
                m_titles_exp = "<b>" + movies[uri_iid_dict[value[0]]]['title'] + "</b>"
            else:
                m_titles_exp = ""
                for m in value:
                    m_titles_exp += "<b>" + movies[uri_iid_dict[m]]['title'] + "</b>" + ", "
            explanation += " You " + random.choice(['love', 'like', 'rate']) + movies_exp + " whose " + ppt + " is " + "<i>" + key + "</i>" + " as " + m_titles_exp + ". "
        return explanation
    else:
        count = 1
        for ppt in pattern_dict.keys():
            if count == 1:
                explanation += "We " + random.choice(['recommend', 'suggest', 'provide']) + " you this movie " + random.choice(['beacause', 'since'])
            else:
                explanation += random.choice(['Furthermore', 'Moreover', 'In addition']) + ", we " + random.choice(['recommend', 'suggest', 'provide']) + " you it " + random.choice(['beacause', 'since'])

            po_dict = pattern_dict[ppt]
            ppt = PROPERTIE_LABEL_DICT[ppt] if ppt in PROPERTIE_LABEL_DICT.keys() else ppt
            for key, value in po_dict.items():
                movies_exp = " movies" if len(value) > 1 else " movie"
                if len(value) == 1:
                    m_titles_exp = "<b>" + movies[uri_iid_dict[value[0]]]['title'] + "</b>"
                else:
                    m_titles_exp = ""
                    for m in value:
                        m_titles_exp += "<b>" + movies[uri_iid_dict[m]]['title'] + "</b>" + ", "
                explanation += " You " + random.choice(['love', 'like', 'rate']) + movies_exp + " whose " + ppt + " is "+ "<i>" + key + "</i>" + " as " + m_titles_exp + ". "
            count += 1
        return explanation


def basic_exp_generator(input_dict, recommended_items, alpha=0.5, beta=0.5, k=3):
    # generate queries
    filter_profil, filter_rec, query_basic_builder, query_broader_builder = generate_queries(input_dict, recommended_items)
    # filter properties to get overlap ones
    candidate_properties = basic_builder(query_basic_builder)
    # scoring these properties
    basic_p_scores = rank_p_basic(candidate_properties, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec)
    # extract the top-k properties
    top_properties = list({k: v for k, v in sorted(basic_p_scores.items(), key=lambda item: item[1], reverse=True)})[:k]
    # generate patterns for explanation
    patterns_dict = basic_patterns(top_properties, filter_profil, filter_rec)
    # for each recommended movie, generate explanations
    exp_output_dict = dict()
    for rec_item in patterns_dict.keys():
        pattern = patterns_dict[rec_item]
        explantion = generate_exp_from_pattern(pattern)
        exp_output_dict[uri_iid_dict[rec_item]] = explantion
    return exp_output_dict


def broader_exp_generator(input_dict, recommended_items, alpha=0.5, beta=0.5, k=3):
    # generate queries
    filter_profil, filter_rec, query_basic_builder, query_broader_builder = generate_queries(input_dict, recommended_items)
    # filter properties to get overlap ones
    candidate_properties_basic = basic_builder(query_basic_builder)
    # scoring these properties
    basic_p_scores = rank_p_basic(candidate_properties_basic, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec)
    # filter properties to get overlap ones
    candidate_properties_broader = broader_builder(query_broader_builder)
    # scoring these properties
    broader_p_scores = rank_p_broader(candidate_properties_broader, basic_p_scores, input_dict, recommended_items, alpha, beta, filter_profil, filter_rec)
    # extract the top-k properties
    top_properties = list({k: v for k, v in sorted(broader_p_scores.items(), key=lambda item: item[1], reverse=True)})[:k]
    # generate patterns for explanation
    patterns_dict = broader_patterns(top_properties, filter_profil, filter_rec)
    # for each recommended movie, generate explanations
    exp_output_dict = dict()
    for rec_item in patterns_dict.keys():
        pattern = patterns_dict[rec_item]
        explantion = generate_exp_from_pattern(pattern)
        exp_output_dict[uri_iid_dict[rec_item]] = explantion
    return exp_output_dict