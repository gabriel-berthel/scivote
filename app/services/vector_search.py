import spacy
from sentence_transformers import SentenceTransformer
import elasticsearch
import pytextrank
from models.arxiv_document import ArxivDocument
import os

idx = {
    "settings": {
        "index": {
            "number_of_replicas": 0,
            "refresh_interval": "30s",
            "translog.durability": "async"
        }
    },
    "mappings": {
        "dynamic": "false",
        "properties": {
            "arxiv_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "standard"
            },
            "abstract": {
                "type": "text",
                "analyzer": "standard"
            },
            "published": {
                "type": "date"
            },
            "keywords": {
                "type": "keyword"
            },
            "abstract_keywords": {
                "type": "keyword"
            },
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            },
            "categories": {
                "type": "keyword"
            }
        }
    }
}

class VectorSearch:
    def __init__(self, es_host="http://elasticsearch-container:9200", username="elastic"):
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe("textrank")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.es = elasticsearch.Elasticsearch(
            [es_host]
        )

        self.create_index_if_not_exists("webpages", idx)

    def create_index_if_not_exists(self, index_name, mapping):
        """
        Check if an Elasticsearch index exists. If not, create it with the provided mapping.
        """
        if not self.es.indices.exists(index=index_name):
            print(f"Index '{index_name}' does not exist. Creating it...")
            self.es.indices.create(index=index_name, body=mapping)
            print(f"Index '{index_name}' created successfully.")
        else:
            print(f"Index '{index_name}' already exists.")

    def extract_keywords(self, text):
        """Extract keywords using TextRank & via spaCy"""
        doc = self.nlp(text)
        keywords = [phrase.text for phrase in doc._.phrases]
        return keywords
    
    def prepare_document(self, doc: ArxivDocument):
        keywords = self.extract_keywords(doc.content)
        abstract_keywords = self.extract_keywords(doc.abstract)
        embedding = self.model.encode([doc.content])[0]
        
        return {
            "published": doc.published,
            "title": doc.title,
            "keywords": keywords,
            "abstract": doc.abstract,
            "abstract_keywords": abstract_keywords,
            "embedding": embedding.tolist(),
            "categories": doc.categories
        }

    def insert_document(self, doc: ArxivDocument):
        """Insert a document into Elasticsearch."""
        doc_data = self.prepare_document(doc)
        self.es.index(index="webpages", id=doc.arxiv_id, document=doc_data)

    def search_documents(self, query, category_filter: str, max_results=250):
        query_keywords = self.extract_keywords(query)
        query_embedding = self.model.encode([query])[0].tolist()

        must_clauses = []
        if category_filter:
            if "*" in category_filter:
                must_clauses.append({
                    "wildcard": {"categories": category_filter}
                })
        
        resp = self.es.search(
            index="webpages",
            size=max_results,
            query={
                "bool": {
                    "should": [
                        {
                            "match": {
                                "title": {"query": query, "boost": 2.0}
                            }
                        },
                        {
                            "match": {
                                "abstract": {"query": query, "boost": 1.5}
                            }
                        },
                        *[
                            {"term": {"abstract_keywords": {"value": kw, "boost": 2.0}}}
                            for kw in query_keywords
                        ],
                        *[
                            {"term": {"keywords": {"value": kw, "boost": 1.0}}}
                            for kw in query_keywords
                        ]
                    ],
                    "minimum_should_match": 1,
                    "must": must_clauses
                }
            },
            knn={
                "field": "embedding",
                "query_vector": query_embedding,
                "k": max_results,
                "num_candidates": max_results * 3,
                "filter": [
                    *must_clauses
                ]
            }
        )

        return [{'id': hit['_id'], 'score': hit['_score']} for hit in resp['hits']['hits']]

def get_vector_search_service() -> VectorSearch:
    return VectorSearch()
