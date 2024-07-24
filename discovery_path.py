'''This .py is used to find direct path and indirect path'''

import networkx as nx
from typing import Set, List
from sklearn.linear_model import LinearRegression
import numpy as np
# from datasets.synthetic_Friedman import dataset_synthetic_regression as dataset
import pandas as pd
import lingam
from random import uniform

def find_direct_paths(g, ori, des):
    '''
    Find direct path(direct path)
    :param g: directed acyclic graph
    :param ori: node
    :param des: outcome
    :return: direct path
    '''
    path_list = []
    for path in g.out_edges(ori):
        if path[1] == des:
            path_list.append(path)

    return path_list

def find_indirect_paths(g, ori, des):
    '''
    Find indirect path(indirect path)
    :param g: directed acyclic graph
    :param ori: original node
    :param des: outcome/destination
    :return: indirect path
    '''

    def find(src, path):
        path_list = path + (src, )

        # make sure DAG(acyclic)
        assert src not in path, 'Graph produced must be a DAG(Direct Acyclic Graph): {}'.format(path_list)

        # if gets to destination
        if src == des:
            yield path_list

        # Nested search
        for node, node_child in g.out_edges(src):
            yield from find(node_child, path_list)

    path_list = list(find(ori, ()))
    return [path for path in path_list if len(path) > 2]

def find_all_paths(g, ori, des):
    '''
    Find all paths(backdoor path, direct path, indirect path)
    :param g: DAG
    :param ori: original node
    :param des: outcome/destination
    :return: all of paths
    '''
    def find(src, path):
        path_list = path + (src,)

        # if gets to destination
        if src == des:
            yield path_list

        elif src not in path:
            for node, node_child in g.out_edges(src):
                yield from find(node_child, path_list)

            for node_child, node in g.in_edges(src):
                yield from find(node_child, path_list)

    return list(find(ori, ()))

def find_backdoor_paths(all_paths: Set, direct_paths: Set, indirect_paths: Set, g, ori):
    '''
    Find backdoor paths
    :param all_paths: all paths
    :param direct_paths: direct paths
    :param indirect_paths: indirect paths
    :return:
    '''
    out = all_paths.difference(direct_paths).difference(indirect_paths)
    out_list = []
    a = [nodes[1] for nodes in list(g.out_edges(ori))]
    for path in out:
        if path[1] not in a:
            out_list.append(path)

    return out_list

def find_chain_X_on_Y(g, ori, des):
    '''
    Find chain structure of X on Y
    :param g:
    :param ori:
    :param des:
    :return:
    '''
    path_list = []
    for path in g.in_edges(ori):
        if des not in path:
            path_list.append(path)
    node_list = []

    for i, j in path_list:
        node_list.append(i)

    chain_paths = []
    for node in node_list:
        indirect_paths = find_indirect_paths(g, node, des)
        for path in indirect_paths:
            if len(path) == 3 and path[1] == ori:
                chain_paths.append(path)

    return chain_paths

def find_fork_X_on_Y(g, ori, des):
    '''
    Find for structure of X on Y
    :param g:
    :param ori:
    :param des:
    :return:
    '''
    path_list = []
    for path in g.out_edges(ori):
        if des not in path:
            path_list.append(path)
    node_list = []

    for i, j in path_list:
        node_list.append(j)

    fork_paths = []
    for node in node_list:
        all_paths = find_all_paths(g, node, des)
        direct_paths = find_direct_paths(g, node, des)
        indirect_paths = find_indirect_paths(g, node, des)
        back_paths = find_backdoor_paths(set(all_paths), set(direct_paths), set(indirect_paths), g, ori)
        for path in back_paths:
            if len(path) == 3 and path[1] == ori:
                fork_paths.append(path)

    return fork_paths

def if_chain(g, front, mid, back):
    '''
    If chain structure
    :param g:
    :param front:
    :param mid:
    :param back:
    :return:
    '''
    return (front, mid) in set(g.out_edges(front)) and (mid, back) in set(g.out_edges(mid))

def if_fork(g, pa, ch1, ch2):
    '''
    If fork structure
    :param g: DAG
    :param pa: parent
    :param ch1: child1
    :param ch2: child2
    :return:
    '''
    return (pa, ch1) and (pa, ch2) in set(g.out_edges(pa))

def if_collider(g, pa1, pa2, child):
    '''
    If collider structure
    :param g: DAG
    :param pa1: parents1
    :param pa2: parents2
    :param child: child
    :return:
    '''
    return (pa1, child) and (pa2, child) in set(g.in_edges(child))

