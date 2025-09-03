import logging

from collections import defaultdict

from lambdatune.config_selection.query_to_index import QueryToIndex


class QueryCluster:
    """
    A class that represents a cluster of queries that share the same set of indexes.
    """
    def __init__(self, cluster_id, queries, indexes):
        """
        Creates a new QueryCluster
        """
        self.__cluster_id = cluster_id
        self.__queries = queries
        self.__indexes = indexes

    def get_queries(self):
        """
        Returns the queries in the cluster
        """
        return self.__queries

    def get_indexes(self):
        """
        Returns the indexes in the cluster
        """
        return self.__indexes

    def get_cluster_id(self):
        """
        Returns the cluster id
        """
        return self.__cluster_id

def create_index_dict(index_dependencies: QueryToIndex):
    """
    Creates a dictionary that maps each index to a unique id
    """
    index_dict = dict()
    idx = 0
    for query in index_dependencies.query_to_index:
        for index in index_dependencies.get_query_indexes(query):
            if index not in index_dict:
                index_dict[index] = idx
                idx += 1

    return index_dict


def create_query_vectors(queries, index_dependencies: QueryToIndex):
    """
    Creates the query vectors
    """
    # Create index dictionary
    index_dict = create_index_dict(index_dependencies)

    # Create query vector
    query_vectors = list()
    for query in queries:
        vector = [0] * len(index_dict)
        for index in index_dependencies.get_query_indexes(query):
            vector[index_dict[index]] = 1
        query_vectors.append(vector)

    return query_vectors


def generate_query_clusters(queries, index_dependencies: QueryToIndex, max_clusters: int=13):
    """
    Generates the query clusters from the queries and the index dependencies
    """
    query_groups = defaultdict(list)

    # First group the queries by the set of indexes they use
    for query in queries:
        indexes = index_dependencies.get_query_indexes(query)
        query_groups[frozenset(indexes)].append(query)

    # Create the query clusters
    query_clusters = list()
    cluster_id = 0
    for group in query_groups:
        query_clusters.append(QueryCluster(cluster_id=cluster_id, queries=query_groups[group], indexes=group))
        cluster_id += 1

    # Reduce the number of clusters if necessary using K-means clustering
    if len(query_clusters) > max_clusters:
        new_query_clusters = list()

        # Create query vectors according to the index dependencies
        query_vectors = create_query_vectors(queries, index_dependencies)

        # K-means clustering
        from sklearn.cluster import KMeans
        import numpy as np
        kmeans = KMeans(n_clusters=max_clusters, random_state=0).fit(np.array(query_vectors))

        # Print clusters
        logging.debug("Clusters:")
        num_queries = 0
        for cluster_id in range(0, max_clusters):
            cluster_vectors = list()
            cluster_queries = list()
            cluster_indexes = set()

            for j in range(0, len(kmeans.labels_)):
                if kmeans.labels_[j] == cluster_id:
                    cluster_vectors.append(query_vectors[j])
                    cluster_queries.append(queries[j])
                    cluster_indexes = cluster_indexes.union(index_dependencies.get_query_indexes(queries[j]))
                    num_queries += 1

            new_query_clusters.append(QueryCluster(
                cluster_id=cluster_id,
                queries=cluster_queries,
                indexes=cluster_indexes))

            logging.debug(f"Cluster {cluster_id} (size: {len(cluster_vectors)}):")
            for vector in cluster_vectors:
                logging.debug(vector)

        query_clusters = new_query_clusters

    return query_clusters
