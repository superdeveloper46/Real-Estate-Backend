from flask import Blueprint, g, make_response, jsonify, request, json, send_file
from sqlalchemy import text

from appname.models import db
from appname.models.notes import Notes
from appname.models.files import Files

from datetime import date

from werkzeug.utils import secure_filename
import uuid
import os

properties = Blueprint('property', __name__)

# search and return property - overview data by property id
@properties.route("/api/search/property/overview/<string:propertyId>", methods=["GET"])
def getOverviewData(propertyId):
    query = text(f"""
    SELECT DISTINCT pc.description AS property_type, fo.description as owner1ownershiprights, a.situsfullstreetaddress, a.situscity, a.situsstate, a.situszip5, a.situszip4, a.propertyclassid, a.yearbuilt, a.bedrooms, a.bathtotalcalc, a.sumbuildingsqft, a.lotsizesqft, a.currentavmvalue, a.totalopenlienamt, a.currentavmvalue - a.totalopenlienamt AS equity, a.currentsalesprice, date(a.currentsalecontractdate::text), a.ownername1full, a.ownername2full, a.hoa1name, f.county, f.msa, a.apn, a.owneroccupied,	
    date_part('year', now()) - date_part('year', date(a.currentsalecontractdate::text)) years, date_part('month', now()) - date_part('month', date(a.currentsalecontractdate::text)) months, a.islistedflag AS listed, o.count, o.resi_cnt, o.sfr_cnt, o.pids, fo.description AS owner_type, s.fname || ' ' || s.lname AS contact_name, i.age	
    FROM assessor AS a
    LEFT JOIN fa_prop_cl_ind pc ON pc.code = a.propertyclassid
    LEFT JOIN fips_correct f ON f.fips_code = a.fips
    LEFT JOIN owner_names_mailing_address o ON o.mailingfullstreetaddress = a.mailingfullstreetaddress AND o.mailingzip5 = a.mailingzip5
    LEFT JOIN fa_owner_vest fo ON fo.code = a.owner1ownershiprights
    LEFT JOIN sim_scores s ON s.propertyid = a.propertyid AND similarity_score_on1 >= .8
    LEFT JOIN infutor i ON i.pid = s.pid
    WHERE a.propertyid = {propertyId}
    """)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'status': 200}), 200)

# search and return property - property data with by property id
@properties.route("/api/search/property/property/<string:propertyId>", methods=["GET"])
# @token_required
def getPropertyData(propertyId):
    query = text(f"""
    SELECT DISTINCT a.ownername1full, a.mailingcity, a.situscity, a.situszip5, fp.description as property_class, fs.description as stories, a.yearbuilt, a.sumbuildingsqft, pf.description AS pfc_status, date(a.currentsalecontractdate::text)as sales_date, a.lotsizesqft, a.vacantflag, a.bedrooms, a.bathtotalcalc, fs.description AS stories, nullif(a.totalrooms,0) AS totalrooms, a.buildingqualitycode, a.propertyclassid, l.description AS property_type, a.zoning, a.landusecode, a.fips, a.apn, a.situsfullstreetaddress, a.situslatitude, a.situslongitude, a.subdivisionname, a.situscensustract, a.situscensusblock, a.situscarriercode, a.legaldescription, a.schooldistrictname, a.lotnbr, a.currentavmvalue, a.assdtotalvalue, a.assdlandvalue, a.assdimprovementvalue, a.assdyear, a.taxyear, a.taxamt, a.taxratecodearea, f.county, a.hoa1name, a.hoa1type, a.hoa1feevalue, a.hoa1feefrequency, a.hoa2name, a.hoa2type, a.hoa2feevalue, a.hoa2feefrequency, a.currentsaledocumenttype, a.currentsaledocnbr, a.currentsalebuyer1fullname, a.currentsalebuyer2fullname, a.currentsaleseller1fullname, a.currentsaleseller2fullname, a.currentsalesprice, a.currentsalerecordingdate, a.currentavmvalue - a.totalopenlienamt AS equity, a.countylandusecode, fp.description AS property_class, fh.description AS heatcode, fg.description AS garage, a.fireplacecode, fb.description AS buildingquality, fa_ac.description AS airconditioning	
    FROM assessor a	
    LEFT JOIN fa_lu_code l ON l.code = a.landusecode	
    LEFT JOIN fips_correct f ON f.fips_code = a.fips	
    LEFT JOIN fa_prop_cl_ind fp ON fp.code = a.propertyclassid	
    LEFT JOIN fa_stories fs ON fs.code = a.storiesnbrcode	
    LEFT JOIN fa_heat fh ON fh.code::int = a.heatcode	
    LEFT JOIN fa_garage fg ON fg.code::int = a.garage	
    LEFT JOIN fa_buildingquality fb ON fb.code::int = a.buildingqualitycode	
    LEFT JOIN fa_ac ON fa_ac.code::int = a.airconditioningcode
    LEFT JOIN fa_preforeclosure pf ON pf.code::int = a.pfcindicator
    WHERE propertyid = {propertyId}
    """)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'status': 200}), 200)

