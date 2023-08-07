from flask import Blueprint, request, json, make_response
from sqlalchemy import text

from appname.controllers.elasticsearch.base import esSearch, esInject, esCount

from geopy.geocoders import Nominatim

import googlemaps

listbuilder = Blueprint('listbuilder', __name__)

indexName = "sfra_propertylist"

# search AND return property list data with given params from an index of Elasticsearch
@listbuilder.route("/api/elasticsearch/search/propertylistdata", methods=["POST"])
def getPropertyListDataFromElasticsearch():
    params = request.get_json()
    # draft search params
    searchParam = params

    return esSearch(indexName, searchParam)

@listbuilder.route("/api/elasticsearch/search/getparsedlocation", methods=["POST"])
def searchProperty():
    params = request.get_json()
    searchText = params['searchText']
    
    
    gmaps = googlemaps.Client(key='AIzaSyDI2ZGHB239jBH4dvTdhemt0YupHnfyLOQ')
    autocomplete_predictions = gmaps.places_autocomplete(searchText, components={'country': 'us'})

    response_data= []

    for data in autocomplete_predictions:
        geocodes = gmaps.geocode(data['description'])
        for geocode in geocodes:
            response_data.append(geocode)
    
    result = json.dumps([value for value in response_data])
    return make_response(result, 200)

    # geolocator = Nominatim(user_agent="SFRA_App")
    # location = geolocator.geocode(searchText, exactly_one=False, limit=100, addressdetails=True, country_codes=['US'])

    # if location is None:
    #     return make_response(json.dumps([]), 200)
    # else:
    #     result = json.dumps([
    #         {'label': data.raw['display_name'][0:len(data.raw['display_name'])-15], 
    #          'road':data.raw['address']['road'] if 'road' in data.raw['address'] else '',
    #          'city':data.raw['address']['city'] if 'city' in data.raw['address'] else '',
    #          'county':data.raw['address']['county'] if 'county' in data.raw['address'] else '',
    #          'msa':data.raw['address']['state'] if 'state' in data.raw['address'] else '',
    #          'zipCode':data.raw['address']['postcode'] if 'postcode' in data.raw['address'] else ''
    #          } for data in location])
    #     return make_response(result, 200)


    # return make_response(jsonify(
    #     result='success'
    # ), 200)

    
