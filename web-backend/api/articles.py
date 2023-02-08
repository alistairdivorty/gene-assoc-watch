import os
from datetime import datetime, timedelta
from flask import request
from pymongo import MongoClient
from pymongo.database import Database
from bson.json_util import dumps
from . import api

db: Database = MongoClient(os.environ["MONGODB_CONNECTION_URI"]).get_default_database()


@api.route("/articles", methods=["POST"])
def index():
    params = request.get_json() or {}

    pipeline = []

    searchStage = {"compound": {}}

    searchStage["compound"]["filter"] = []

    searchStage["compound"]["filter"].append(
        {
            "range": {
                "path": "firstPublicationDate",
                "gte": datetime.now()
                - timedelta(days=params.get("daysSincePublication", 7)),
                "lte": datetime.now(),
            }
        }
    )

    searchStage["compound"]["must"] = []

    if "fullText" not in params:
        searchStage["compound"]["must"].append(
            {
                "near": {
                    "path": "firstPublicationDate",
                    "origin": datetime.now(),
                    "pivot": 2592000000,
                }
            }
        )

    if "fullText" in params:
        searchStage["compound"]["must"].append(
            {
                "text": {
                    "query": params["fullText"],
                    "path": ["title", "abstract"],
                    "fuzzy": {"maxEdits": 1},
                }
            }
        )

    searchStage["count"] = {"type": "total"}

    pipeline.append({"$search": searchStage})

    pipeline.append(
        {
            "$project": {
                "abstract": 1,
                "authors": 1,
                "firstPublicationDate": 1,
                "gda": 1,
                "journal": 1,
                "pmid": 1,
                "title": 1,
                "meta": "$$SEARCH_META",
            }
        }
    )

    if "page" and "pageSize" in params:
        pipeline.append({"$skip": params["pageSize"] * (params["page"] - 1)})
        pipeline.append({"$limit": params["pageSize"]})

    cursor = db.pubmedArticles.aggregate(pipeline)

    return dumps(list(cursor))