# search and return property - current mortgages data by property id
@properties.route("/api/search/property/current-mortgages/<string:propertyId>", methods=["GET"])
def getCurrentMortgagesData(propertyId):
    query = text(f"""
    SELECT DISTINCT 
    a.mtg1lienposition, a.mtg1recordingdate, d.documentnbr AS mtg1documentnbr, a.mtg1loanamt, a.mtg1lender, fa.description AS mtg1loantype, d.FirstMtgInterestRate AS mtg1interestrate, a.mtg1term, d.firstmtgduedate AS mtg1duedate, 
    a.mtg2lienposition, a.mtg2recordingdate, d2.documentnbr AS mtg2documentnbr, a.mtg2loanamt, a.mtg2lender, fa2.description AS mtg2loantype, d2.FirstMtgInterestRate AS mtg2interestrate, a.mtg2term, d2.firstmtgduedate AS mtg2duedate, 
    a.mtg3lienposition, a.mtg3recordingdate, d3.documentnbr AS mtg3documentnbr, a.mtg3loanamt, a.mtg3lender, fa3.description AS mtg3loantype, d3.FirstMtgInterestRate AS mtg3interestrate, a.mtg3term, d3.firstmtgduedate AS mtg3duedate, 
    a.mtg4lienposition, a.mtg4recordingdate, d4.documentnbr AS mtg4documentnbr, a.mtg4loanamt, a.mtg4lender, fa4.description AS mtg4loantype, d4.FirstMtgInterestRate AS mtg4interestrate, a.mtg4term, d4.firstmtgduedate AS mtg4duedate
    FROM assessor a
    LEFT JOIN deed d ON d.fatransactionid = a.mtg1transactionid
    LEFT JOIN deed d2 ON d2.fatransactionid = a.mtg2transactionid
    LEFT JOIN deed d3 ON d3.fatransactionid = a.mtg3transactionid
    LEFT JOIN deed d4 ON d4.fatransactionid = a.mtg4transactionid
    LEFT JOIN fa_loan_type fa ON fa.code = a.mtg1loantype
    LEFT JOIN fa_loan_type fa2 ON fa2.code = a.mtg2loantype
    LEFT JOIN fa_loan_type fa3 ON fa3.code = a.mtg3loantype
    LEFT JOIN fa_loan_type fa4 ON fa4.code = a.mtg4loantype
    WHERE a.propertyid = {propertyId}
    """)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'status': 200}), 200)

