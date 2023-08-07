from flask import jsonify, make_response
from appname.models import db
from elasticsearch import Elasticsearch, helpers
import os

# inject data to Elasticsearch with given search param json
def esInject(indexName, sqlQuery, indexIdColumn):
    esClient = Elasticsearch(os.getenv("ES_URL"))
    configuration = {
        "settings": {
            "index": {
                "number_of_replicas": 2,
            },
        }
    }
    
    data = fetchDataSource(indexName, sqlQuery, indexIdColumn)
    
    if esClient.indices.exists(index=indexName):
        print("The selected index already exists")
        helpers.bulk(esClient, data)
    else:
        print("Creating es index ...")
        esClient.indices.create(
            index=indexName,
            body=configuration
        )
        print("Created es index !")
        helpers.bulk(esClient, data)

# search data from Elasticsearch with given search param json
def esSearch(indexName, search_param):
    es = Elasticsearch()
    es.indices.put_settings(index=indexName,
                        body= {"index" : {
                                "max_result_window" : 200000000
                              }})
    
    response = es.search(index=indexName, body=search_param, request_timeout=30)
    try:
        result = [dict(hit["_source"]) for hit in response["hits"]["hits"]]
        return make_response(jsonify({"result": result, "totalCount": response["hits"]["total"]["value"]}), 200)
    except:
        return make_response(jsonify({"result": "No data available"}), 404)

# fetch data from postgresdb with given elasticsearch index name, sql sqlQuery and db table column name for id
def fetchDataSource(indexName, sqlQuery, indexIdColumn):
    print("Fetching data from postgres...")
    response = db.engine.execute(sqlQuery)

    for row in response:  
        doc = {
            "_index": indexName,
            "_id": row[indexIdColumn],
            "_source": dict(row),
        }
        yield doc
        
# delete given index of Elasticsearch
def esDelete(indexName):
    es = Elasticsearch()
    es.indices.delete(index=indexName)
    
# return count of docs for a given index of Elasticsearch
def esCount(indexName):
    es = Elasticsearch()
    return es.count(index=indexName)['count']
