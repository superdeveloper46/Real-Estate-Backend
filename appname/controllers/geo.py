from flask import Blueprint, make_response, jsonify
from sqlalchemy import text

from appname.models import db


geo = Blueprint('geo', __name__)

# search and return property - overview data by property id
@geo.route("/api/geo/<string:fips>", methods=["GET"])
def getOverviewData(fips):
    query = text(f"""
    SELECT count(distinct propertyid)
    from assessor
    where fips = {fips}::varchar
    """)
    print(query)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'status': 200}), 200)