# search and return property - mortgage & transaction history data by property id
@properties.route("/api/search/property/transaction_mortgage-history/<string:propertyId>", methods=["GET"])
def getMortgageAndTransactionHistoryData(propertyId):
    query = text(f"""
    SELECT DISTINCT date(d.recordingdate::text) AS recordingdate, date(d.saledate::text) AS saledate, d.buyerborrower1name, d.seller1name, d.saleamt, fl.description AS loan_type, d.firstmtglendername, d.firstmtgterm, date(d.firstmtgduedate::text) AS loan_due_date, d.firstmtgamt, d.firstmtgdocumentnbr, d.firstmtgdocumenttype
    FROM deed d
    LEFT JOIN fa_loan_type fl ON fl.code = d.firstmtgloantype
    WHERE d.propertyid = {propertyId}
    """)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'status': 200}), 200)

# search and return property - owner demographics data by property id
@properties.route("/api/search/property/owner-demographics/<string:propertyId>", methods=["GET"])
def getOwnerDemographicsData(propertyId):
    planType = 'plus' # static temp data for paywall plan
    
    basicPlanColumns = "i.fname || ' ' || i.lname AS contact_name, i.gender, i.age, io.description occupation"
    plusPlanColumns = f"""{basicPlanColumns}, 
    case when i.marriedcd = 'S' then 'Single' when marriedcd = 'M' then 'Married' else null end AS married, l.description AS language, i.hhnbr, i.child, i.childagecd_6, i.childagecd_6_10, i.childagecd_11_15, i.childagecd_16_17,		
    case when childagecd_6 is NOT null or childagecd_6_10 is NOT null or childagecd_11_15 is NOT null or childagecd_16_17 is NOT null then 'Child Under 18 Present' else 'No Child Present' end AS child_present, i.sglparent
    """
    premiumPlanColumns = f"""{plusPlanColumns},
    w.description AS estimated_net_worth,		
    case when i.ct_homeimprove12_any is NOT null or i.ct_homeremodel12_any is NOT null then 'Likely home improvement done' else 'No information ON home improvement done' end AS home_improvement, i.CT_MEDIA_HEAVYUSAGE_INTERNET, hh.name AS cluster_name, hh.description AS cluster_description, i.fmclstrdcd, e.description AS likely_ethnicity, i.lifestg_clstrd, i.lifestg_grpcd, ehi.description AS estimated_income		
    """
    
    selectedColumns = ""
    if planType == "basic":
        selectedColumns = basicPlanColumns
    elif planType == "plus":
        selectedColumns = plusPlanColumns
    elif planType == "premium":
        selectedColumns = premiumPlanColumns
    
    query = text(f"""
    SELECT DISTINCT {selectedColumns} 
    FROM assessor a		
    LEFT JOIN fa_prop_cl_ind pc ON pc.code = a.propertyclassid		
    LEFT JOIN fips_correct f ON f.fips_code = a.fips		
    LEFT JOIN owner_names_mailing_address o ON o.mailingfullstreetaddress = a.mailingfullstreetaddress AND o.mailingzip5 = a.mailingzip5		
    LEFT JOIN fa_owner_vest fo ON fo.code = a.owner1ownershiprights		
    LEFT JOIN sim_scores s ON s.propertyid = a.propertyid AND (similarity_score_on1 >= .8 or similarity_score_on2 >= .8)		
    LEFT JOIN infutor i ON i.pid = s.pid		
    LEFT JOIN inf_ehi ehi ON i.ehi = ehi.code		
    LEFT JOIN inf_wealthscore w ON w.code = i.wealthscr		
    LEFT JOIN inf_language l ON i.languagecd = l.code		
    LEFT JOIN inf_ethnicity e ON e.code = i.ethnicitycd		
    LEFT JOIN inf_occupation io ON io.code = i.occupationcd		
    LEFT JOIN inf_hhcl hh ON hh.code = i.hhclstrdcd		
    WHERE a.propertyid = {propertyId}
    """)
    
    results = db.engine.execute(query)
    return make_response(jsonify({'result' : [dict(r) for r in results][0], 'planType': planType, 'status': 200}), 200)

