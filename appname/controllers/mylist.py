from flask import Blueprint, g, make_response, jsonify, request, json

from appname.models import db
from appname.models.listName import ListName
from appname.models.filters import Filters
from appname.models.myLists import MyLists
from elasticsearch import Elasticsearch

from datetime import date

mylist = Blueprint('mylist', __name__)

@mylist.route("/api/mylist/makelist", methods=["POST"])
def makeList():
    params = request.get_json()

    listName = params['listName']
    dmi = params['dmi']
    totalCount = params['totalCount']
    newCount = params['newCount']
    createAt = date.today()
    updateAt = date.today()
    uid = g.uid
    
    filters = params['filters']
    
    listId = ListName.create(listName, dmi, totalCount, newCount, len(filters), createAt, updateAt, uid)
    
    for obj in filters:
        db.session.add(Filters(listId, obj['dataId'], obj['key'], obj['value']))
        db.session.commit()
        
    searchParam = params['options']
    if(len(searchParam) != 0):
        es = Elasticsearch()
        es.indices.put_settings(index='sfra_propertylist',
                            body= {"index" : {
                                    "max_result_window" : 200000000
                                }})
        
        response = es.search(index='sfra_propertylist', body=searchParam, request_timeout=30)
        result = [dict(hit["_source"]) for hit in response["hits"]["hits"]]
        
        for obj in result:
            db.session.add(MyLists(obj['absentee_owner_location'], obj['assdtotalvalue'], obj['atticsqft'], obj['bank_owned'], obj['basement'], obj['bathtotalcalc'], obj['bedrooms'], obj['cash_buyer'], obj['cemeteryind'], obj['count'], obj['county'], obj['currentavmvalue'], obj['currentsalesprice'], obj['disabledind'], obj['equity'], obj['firstmtgsellercarrybackflag'], obj['garage'], obj['hoa1name'], obj['homesteadind'], obj['hospitalind'], obj['islistedflag'], obj['islistedpricerange'], obj['libraryind'], obj['listedflagdate'], obj['loan_type'], obj['lotsizesqft'], obj['msa'], obj['mtg1_ir'], obj['mtg1type'], obj['mtg1typefinancing'], obj['mtg2_ir'], obj['mtg2type'], obj['mtg2typefinancing'], obj['mtg3_ir'], obj['mtg3type'], obj['mtg3typefinancing'], obj['mtg4_ir'], obj['mtg4type'], obj['mtg4typefinancing'], obj['num_stories'], obj['owned_free_clear'], obj['owner1corpind'], obj['owner1ownershiprights'], obj['owner_type'], obj['ownername1full'], obj['owneroccupied'], obj['pfc_status'], obj['pfcflag'], obj['pfcindicator'], obj['pfcrecordingdate'], obj['pfcreleasereason'], obj['pool'], obj['property_classification'], obj['property_type'], obj['propertyid'], obj['publicutilityind'], obj['religiousind'], obj['sales_date'], obj['schoolcollegeind'], obj['schooldistrictname'], obj['seniorind'], obj['sfr_cnt'], obj['situscity'], obj['situsfullstreetaddress'], obj['situslatitude'], obj['situslongitude'], obj['situsunitnbr'], obj['situszip5'], obj['sumbuildingsqft'], obj['totalopenlienamt'], obj['totalopenliennbr'], obj['vacantflag'], obj['vacantflagdate'], obj['veteranind'], obj['welfareind'], obj['widowind'], obj['yearbuilt'], obj['years_owned'], listId))
            db.session.commit()

    return make_response(jsonify(
        result='success'
    ), 200)
    
@mylist.route("/api/mylist/editlist", methods=["POST"])
def editList():
    params = request.get_json()

    id = params['id']
    listName = params['listName']
    dmi = params['dmi']
    updateAt = date.today()
    
    list = ListName.query.filter_by(id=id).first();
    list.listName = listName;
    list.dmi = dmi;
    list.updateAt = updateAt;
    
    db.session.commit();

    return make_response(list.as_dict(), 200)
    
@mylist.route("/api/mylist/getlists", methods=["POST"])
def getLists():
    uid = g.uid
    params = request.get_json()
    searchKey = params['searchKey']
    sort = params['sort']
    page = params['from']
    size = params['size']
    
    search = "%{}%".format(searchKey)
    
    if(sort == 0):
        sorting = ListName.createAt.desc()
    elif(sort == 1):
        sorting = ListName.filterCount.desc()
    elif(sort == 2):
        sorting = ListName.filterCount.asc()
    elif(sort == 3):
        sorting = ListName.newCount.desc()
    elif(sort == 4):
        sorting = ListName.newCount.asc()
        
    listNames = ListName.query.filter_by(uid=uid).filter(ListName.listName.like(search)).order_by(sorting).paginate(page=page, per_page=size)
    
    result = json.dumps([data.as_dict() for data in listNames.items])
    return make_response(result, 200)

