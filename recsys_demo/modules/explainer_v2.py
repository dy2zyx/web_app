import pickle
import numpy as np
import math
import os

from collections import defaultdict
from SPARQLWrapper import SPARQLWrapper2
from django.conf import settings
from scipy import stats


class DBpediaCategoryTree:
    def __init__(self):
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/node_children_dict_valid_avec_id.pickle'), 'rb') as file:
            self.node_children_dict_valid = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/node_parent_dict_valid_avec_id.pickle'), 'rb') as file:
            self.node_parent_dict_valid = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/movie_annotation_dict.pickle'), 'rb') as file:
            self.movie_annotation_dict = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/entity_label_dict.pickle'), 'rb') as file:
            self.entity_label_dict = pickle.load(file)

        self.total_nb_items = len(self.movie_annotation_dict.keys())


class GraphLoader(DBpediaCategoryTree):
    def __init__(self):
        super().__init__()


class GraphForExplod:
    def __init__(self):
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/annotation_counts_dict_explod.pickle'), 'rb') as file:
            self.annotation_counts_dict = pickle.load(file)


class GraphForProposed:
    def __init__(self):
        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/annotation_counts_dict.pickle'), 'rb') as file:
            self.annotation_counts_dict = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/all_direct_annotations.pickle'), 'rb') as file:
            self.all_direct_annotations = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_user_liked_items.pickle'), 'rb') as file:
            self.dict_user_liked_items = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/dict_item_liked_by_user.pickle'), 'rb') as file:
            self.dict_item_liked_by_users = pickle.load(file)

        with open(os.path.join(settings.BASE_DIR, 'recsys_demo/static/recsys_demo/data/nodes_parse_post_order_new.pickle'), 'rb') as file:
            self.nodes_parse_post_order = pickle.load(file)

class ExpLodBroader:
    def __init__(self, loader, dbpedia_annotation, profile_items=None, recommended_items=None, nb_po=3, alpha=0.5, beta=0.5):
        self.profile_items = profile_items
        self.recommended_items = recommended_items
        self.nb_po = nb_po
        self.alpha = alpha
        self.beta = beta
        self.node_children_dict_valid = loader.node_children_dict_valid
        self.node_parent_dict_valid = loader.node_parent_dict_valid
        self.movie_annotation_dict = loader.movie_annotation_dict
        self.entity_label_dict = loader.entity_label_dict
        self.annotation_counts_dict = dbpedia_annotation.annotation_counts_dict
        self.total_nb_items = loader.total_nb_items

    def get_properties(self):
        ppt_item_profil_dict = defaultdict(set)
        ppt_item_rec_dict = defaultdict(set)
        for item in self.profile_items.keys():
            for ppt in self.movie_annotation_dict[item]:
                ppt_item_profil_dict[ppt].add(item)

        for item in self.recommended_items:
            for ppt in self.movie_annotation_dict[item]:
                ppt_item_rec_dict[ppt].add(item)
        return ppt_item_profil_dict, ppt_item_rec_dict

    def compute_property_scores(self, ppt_item_profil_dict, ppt_item_rec_dict):
        profile_size = len(self.profile_items.keys())
        recommendation_size = len(self.recommended_items)
        ppt_score_dict = dict()

        parents_profile_dict = self.get_parents(ppt_item_profil_dict)
        parents_rec_dict = self.get_parents(ppt_item_rec_dict)
        commun_ppts = set(parents_profile_dict.keys()).intersection(set(parents_rec_dict.keys()))

        all_properties = set(ppt_item_profil_dict.keys()).union(set(ppt_item_rec_dict.keys()))

        for ppt in all_properties:
            nb_i_prof = len(ppt_item_profil_dict[ppt])
            nb_i_rec = len(ppt_item_rec_dict[ppt])
            nb_item_described_by_ppt = self.annotation_counts_dict[ppt]
            idf_ppt = math.log(self.total_nb_items / nb_item_described_by_ppt)
            ppt_score_dict[ppt] = (self.alpha * nb_i_prof / profile_size + self.beta * nb_i_rec / recommendation_size) * idf_ppt

        results = list()
        for broader_ppt in commun_ppts:
            associated_items = parents_profile_dict[broader_ppt].union(parents_rec_dict[broader_ppt])
            nb_item_described_by_ppt = self.annotation_counts_dict.get(broader_ppt)
            idf_broader_ppt = 0 if nb_item_described_by_ppt is None else math.log(self.total_nb_items / nb_item_described_by_ppt)
            child_ppts = set(self.node_children_dict_valid[broader_ppt]).intersection(all_properties)
            score_broader_ppt = np.sum([ppt_score_dict[child] for child in child_ppts]) * idf_broader_ppt
            results.append((score_broader_ppt, broader_ppt, associated_items))
        results.sort(key=lambda x:x[0], reverse=True)
        return results[:self.nb_po]

    def get_parents(self, ppt_item_dict):
        parents_dict = defaultdict(set)
        for ppt in ppt_item_dict.keys():
            parents = self.node_parent_dict_valid[ppt]
            for parent in parents:
                parents_dict[parent] = parents_dict[parent].union(ppt_item_dict[ppt])
        return parents_dict

    def explain(self):
        ppt_item_profil_dict, ppt_item_rec_dict = self.get_properties()
        results = self.compute_property_scores(ppt_item_profil_dict, ppt_item_rec_dict)
        result_dict = defaultdict(list)
        for result in results:
            score, ppt, associated_items = result[0], result[1], result[2]
            recommendations = set(self.recommended_items).intersection(associated_items)
            profile_items = [item for item in associated_items if item not in recommendations]
            for rec in recommendations:
                result_dict[rec].append((ppt, score, profile_items, self.get_entity_label(ppt)))
        return result_dict

    def get_entity_label(self, entity):
        label = self.entity_label_dict[entity] if entity in self.entity_label_dict.keys() else self.entity_to_label(entity)
        label.strip('\n')
        return label

    def entity_to_label(self, entity):
        label = entity.replace('<http://dbpedia.org/resource/Category:', '')
        label = label.replace('>', '')
        label = label.replace('_', ' ')
        return label