# Note
@properties.route("/api/property/addNote", methods=["POST"])
def addNote():
    params = request.get_json()

    propertyId = params['propertyId']
    note = params['note']
    archived = params['archived']
    createAt = date.today()
    uid = g.uid
    
    data = Notes(propertyId, uid, note, archived, createAt)
    db.session.add(data)
    db.session.flush()
    db.session.commit()
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@properties.route("/api/property/editNote", methods=["POST"])
def eidtNote():
    params = request.get_json()

    id = params['id']
    note = params['note']
    archived = params['archived']
    
    data = Notes.query.get(id)
    data.note = note
    data.archived = archived
    db.session.commit()
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@properties.route("/api/property/getnotes", methods=["POST"])
def getNotes():
    params = request.get_json()

    propertyId = params['propertyId']
    createAt = params['createAt']
    archived = params['archived']
        
    notes = Notes.query.filter_by(propertyId=propertyId).filter_by(archived=archived).filter_by(createAt=createAt).filter_by(uid=g.uid)
    
    result = json.dumps([data.as_dict() for data in notes])
    return make_response(result, 200)

@properties.route("/api/property/deletenote", methods=["POST"])
def deleteNote():
    params = request.get_json()
    id = params['id']
    
    data = Notes.query.get(id)
    db.session.delete(data)
    db.session.commit();
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@properties.route("/api/property/archivenote", methods=["POST"])
def archiveNote():
    params = request.get_json()
    id = params['id']
    archived = params['archived']
    
    data = Notes.query.get(id)
    data.archived = archived
    db.session.commit();
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
# File&Photos
@properties.route('/api/property/addFiles', methods=['POST'])
def addFiles():
    uploadFolder = '';
    uid = g.uid
    type = request.form.get('type');
    propertyId = request.form.get('propertyId');
    if type == '0':
        uploadFolder = 'files';
    else :
        uploadFolder = 'photos'
        
    files = request.files.getlist("files")
    for file in files:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        hashname = str(uuid.uuid4()) + ext
        file_path = properties.root_path +'/uploads/'+uploadFolder+'/'+ hashname
        file.save(file_path)
        
        data = Files(propertyId, uid, file.filename, hashname, os.path.getsize(file_path), int(type))
        db.session.add(data)
        db.session.flush()
        db.session.commit()
    return make_response(jsonify(
        result='success'
    ), 200)
    
@properties.route("/api/property/getfiles", methods=["POST"])
def getFiles():
    params = request.get_json()

    searchKey = params['searchKey']
    propertyId = params['propertyId']
    type = params['type']
    
    if(searchKey == ''):
        files = Files.query.filter_by(propertyId=propertyId).filter_by(type=type).filter_by(uid=g.uid)
    else :
        files = Files.query.filter_by(propertyId=propertyId).filter(Files.name.like('%'+searchKey+'%')).filter_by(type=type).filter_by(uid=g.uid)
    
    result = json.dumps([data.as_dict() for data in files])
    return make_response(result, 200)

@properties.route("/api/property/deletefile", methods=["POST"])
def deleteFile():
    params = request.get_json()
    id = params['id']
    type = params['type']
    
    data = Files.query.get(id)
    hashname = data.hashname;
    db.session.delete(data)
    db.session.commit();
    
    if type == '0':
        uploadFolder = 'files';
    else :
        uploadFolder = 'photos'
    
    file_path = properties.root_path +'/uploads/'+uploadFolder+'/'+ hashname
    
    os.remove(file_path)
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@properties.route("/api/property/downloadFile/<string:id>/<string:type>", methods=["GET"])
def downloadFile(id, type):
    data = Files.query.get(id)
    hashname = data.hashname;
    
    if type == '0':
        uploadFolder = 'files';
    else :
        uploadFolder = 'photos'
    
    file_path = properties.root_path +'/uploads/'+uploadFolder+'/'+ hashname
    
    return send_file(file_path, as_attachment=True)