@mylist.route("/api/mylist/getlisttotalcount", methods=["POST"])
def getListTotalCount():
    uid = g.uid
    params = request.get_json()
    searchKey = params['searchKey']
    
    search = "%{}%".format(searchKey)
    count = ListName.query.filter_by(uid=uid).filter(ListName.listName.like(search)).count()
    return make_response(jsonify(
        result=count
    ), 200)

@mylist.route("/api/mylist/deletelist", methods=["POST"])
def deleteList():
    params = request.get_json()
    id = params['id']
    
    datas = Filters.query.filter_by(listId=id)
    for d in datas:
        db.session.delete(d)
        db.session.commit();
        
    datas = MyLists.query.filter_by(listId=id)
    for d in datas:
        db.session.delete(d)
        db.session.commit();
    
    data = ListName.query.get(id)
    db.session.delete(data)
    db.session.commit();
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@mylist.route("/api/mylist/getfilters", methods=["POST"])
def getFiltersByListId():
    params = request.get_json()
    id = params['id']
    
    filters = Filters.query.filter_by(listId=id);
    result = json.dumps([data.as_dict() for data in filters])
    return make_response(result, 200)

@mylist.route("/api/mylist/getMyListsByName", methods=["POST"])
def getMyListsByName():
    params = request.get_json()
    listId = params['listId']
    
    filters = MyLists.query.filter_by(listId=listId);
    result = json.dumps([data.as_dict() for data in filters])
    return make_response(result, 200)
    
@mylist.route("/api/mylist/addToList", methods=["POST"])
def addToList():
    params = request.get_json()
    listId = params['listId']
    searchParam = params['options']
    print(searchParam)
    es = Elasticsearch()
    es.indices.put_settings(index='sfra_propertylist',
                        body= {"index" : {
                                "max_result_window" : 200000000
                            }})
    
    response = es.search(index='sfra_propertylist', body=searchParam, request_timeout=30)
    result = [dict(hit["_source"]) for hit in response["hits"]["hits"]]
    
    for obj in result:
        db.session.add(MyLists(obj['absentee_owner_location'], obj['assdtotalvalue'], obj['atticsqft'], obj['bank_owned'], obj['basement'], obj['bathtotalcalc'], obj['bedrooms'], obj['cash_buyer'], obj['cemeteryind'], obj['count'], obj['county'], obj['currentavmvalue'], obj['currentsalesprice'], obj['disabledind'], obj['equity'], obj['firstmtgsellercarrybackflag'], obj['garage'], obj['hoa1name'], obj['homesteadind'], obj['hospitalind'], obj['islistedflag'], obj['islistedpricerange'], obj['libraryind'], obj['listedflagdate'], obj['loan_type'], obj['lotsizesqft'], obj['msa'], obj['mtg1_ir'], obj['mtg1type'], obj['mtg1typefinancing'], obj['mtg2_ir'], obj['mtg2type'], obj['mtg2typefinancing'], obj['mtg3_ir'], obj['mtg3type'], obj['mtg3typefinancing'], obj['mtg4_ir'], obj['mtg4type'], obj['mtg4typefinancing'], obj['num_stories'], obj['owned_free_clear'], obj['owner1corpind'], obj['owner1ownershiprights'], obj['owner_type'], obj['ownername1full'], obj['owneroccupied'], obj['pfc_status'], obj['pfcflag'], obj['pfcindicator'], obj['pfcrecordingdate'], obj['pfcreleasereason'], obj['pool'], obj['property_classification'], obj['property_type'], obj['propertyid'], obj['publicutilityind'], obj['religiousind'], obj['sales_date'], obj['schoolcollegeind'], obj['schooldistrictname'], obj['seniorind'], obj['sfr_cnt'], obj['situscity'], obj['situsfullstreetaddress'], obj['situslatitude'], obj['situslongitude'], obj['situsunitnbr'], obj['situszip5'], obj['sumbuildingsqft'], obj['totalopenlienamt'], obj['totalopenliennbr'], obj['vacantflag'], obj['vacantflagdate'], obj['veteranind'], obj['welfareind'], obj['widowind'], obj['yearbuilt'], obj['years_owned'], listId))
        db.session.commit()

    return make_response(jsonify(
        result='success'
    ), 200)