def d_separate(g, ori, des, mixed_set):
    '''

    :param g: DAG
    :param ori: original node
    :param des: outcome/destination
    :param mixed_set: set which is used to block info
    :return: connected_paths, blocked_paths
    '''
    connected_paths = []
    blocked_paths = []
    for path in find_all_paths(g, ori, des):
        if_connected = True
        for i in range(1, len(path)-1):
            if if_collider(g, path[i-1], path[i], path[i+1]):
                if path[i] not in mixed_set:
                    if_connected = False
                    break
            else:
                if path[i] in mixed_set:
                    if_connected = False
                    break
        if if_connected == True:
            connected_paths.append(path)
        else:
            blocked_paths.append(path)

    return connected_paths, blocked_paths

def backdoor_separate(g, ori, des, mixed_set):
    '''

    :param g: DAG
    :param ori: original node
    :param des: outcome/destination
    :param mixed_set: set which is used to block info
    :return: connected_paths, blocked_paths
    '''
    connected_paths = []
    blocked_paths = []
    all_paths = set(find_all_paths(g, ori, des))
    direct_paths = set(find_direct_paths(g, ori, des))
    indirect_paths = set(find_indirect_paths(g, ori, des))
    for path in find_backdoor_paths(all_paths, direct_paths, indirect_paths, g, ori):
        if_connected = True
        for i in range(1, len(path)-1):
            if if_collider(g, path[i-1], path[i], path[i+1]):
                if path[i] not in mixed_set:
                    if_connected = False
                    break
            else:
                if path[i] in mixed_set:
                    if_connected = False
                    break
        if if_connected == True:
            connected_paths.append(path)
        else:
            blocked_paths.append(path)

    return connected_paths, blocked_paths

def indirect_separate(g, ori, des, mixed_set):
    '''

    :param g: DAG
    :param ori: original node
    :param des: outcome/destination
    :param mixed_set: set which is used to block info
    :return: connected_paths, blocked_paths
    '''
    connected_paths = []
    blocked_paths = []
    for path in find_indirect_paths(g, ori, des):
        if_connected = True
        for i in range(1, len(path)-1):
            if if_collider(g, path[i-1], path[i], path[i+1]):
                if path[i] not in mixed_set:
                    if_connected = False
                    break
            else:
                if path[i] in mixed_set:
                    if_connected = False
                    break
        if if_connected == True:
            connected_paths.append(path)
        else:
            blocked_paths.append(path)

    return connected_paths, blocked_paths

def identify_direct_effect(g, ori, des, df, obs):
    '''
    Identify direct effect of X on Y
    :param g: Graph
    :param ori: original node
    :param des: outcome/destination
    :param mixed_set: mixed set
    :return:
    '''
    BB = []
    all_paths = set(find_all_paths(g, ori, des))
    direct_paths = set(find_direct_paths(g, ori, des))
    indirect_paths = set(find_indirect_paths(g, ori, des))

    for path in find_backdoor_paths(all_paths, direct_paths, indirect_paths, g, ori):
        BB.append(path[1])
    for node in g.in_edges(ori):
        BB.append(node[0])
    BB = list(set(BB))

    value = do_value(g, ori, BB, obs)

    coeff_list = path_coefficients_all(g, df)

    for path_coeff in coeff_list:
        if path_coeff[1]==ori and path_coeff[0] in BB:
            value[ori] += path_coeff[-1]*value[path_coeff[0]]

    others_direct_coeff = []

    ori_direct_coeff = 0

    for coeff in coeff_list:
        if des in coeff and ori in coeff:
            ori_direct_coeff = coeff[-1]

    ori_direct_effect = value[ori] * ori_direct_coeff

    ori_direct_effect_before = ori_direct_effect
    print("Direct effect before: ", ori_direct_effect_before)
    # for node in g.nodes:
    #     if node != ori and node != des:
    #         indirect_paths_to_des.append(find_indirect_paths(g, node, des))
    # for ips in indirect_paths_to_des:
    #     if len(ips) > 0:
    #         for ip in ips:
    #             if ori == ip[-2]:
    #                 indirect_paths_through_ori.append(ip)
    # print(indirect_paths_through_ori)
    # for ip in indirect_paths_through_ori:
    #     path_coeff = []
    #     for i in range(1, len(ip)):
    #         for coeff in coeff_list:
    #             if ip[i-1] in coeff and ip[i] in coeff:
    #                 path_coeff.append(coeff[-1])
    #     path_coeffs.append(path_coeff)

    for bb in BB:
        for coeff in coeff_list:
            if bb in coeff and ori in coeff:
                others_direct_coeff.append(coeff)

    others_direct_coeff = list([{coeff[0]: coeff[2]} for coeff in others_direct_coeff])

    for b, coef in zip(BB, others_direct_coeff):
        ori_direct_effect -= coef.get(b) * ori_direct_coeff * value[b]
    ori_direct_effect_after = ori_direct_effect

    return len(BB), ori_direct_effect_after

