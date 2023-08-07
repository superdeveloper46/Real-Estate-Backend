
from flask import Blueprint, g, json, request, make_response, jsonify, send_file

from appname.models.skiptrace import Skiptrace
from appname.models.user import User
from appname.models import db
from werkzeug.utils import secure_filename
import uuid
import os

import csv
import pandas as pd
from appname.helpers.scrapePeople import FastPeopleSearch

from datetime import datetime, timedelta

skiptrace = Blueprint('skiptrace', __name__)

@skiptrace.route("/api/skiptrace/upload", methods=["POST"])
def importFiles():
    file = request.files.getlist("files")[0]
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    hashname = str(uuid.uuid4()) + ext
    file_path = skiptrace.root_path +'/uploads/skiptrace/'+ hashname
    file.save(file_path)
        
    return make_response(jsonify(
        result='success', fileName=hashname
    ), 200)
    
@skiptrace.route("/api/skiptrace/getCSVData", methods=["POST"])
def getCSVData():
    params = request.get_json()
    fileName = params['fileName']
    filePath = skiptrace.root_path +'/uploads/skiptrace/'+ fileName
    
    ext = os.path.splitext(fileName)[1]
    if(ext != '.csv'):
        sheets = pd.ExcelFile(filePath).sheet_names
        headers = []
        rowCounts = 0
        for sheet in sheets:
            excel = pd.read_excel(filePath, sheet)
            header = [data for data in excel.columns]
            headers.append(header)
            rowCounts += excel.shape[0]
        res_data = jsonify(sheets=sheets, headers=headers, rowCounts=rowCounts)
    else:
        csv = pd.read_csv(filePath, encoding='unicode_escape')
        res_data = jsonify(sheets=['Worksheet'], headers=[[data for data in csv.columns]], rowCounts=csv.shape[0])
    
    return make_response(res_data, 200)

@skiptrace.route("/api/skiptrace/addSkiptrace", methods=["POST"])
def addSkipTrace():
    params = request.get_json()
    fileName = params['fileName']
    hashName = params['hashName']
    totalRecords = params['totalRecords']
    totalHits = params['totalHits']
    hit = params['hit']
    matches = params['matches']
    savings = params['savings']
    totalCost = params['totalCost']
    uid = g.uid
    
    
    data = Skiptrace(fileName, hashName, totalRecords, totalHits, hit, matches, savings, totalCost, uid)
    db.session.add(data)
    db.session.flush()
    db.session.commit()
    
    return make_response(jsonify(
        result='success'
    ), 200)
    
@skiptrace.route("/api/skiptrace/getSkiptrace", methods=["POST"])
def getSkiptrace():
    uid = g.uid
    params = request.get_json()
    page = params['from']
    size = params['size']
    selectedDays = params['selectedDays']
    end_date = datetime.now();
    
    if (selectedDays == 0) :
        d = timedelta(days=7)
    elif (selectedDays == 1) :
        d = timedelta(days=30)
    elif (selectedDays == 2) :
        d = timedelta(days=90)
    start_date = end_date - d
    
    if(selectedDays != -1) :
        skipData = Skiptrace.query.filter_by(uid=uid).filter(Skiptrace.created.between(start_date, end_date)).paginate(page=page, per_page=size)
    else:
        skipData = Skiptrace.query.filter_by(uid=uid).paginate(page=page, per_page=size)
        
    result = json.dumps([data.as_dict() for data in skipData.items])
    return make_response(result, 200)

@skiptrace.route("/api/skiptrace/downloadOriginFile/<string:id>", methods=["GET"])
def downloadOriginFile(id):
    data = Skiptrace.query.get(id)
    hashName = data.hashName;
    
    file_path = skiptrace.root_path +'/uploads/skiptrace/'+ hashName
    
    return send_file(file_path, as_attachment=True)

@skiptrace.route("/api/skiptrace/downloadExportFile/<string:id>", methods=["GET"])
def downloadExportFile(id):
    data = Skiptrace.query.get(id)
    hashName = "Export_"+data.hashName;
    
    file_path = skiptrace.root_path +'/uploads/skiptrace/'+ hashName
    
    return send_file(file_path, as_attachment=True)

@skiptrace.route("/api/skiptrace/createExportFile", methods=["POST"])
def createExportFile():
    params = request.get_json()
    fileName = params['fileName']
    dest = params['dest']
    input = skiptrace.root_path +'/uploads/skiptrace/'+ fileName
    output = skiptrace.root_path +'/uploads/skiptrace/'+ "Export_"+fileName
    
    fileName = secure_filename(fileName)
    ext = os.path.splitext(fileName)[1]

    file_exists = os.path.exists(output)
    if(file_exists):
        os.remove(output)    

    if(ext == '.csv'):
        csvData = pd.read_csv(input, encoding='unicode_escape')
        
        for i in range(len(csvData)):
            try:
                name = csvData[dest['firstName']][i] + ' ' + csvData[dest['lastName']][i]
                location = csvData[dest['zipCode']][i]
                
                API_KEY = "4f8f0440cff74bf0848bf6a70e0807826e9b1dc3d1f"
                obj = FastPeopleSearch(API_KEY)
                matches =  obj.search("name", {"name": name, "location": str(location)})
                response = matches[0]

                if not file_exists:
                    with open(output, mode='w', newline='') as output_file:
                        fieldnames = list(response.keys())
                        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                        writer.writeheader()

                with open(output, mode='a', newline='') as output_file:
                    fieldnames = list(response.keys())
                    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                    writer.writerow(response)
            except Exception as e:
                print(e)

    return make_response(jsonify(
        result='success'
    ), 200)
    

@skiptrace.route("/api/skiptrace/getBalance", methods=["GET"])
def getBalance():
    data = User.query.get(g.uid)
    balance = data.balance;
    
    return make_response(jsonify(
        result='success', balance=balance
    ), 200)





