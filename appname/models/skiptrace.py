from appname.models import db, Model

class Skiptrace(Model):
    __tablename__= "sfra_skiptrace"

    id = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.String())
    hashName = db.Column(db.String())
    totalRecords = db.Column(db.Integer)
    totalHits = db.Column(db.Integer)
    hit = db.Column(db.Float)
    matches = db.Column(db.Integer)
    savings = db.Column(db.Float)
    totalCost = db.Column(db.Float)
    uid = db.Column(db.Integer)

    def __init__(self, fileName='', hashName='', totalRecords=0, totalHits=0, hit=0, matches=0, savings=0, totalCost=0, uid='', deleted=False):
        self.fileName = fileName
        self.hashName = hashName
        self.totalRecords = totalRecords
        self.totalHits = totalHits
        self.hit = hit
        self.matches = matches
        self.savings = savings
        self.totalCost = totalCost
        self.uid = uid