# create an index AND inject data with sql query to Elasticsearch
@listbuilder.route("/api/elasticsearch/inject/propertylistdata", methods=["GET", "POST"])
def injectPropertyListDataToElasticsearch():
    indexIdColumn = "propertyid"
    limit = 2000000
    startIndex = 62
    loop = 80
    
    try:
        for x in range(startIndex, loop):
            startNum = x * limit
            endNum = (x + 1) * limit
            print(f"Indexing Listbuilder data from {startNum} to {endNum} ...")
            
            sqlQuery = text(f"""
            SELECT DISTINCT a.propertyid, a.situsfullstreetaddress, a.situszip5, a.situscity, a.situslatitude, a.situslongitude, f.county, f.msa, a.schooldistrictname, pc.description AS property_classification, lu.description AS property_type, a.bedrooms, a.bathtotalcalc, a.sumbuildingsqft, a.lotsizesqft, a.yearbuilt, s.description AS num_stories, a.hoa1name, p.description AS pool, a.atticsqft, g.description AS garage, b.description AS basement, a.situsunitnbr, date(a.currentsalecontractdate::text) AS sales_date, date_part('year', now()) - date_part('year', date(a.currentsalecontractdate::text)) years_owned, a.owner1corpind, a.owner1ownershiprights, CASE WHEN coalesce(v.description, a.owner1corpind) IS NOT NULL THEN coalesce(v.description, a.owner1corpind) WHEN a.owner1corpind IS NULL THEN 'Individual' WHEN a.owner1corpind IS NOT NULL THEN 'Corporate' END AS owner_type, a.ownername1full, a.currentsalesprice, a.owneroccupied, a.vacantflag, onm.sfr_cnt, onm.count, HomesteadInd, VeteranInd, DisabledInd,WidowInd, SeniorInd, SchoolCollegeInd, ReligiousInd, WelfareInd, PublicUtilityInd, CemeteryInd, HospitalInd, LibraryInd, CASE WHEN owneroccupied IS NULL AND a.mailingstate != a.situsstate THEN 'Out of State' WHEN owneroccupied IS NULL AND a.mailingcity != a.situscity THEN 'Out of City' ELSE '' END AS absentee_owner_location, CASE WHEN vacantflag = 'B' AND vacantflagdate > currentsalecontractdate THEN 1 ELSE 0 END AS bank_owned, vacantflagdate, a.totalopenlienamt, a.currentavmvalue, a.currentavmvalue - a.totalopenlienamt AS equity, a.assdtotalvalue, a.pfcflag, a.pfcindicator,pf.description AS pfc_status, date(a.pfcrecordingdate::text) AS pfcrecordingdate, a.pfcreleasereason, date(a.islistedflagdate::text) AS listedflagdate, islistedflag, a.islistedpricerange, l.description AS loan_type, a.totalopenliennbr, a.totalopenlienamt, l.code AS mtg1type, l2.code AS mtg2type, l3.code AS mtg3type, l4.code AS mtg4type, a.mtg1typefinancing, a.mtg2typefinancing, a.mtg3typefinancing, a.mtg4typefinancing, d.firstmtginterestrate::float/100 AS mtg1_ir, d2.firstmtginterestrate::float/100 AS mtg2_ir, d3.firstmtginterestrate::float/100 AS mtg3_ir, d4.firstmtginterestrate::float/100 AS mtg4_ir, CASE WHEN d5.firstmtgamt = 0 THEN 1 ELSE 0 END AS cash_buyer , CASE WHEN a.totalopenlienamt IS NULL THEN 1 ELSE 0 END AS owned_free_clear, d5.firstmtgsellercarrybackflag
            FROM (SELECT * FROM assessor LIMIT 2000000 OFFSET {startNum}) AS a
            LEFT JOIN fips_correct f ON f.fips_code = a.fips
            LEFT JOIN fa_prop_cl_ind pc ON pc.code = a.propertyclassid
            LEFT JOIN fa_lu_code lu ON lu.code = a.landusecode
            LEFT JOIN fa_stories s ON s.code = a.storiesnbrcode
            LEFT JOIN fa_pool p ON p.code::int = a.poolcode
            LEFT JOIN fa_garage g ON g.code::int = a.garage
            LEFT JOIN fa_basement b ON b.code::int = a.basementcode
            LEFT JOIN fa_owner_vest v ON v.code = a.owner1ownershiprights
            LEFT JOIN owner_names_mailing_address onm ON onm.mailingfullstreetaddress = a.mailingfullstreetaddress AND onm.mailingzip5 = a.mailingzip5
            LEFT JOIN fa_loan_type l ON l.code = a.mtg1loantype
            LEFT JOIN fa_loan_type l2 ON l2.code = a.mtg2loantype
            LEFT JOIN fa_loan_type l3 ON l3.code = a.mtg3loantype
            LEFT JOIN fa_loan_type l4 ON l4.code = a.mtg4loantype
            LEFT JOIN deed d ON d.fatransactionid = a.mtg1transactionid
            LEFT JOIN deed d2 ON d2.fatransactionid = a.mtg2transactionid
            LEFT JOIN deed d3 ON d3.fatransactionid = a.mtg3transactionid
            LEFT JOIN deed d4 ON d4.fatransactionid = a.mtg4transactionid
            LEFT JOIN deed d5 ON d5.fatransactionid = a.currentsaletransactionid
            LEFT JOIN fa_preforeclosure pf ON pf.code::int = a.pfcindicator
            """)
            esInject(indexName, sqlQuery, indexIdColumn)
        print("Great, indexing has been finished successfully!")
    except:
        print("Unexpected error has been occurred while indexing")