class ExpProposed:
    def __init__(self, loader, dbpedia_annotation, profile_items=None, recommended_items=None, nb_po=3):
        self.profile_items = profile_items
        self.recommended_items = recommended_items
        self.nb_po = nb_po
        self.node_children_dict_valid = loader.node_children_dict_valid
        self.node_parent_dict_valid = loader.node_parent_dict_valid
        self.movie_annotation_dict = loader.movie_annotation_dict
        self.entity_label_dict = loader.entity_label_dict
        self.annotation_counts_dict = dbpedia_annotation.annotation_counts_dict
        self.total_nb_items = loader.total_nb_items
        self.all_direct_annotations = dbpedia_annotation.all_direct_annotations
        self.dict_item_liked_by_users = dbpedia_annotation.dict_item_liked_by_users
        self.dict_user_liked_items = dbpedia_annotation.dict_user_liked_items
        self.nodes_parse_post_order = dbpedia_annotation.nodes_parse_post_order
        self.ppt_item_profil_dict = self.get_properties_prof()
        self.visited = set()

    def post_order(self, root):
        self.visited.clear()
        root_to_post = defaultdict(list)
        root_to_post[root] = list()
        self.post_order_rec(root_to_post[root], root)
        return root_to_post

    def post_order_rec(self, post_order_list, current_node):
        self.visited.add(current_node)
        for node in self.node_children_dict_valid[current_node]:
            if node not in self.visited:
                self.post_order_rec(post_order_list, node)
        post_order_list.append(current_node)

    def get_ancestors(self, seed_node, already_done):
        if seed_node not in already_done:
            ancestors_todo = [seed_node]
        while len(ancestors_todo) != 0:
            node_current = ancestors_todo[0]
            already_done.add(node_current)
            parents = self.node_parent_dict_valid[node_current]
            for parent in parents:
                if not parent in already_done and not parent in ancestors_todo:
                    ancestors_todo.append(parent)
            ancestors_todo.remove(node_current)
        return already_done

    def get_descendents(self, seed_node, already_done):
        if seed_node not in already_done:
            descendents_todo = [seed_node]
        while len(descendents_todo) != 0:
            node_current = descendents_todo[0]
            already_done.add(node_current)
            children = self.node_children_dict_valid[node_current]
            for child in children:
                if not child in already_done and not child in descendents_todo:
                    descendents_todo.append(child)
            descendents_todo.remove(node_current)
        return already_done

    def get_chemin(self, seed_node, already_done, dest_node):
        paths=defaultdict(list)
        if seed_node not in already_done:
            ancestors_todo = [seed_node]
        while len(ancestors_todo) != 0:
            node_current = ancestors_todo[0]
            already_done.add(node_current)
            parents = self.node_parent_dict_valid[node_current]
            for parent in parents:
                if not parent in already_done and not parent in ancestors_todo:
                    if not paths[node_current] is None:
                        cp_path = paths[node_current].copy()
                        cp_path.append(node_current)
                        paths[parent] = cp_path
                    else:
                        paths[parent].append(node_current)
                    ancestors_todo.append(parent)
            ancestors_todo.remove(node_current)
        return paths[dest_node]

    def get_properties_prof(self):
        ppt_item_profil_dict = defaultdict(set)
        for item in self.profile_items.keys():
            for ppt in self.movie_annotation_dict[item]:
                ppt_item_profil_dict[ppt].add(item)
        return ppt_item_profil_dict

    def get_properties_recommend(self, recommended_item):
        ppt_item_recommend = set()
        for ppt in self.movie_annotation_dict[recommended_item]:
            ppt_item_recommend = ppt_item_recommend.union(self.get_ancestors(ppt, set()))
        return ppt_item_recommend

    def extract_relevant_ppt(self):
        nodes_vu = set()
        ppt_2_item = defaultdict(set)
        for ppt in self.ppt_item_profil_dict.keys():
            broader_ppt = self.get_ancestors(ppt, set())
            for parent in broader_ppt:
                ppt_2_item[parent] = ppt_2_item[parent].union(set(self.ppt_item_profil_dict[ppt]))
                nodes_vu.add(parent)
        return nodes_vu, ppt_2_item

    def get_candidates_ppts(self, recommended_item):
        profile_ppt, ppt_2_item = self.extract_relevant_ppt()
        rec_ppt = self.get_properties_recommend(recommended_item)

        candidates = list()

        relevant_ppt = profile_ppt.intersection(rec_ppt)
        relevant_ppt = relevant_ppt.intersection(self.all_direct_annotations)

        for ppt in relevant_ppt:
            has_equally_good_child = False
            profile_items_associated = ppt_2_item[ppt]
            nb_item = len(ppt_2_item[ppt])
            for child in self.node_children_dict_valid[ppt]:
                if child in relevant_ppt and len(ppt_2_item[child]) >= nb_item:
                    has_equally_good_child = True
                    break

            if has_equally_good_child == False:
                candidates.append((ppt, nb_item, profile_items_associated))
        filtered_candidates = self.filter_redondant(candidates)
        return filtered_candidates

    def filter_redondant(self, candidates):
        filtered_candidates = list()
        all_candidate_ppts = set([candidate[0] for candidate in candidates])

        for candidate in candidates:
            candidate_ppt = candidate[0]
            children_candidate_ppt = self.post_order(candidate_ppt)[candidate_ppt]
            if not len(set(children_candidate_ppt).intersection(all_candidate_ppts)) > 1:
                filtered_candidates.append(candidate)
        return filtered_candidates

    def get_candidates_ppts2(self, recommended_item):
        profile_ppt, ppt_2_item = self.extract_relevant_ppt()
        rec_ppt = self.get_properties_recommend(recommended_item)
        candidates = list()
        relevant_ppt = profile_ppt.intersection(rec_ppt)
        node2NbItemsMaxInDesc = dict()
        node2NbItemsMaxInDirectRelevantDesc = dict()
        for (ppt_idx, ppt, ppt_isLeaf, ppt_isDirect) in self.nodes_parse_post_order:
            nbItemForThisNode = len(ppt_2_item[ppt])
            children_ppt = self.node_children_dict_valid[ppt]
            nbItemsMaxInDes = 0
            nbItemsMaxInDirectRelevantDes = 0
            for child in children_ppt:
                nbItemsMaxInDes = max(nbItemsMaxInDes, node2NbItemsMaxInDesc[child])
                nbItemsMaxInDirectRelevantDes = max(nbItemsMaxInDirectRelevantDes, node2NbItemsMaxInDirectRelevantDesc[child])
            node2NbItemsMaxInDesc[ppt] = max(nbItemForThisNode, nbItemsMaxInDes)
            if ppt_isDirect and ppt in relevant_ppt:
                if nbItemForThisNode > nbItemsMaxInDirectRelevantDes:
                    candidates.append((ppt, nbItemForThisNode, ppt_2_item[ppt]))
                node2NbItemsMaxInDirectRelevantDesc[ppt] = max(nbItemForThisNode, nbItemsMaxInDirectRelevantDes)
            else:
                node2NbItemsMaxInDirectRelevantDesc[ppt] = nbItemsMaxInDirectRelevantDes
        return candidates

    def scoring_fold_change(self, candidates):
        result = list()
        for candidate in candidates:
            ratio_db = self.annotation_counts_dict[candidate[0]] / self.total_nb_items
            ratio_profil = candidate[1] / len(self.profile_items.keys())
            score = ratio_profil / (ratio_db ** 2)
            if candidate[1] == 1:
                score = min(score, 1)
            if score >= 1:
                result.append((candidate[0], score, self.annotation_counts_dict[candidate[0]], candidate[1], candidate[2], self.get_entity_label(candidate[0])))

        result.sort(key=lambda x:x[1], reverse=True)
        return result[:self.nb_po]

    def scoring_ficher(self, candidates):
        result = list()
        for candidate in candidates:
            ratio_db = self.annotation_counts_dict[candidate[0]] / self.total_nb_items
            ratio_profil = candidate[1] / len(self.profile_items.keys())
            score = ratio_profil / ratio_db

            f_obs = [candidate[1], len(self.profile_items.keys()) - candidate[1]]
            f_exp = [self.annotation_counts_dict[candidate[0]], self.total_nb_items - self.annotation_counts_dict[candidate[0]]]
            if f_exp[1] < 0:
                p_score = 1
            else:
                p_score = 1 - stats.fisher_exact([f_obs, f_exp])[1]

            if candidate[1] == 1:
                score = min(score, 1)
            if score >= 1:
                result.append((candidate[0], score, p_score, self.annotation_counts_dict[candidate[0]], candidate[1], candidate[2], self.get_entity_label(candidate[0])))

        result.sort(key=lambda x:x[2], reverse=True)
        return result[:self.nb_po]

    def scoring(self, candidates):
        return self.scoring_fold_change(candidates)

    def explain(self):
        results_dict = dict()
        results_cem = dict()
        for rec_item in self.recommended_items:
            candidates = self.get_candidates_ppts2(rec_item)
            results_dict[rec_item] = self.scoring(candidates)

            # results_cem[rec_item] = self.cf_exp_generator(rec_item)
        return results_dict, results_cem

    def get_entity_label(self, entity):
        label = self.entity_label_dict[entity] if entity in self.entity_label_dict.keys() else self.entity_to_label(entity)
        label.strip('\n')
        return label

    def entity_to_label(self, entity):
        label = entity.replace('<http://dbpedia.org/resource/Category:', '')
        label = label.replace('>', '')
        label = label.replace('_', ' ')
        return label

    def cf_exp_generator(self, i_rec):
        d = dict()
        for i_prof, rating in self.profile_items.items():
            if not len([user for user in self.dict_item_liked_by_users[i_prof]]) == 0:
                percentage = len([user for user in self.dict_item_liked_by_users[i_prof] if i_rec in self.dict_user_liked_items[user]]) / len([user for user in self.dict_item_liked_by_users[i_prof]])
                if percentage > 0:
                    d[i_prof] = percentage
        d = {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}
        return d