def identify_indirect_effect(g, ori, des, df, obs):
    '''
    Identify indirect effect(block direct effect)
    :param g:
    :param ori:
    :param des:
    :param df:
    :param obs:
    :return:
    '''
    BB = [ori]
    value = do_value(g, ori, BB, obs)
    indirect_paths = set(find_indirect_paths(g, ori, des))
    coeff_list = path_coefficients_all(g, df)
    coeff_dict = {}
    for coeff in coeff_list:
        coeff_dict[str(coeff[0])+'_'+str(coeff[1])] = coeff[-1]
    coeffs = {}
    for path in indirect_paths:
        for i in range(1, len(path)):
            if str(path[i-1])+'_'+str(path[i]) in coeff_dict.keys():
                coeffs[str(path[i-1])+'_'+str(path[i])] = coeff_dict.get(str(path[i-1])+'_'+str(path[i]))
    ori_indirect_effect_all = 0
    ori_indirect_effect_list = []

    for path in indirect_paths:
        ori_indirect_effect_each = value[ori]
        for i in range(1, len(path)):
            ori_indirect_effect_each = ori_indirect_effect_each * coeffs.get(str(path[i-1])+'_'+str(path[i]))
        ori_indirect_effect_list.append(ori_indirect_effect_each)
        ori_indirect_effect_all += ori_indirect_effect_each

    # return BB, [{k: v} for k, v in zip(indirect_paths, ori_indirect_effect_list)]
    return len(BB), ori_indirect_effect_all

def path_coefficients_des(df, des, columns):
    '''
    path coefficients on destination
    :param df: data
    :param dest: destination node
    :param model_columns: 除去dest以外的所有节点
    :return:
    '''
    xs = df[columns]
    ys = df[des]

    model = LinearRegression().fit(xs, ys)
    return dict(zip(columns, [np.round(coeff, 5) for coeff in model.coef_]))

def path_coefficients_lingam(df):
    '''

    :param df:
    :param des:
    :param columns:
    :return:
    '''
    X = df

    model = lingam.DirectLiNGAM()
    model.fit(X)

    return model.adjacency_matrix_

def path_coefficients_all(g, df):
    '''
    overall path coefficients
    :param g: graph
    :param df: df
    :return:
    '''
    coeff_list = []
    for node in sorted(g.nodes):

        parents = [other for other, _ in g.in_edges(node)]

        if len(parents) > 0:
            coeffs = path_coefficients_des(df, node, parents)

            for parent in sorted(parents):

                coeff_list.append([parent, node, coeffs[parent]])

    return coeff_list

def do_value(g, ori, BB: List, obs):
    value = {}
    for node in g.nodes:
        value[node] = 0
    for bb in BB:
        a_ = uniform(1, 3)
        value[bb] = a_

    return value

def create_data(num_samples, dataset, g):

    data = [dataset.observation(g) for _ in range(num_samples)]
    df = pd.DataFrame(data, columns=sorted(g.nodes))

    return df

def calculate_S(bb_direct, bb_indirect, n, direct_effect, indirect_effect):
    '''
    S_i = BB_direct/(n-1) * direct_effect + BB_indirect/(n-1) * indirect_effect
    :param bb_direct:
    :param bb_indirect:
    :param n:
    :param direct_effect:
    :param indirect_effect:
    :return:
    '''
    return bb_direct/(n-1) * direct_effect + bb_indirect/(n-1) * indirect_effect

if __name__ == '__main__':

    np.random.seed(41)

    # create a DAG
    g = nx.DiGraph()

    # add edges
    g.add_edges_from([
        ("X4", "X2"),
        ("X4", "X5"),
        ("X4", "X3"),
        ("X4", "X1"),
        ("X3", "X2"),
        ("X3", "X5"),
        ("X3", "X1"),
        ("X2", "X1"),
        ("X2", 'X5'),
        ("X5", "X1"),
        ("X1", "Y"),
    ])

    nx.draw_shell(g)
    # df1 = create_data(100000, dataset, g)

    # identify_direct_effect(g, 'X1', 'Y', df1, dataset.observation(g))


    # for node in sorted(list(g.nodes))[:-1]:
    #     direct_effect = identify_direct_effect(g, node, sorted(list(g.nodes))[-1], df1, dataset.observation(g))[-1]
    #     indirect_effect = identify_indirect_effect(g, node, sorted(list(g.nodes))[-1], df1, dataset.observation(g))[0]
    #
    #     print('Total effect of {} on Y is {}'.format(node, direct_effect+indirect_effect))
    #     print('direct effect of {} on Y is {}'.format(node, direct_effect))
    #     print('indirect effect of {} on Y is {}'.format(node, indirect_effect))
    #     print('*'*50)
    # identify_indirect_effect(g, 'X2', 'Y', df1, dataset.observation(g))
