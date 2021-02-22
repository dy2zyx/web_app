import heapq
import pickle
import math
import pandas as pd
import numpy as np
import random
import os

from surprise import SVD, Reader, Dataset
from django.conf import settings
from scipy.spatial.distance import cosine
from collections import defaultdict
from SPARQLWrapper import SPARQLWrapper2, SPARQLWrapper, JSON


class ExpKGE:
    """
    The proposed KG embedding based approach.
    The parameters:
        recommender: the algorithm used for generate recommandations. Values should be in ['cbf', 'svd', 'hybrid']
        nb_po: number of properties used for generated explanations
        nb_rec: number of top-N items recommended for user
        input_dict: user input representing rating dict {'iid': 'rating'}
    """
    def __init__(self, recommended_items=None, nb_po=3, input_dict=None, alpha=1, beta=0):
        # self.recommender = recommender
        self.nb_po = nb_po
        # self.nb_rec = nb_rec
        self.input_dict = input_dict
        self.alpha = alpha
        self.beta = beta
        self.movies = dict()
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_emb_v5.pickle'), 'rb') as file:
            self.dict_item_embedding = pickle.load(file)
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/movies_v5.csv'), 'r') as movie_data:
            line = movie_data.readline()

            while line != None and line != '':
                movie = dict()
                id, title, release_date, poster_path, overview = line.split("::::")[0], line.split("::::")[1], line.split("::::")[2], line.split("::::")[3], line.split("::::")[4]
                movie['title'] = title
                movie['release_date'] = release_date
                movie['poster_path'] = poster_path
                movie['overview'] = overview
                self.movies[id] = movie
                line = movie_data.readline()

        query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            select (count(distinct ?s) as ?nb_movie)
            where {
            ?s rdf:type dbo:Film .
            }
        """
        sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
        sparql.setQuery(query)
        for result in sparql.query().bindings:
            self.nb_movie = int(result["nb_movie"].value)

        self.PROPERTIE_LABEL_DICT = {
            'http://purl.org/dc/terms/subject': 'category',
            'http://dbpedia.org/ontology/musicComposer': 'music composer',
            'http://dbpedia.org/ontology/starring': 'actor',
            'http://dbpedia.org/ontology/director': 'director',
            'http://dbpedia.org/ontology/distributor': 'distributor',
            'http://dbpedia.org/ontology/writer': 'writer',
            'http://dbpedia.org/ontology/producer': 'producer',
            'http://dbpedia.org/ontology/cinematography': 'cinematography',
            'http://dbpedia.org/ontology/editing': 'editing',
            'http://dbpedia.org/property/starring': 'actor',
            'http://dbpedia.org/property/musicComposer': 'music composer',
            'http://dbpedia.org/property/director': 'director',
            'http://dbpedia.org/property/distributor': 'distributor',
            'http://dbpedia.org/property/writer': 'writer',
            'http://dbpedia.org/property/producer': 'producer',
            'http://dbpedia.org/property/cinematography': 'cinematography',
            'http://dbpedia.org/property/editing': 'editing',
        }

        self.iid_uri_dict, self.uri_iid_dict = self.mapper()
        # self.nb_movie = self.get_total_item_number()
        self.recommended_items = recommended_items

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_user_liked_items.pickle'), 'rb') as file:
            self.dict_user_liked_items = pickle.load(file)
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_liked_by_user.pickle'), 'rb') as file:
            self.dict_item_liked_by_users = pickle.load(file)
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/entropy_by_ppts_entire.pickle'), 'rb') as file:
            self.entropy_ppt_entire_population_dict = pickle.load(file)
        # with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/item_cluster_dict.pickle'), 'rb') as file:
        #     self.item_cluster_dict = pickle.load(file)

        item_property_objets = dict()
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/ickg_v5.nt'), 'r') as file:
            lines = file.readlines()
            for line in lines:
                i_uri = line.split('	')[0]
                label_property = line.split('	')[1][1:][:-1]
                objet = line.split('	')[2]
                if i_uri not in item_property_objets.keys():
                    property_objets = defaultdict(list)
                    property_objets[self.PROPERTIE_LABEL_DICT[label_property]].append(objet)
                    item_property_objets[i_uri] = property_objets
                else:
                    property_objets = item_property_objets[i_uri]
                    property_objets[self.PROPERTIE_LABEL_DICT[label_property]].append(objet)
                    item_property_objets[i_uri] = property_objets
        self.item_property_objets = item_property_objets
        self.ppt_orderedby_entropy = self.compute_ppt_order()

    def get_objects_by_item_and_property(self, iid, property_label):
        iid = '<http://example.org/rating_ontology/Item/Item_' + iid + '>'

        if iid in self.item_property_objets.keys():
            if property_label in self.item_property_objets[iid].keys():
                output = self.item_property_objets[iid][property_label]
                return output
            else:
                return list()
        else:
            return list()

    def compute_subpopu_entropy_by_profile_items(self):
        entropy_ppt_sub_popluation_dict = dict()

        for ppt_uri, ppt_label in self.PROPERTIE_LABEL_DICT.items():
            user_object_properties_list = list()
            for iid in self.input_dict.keys():
                item_object_properties_list = self.get_objects_by_item_and_property(iid, ppt_label)
                user_object_properties_list += item_object_properties_list

            user_object_properties_set = set(user_object_properties_list)

            H = 0
            for objet_property in user_object_properties_set:
                freq = user_object_properties_list.count(objet_property) / len(user_object_properties_list)
                H += freq * math.log2(freq)
            H_sub = -1 * H

            entropy_ppt_sub_popluation_dict[ppt_label] = H_sub

        return entropy_ppt_sub_popluation_dict

    def compute_ppt_order(self):
        H_total_dict = self.entropy_ppt_entire_population_dict
        H_sub_dict = self.compute_subpopu_entropy_by_profile_items()
        result_dict = dict()
        for ppt in H_total_dict.keys():
            result_dict[ppt] = (H_total_dict[ppt] - H_sub_dict[ppt]) / H_total_dict[ppt]
        return {k:v for k, v in sorted(result_dict.items(), key=lambda item: item[1], reverse=True)}

    def mapper(self):
        iid_uri_dict = dict()
        uri_iid_dict = dict()
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/Mapping_upgrated_v5.csv'), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line != None and line != '':
                    uri, iid = line.split('::')[0], line.split('::')[1]
                    iid_uri_dict[iid] = uri
                    uri_iid_dict[uri] = iid
        return iid_uri_dict, uri_iid_dict


    # def get_total_item_number(self):
    #     query = """
    #         PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    #         PREFIX dbo: <http://dbpedia.org/ontology/>
    #
    #         select (count(distinct ?s) as ?nb_movie)
    #         where {
    #         ?s rdf:type dbo:Film .
    #         }
    #     """
    #     sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
    #     sparql.setQuery(query)
    #     for result in sparql.query().bindings:
    #         nb_movie = int(result["nb_movie"].value)
    #     return nb_movie

    def generate_queries(self):
        items_profil = [self.iid_uri_dict[iid] for iid in self.input_dict.keys()]
        items_rec = [self.iid_uri_dict[iid] for iid in [rec_item for rec_item, pred_r in self.recommended_items]]

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
            select distinct ?p ?o
            where {
             ?i_prof ?p ?o .
             ?i_rec ?p ?o .
             """ + filter_profil + "\n" + filter_rec + """
             filter regex(str(?o), \"http://dbpedia.org/resource\") filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
             filter (?o != <http://dbpedia.org/resource/Category:English-language_films>)
             filter (?o != <http://dbpedia.org/resource/Category:American_films>)
            }
            """

        query_broader_builder = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            select distinct ?o3 ?o1 ?o2
            where {
             ?i_prof ?p ?o1 .
             ?i_rec ?p ?o2 .
             ?o1 skos:broader ?o3 .
             ?o2 skos:broader ?o3 .
             """ + filter_profil + "\n" + filter_rec + """
             filter regex(str(?o3), \"http://dbpedia.org/resource\") filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
            }
            """

        return filter_profil, filter_rec, query_basic_builder, query_broader_builder


    def basic_builder(self, query):
        candidate_properties = list()
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        for result in sparql.query().convert()["results"]["bindings"]:
            p = result["p"]["value"]
            o = result["o"]["value"]
            candidate_properties.append((p, o))
        # print(candidate_properties)
        return candidate_properties

    def compute_p_score(self, p, filter_profil, filter_rec):
        i_u = len(self.input_dict.keys())
        i_r = len(self.recommended_items)
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
    # sparql = SPARQLWrapper2("http://factforge.net/repositories/ff-news")
        sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
        sparql.setQuery(query)
        # results = sparql.query()
        for result in sparql.query().bindings:
            nb_i_prof = float(result["nb_i_prof"].value)
            nb_i_rec = float(result["nb_i_rec"].value)
            p_freq = float(result["nb_movie"].value)

        idf_p = 0 if p_freq == 0 else math.log2(self.nb_movie / p_freq)
        p_score = (self.alpha * nb_i_prof / i_u + self.beta * nb_i_rec / i_r) * idf_p
        return p_score

    def rank_p_basic(self, candidate_properties, filter_profil, filter_rec):
        basic_p_scores = dict()
        for p in candidate_properties:
            p_score = self.compute_p_score(p[1], filter_profil, filter_rec)
            basic_p_scores[p] = p_score
        ranked_ppts = list({k: v for k, v in sorted(basic_p_scores.items(), key=lambda item: item[1], reverse=True)}.items())
        norm_ranked_ppts = self.normalise_p_score(ranked_ppts)
        rerank_objetppt = self.rerank_objetppts(norm_ranked_ppts)
        return rerank_objetppt

    def normalise_p_score(self, ranked_ppt):
        result_list = list()
        max_score = ranked_ppt[0][1]
        min_score = ranked_ppt[-1][1]
        score_range = max_score - min_score
        for (ppt, objetppt), score in ranked_ppt:
            result_list.append(((ppt, objetppt), (score - min_score) / score_range))
        return result_list

    def rerank_objetppts(self, norm_ranked_objetppt_explod):
        reranked_ppt = list()
        for rank_ppt_explod in norm_ranked_objetppt_explod:
            if rank_ppt_explod[0][0] in self.PROPERTIE_LABEL_DICT.keys():
                ppt_label = self.PROPERTIE_LABEL_DICT[rank_ppt_explod[0][0]]
                final_score = round(self.ppt_orderedby_entropy[ppt_label] * rank_ppt_explod[1], 4)
                reranked_ppt.append((rank_ppt_explod[0], final_score))
            else:
                reranked_ppt.append((rank_ppt_explod[0], 0))
        reranked_ppt.sort(key=lambda item: item[1], reverse=True)
        return reranked_ppt

    def basic_patterns(self, all_properties):
        patterns_dict = dict()
        patterns_dict_cem = dict()
        for i_rec, pred in self.recommended_items:
            patterns_dict_cem[i_rec] = self.cf_exp_generator(i_rec)
            # similar_items = self.get_similar_items(i_rec)
            if len(all_properties) > 0:
                filter_all_p = "filter ("
                for item in all_properties:
                    item = "<" + item[0][1] + ">"
                    filter_all_p += "?o = " + item + " || "
                filter_all_p = filter_all_p[:-3]
                filter_all_p += ")"

                # items_profil = [self.iid_uri_dict[iid] for iid in similar_items]
                items_profil = [self.iid_uri_dict[iid] for iid in self.input_dict.keys()]
                filter_profil = "filter ("
                for item in items_profil:
                    item = "<" + item + ">"
                    filter_profil += "?i_prof = " + item + " || "
                filter_profil = filter_profil[:-3]
                filter_profil += ")"

                filter_rec = "filter (?i_rec = <" + self.iid_uri_dict[i_rec] + ">)"

                query = """
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    select distinct ?i_prof ?p ?o ?label_o ?i_rec
                    where {
                        ?i_prof ?p ?o .
                        ?i_rec ?p ?o . """ + "\n" + filter_profil + "\n" + filter_rec + "\n" + filter_all_p + """\n
                        ?o rdfs:label ?label_o .
                        filter (lang(?label_o) = 'en')
                        filter (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
                        }
                """
    #             print(query)
                sparql = SPARQLWrapper2("http://dbpedia.org/sparql")
                sparql.setQuery(query)
                commun_ppt = set()
                predicate_dict = dict()
                for result in sparql.query().bindings:
                    i_prof = result["i_prof"].value
                    p = result["p"].value
                    o = result["o"].value
                    o_label = result["label_o"].value
                    i_rec_label = result["i_rec"].value
                    commun_ppt.add(o)
                    if p not in predicate_dict.keys():
                        po_dict = defaultdict(list)
                        po_dict[(o, o_label)].append(i_prof)
                        predicate_dict[p] = po_dict
                    else:
                        predicate_dict[p][(o, o_label)].append(i_prof)
                top_k_ppt = [ppty[0][1] for ppty in all_properties if ppty[0][1] in commun_ppt][:self.nb_po]

                for predicate in predicate_dict.keys():
                    value_dict = predicate_dict[predicate]
                    for po_key in list(value_dict.keys()):
                        if not po_key[0] in top_k_ppt:
                            del value_dict[po_key]

                for predicate in list(predicate_dict.keys()):
                    value_dict = predicate_dict[predicate]
                    if not value_dict:
                        del predicate_dict[predicate]

                predicate_dict_new = dict()
                for po in top_k_ppt:
                    for ppt, ppt_values in predicate_dict.items():
                        ppt = ppt.replace('http://dbpedia.org/property/', 'http://dbpedia.org/ontology/') if 'http://dbpedia.org/property/' in ppt else ppt
                        for key, value in ppt_values.items():
                            if key[0] == po:
                                if ppt not in predicate_dict_new.keys():
                                    po_dict = defaultdict(list)
                                    po_dict[key] = value
                                    predicate_dict_new[ppt] = po_dict
                                else:
                                    predicate_dict_new[ppt][key] = value

                patterns_dict[i_rec] = predicate_dict_new

        return patterns_dict, patterns_dict_cem


    def exp_generator(self):
        # generate queries
        filter_profil, filter_rec, query_basic_builder, query_broader_builder = self.generate_queries()
        # filter properties to get overlap ones
        candidate_properties = self.basic_builder(query_basic_builder)
        # scoring these properties
        ranked_ppts = self.rank_p_basic(candidate_properties,  filter_profil, filter_rec)
        # extract the top-k properties
        all_properties = ranked_ppts[:80]
        # generate patterns for explanation

        patterns_dict, patterns_dict_cem = self.basic_patterns(all_properties)

        return patterns_dict, patterns_dict_cem

    # def get_similar_items(self, i_r):
    #     similar_items = list()
    #     cluster_ir = self.item_cluster_dict[i_r]
    #     for i_u, rating in self.input_dict.items():
    #         cluster_iu = self.item_cluster_dict[i_u]
    #         if cluster_ir == cluster_iu:
    #             similar_items.append(i_u)
    #     return similar_items

    def cf_exp_generator(self, i_rec):
        d = dict()
        for i_prof, rating in self.input_dict.items():
            if not len([user for user in self.dict_item_liked_by_users[i_prof]]) == 0:
                percentage = len([user for user in self.dict_item_liked_by_users[i_prof] if i_rec in self.dict_user_liked_items[user]]) / len([user for user in self.dict_item_liked_by_users[i_prof]])
                if percentage > 0:
                    d[i_prof] = percentage
        d = {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}
        return d