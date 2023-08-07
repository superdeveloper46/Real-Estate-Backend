from appname.models import db, Model
from datetime import date
class Files(Model):
    __tablename__= "sfra_files"

    id = db.Column(db.Integer, primary_key=True)
    propertyId = db.Column(db.Integer)
    uid = db.Column(db.Integer)
    name = db.Column(db.String())
    hashname = db.Column(db.String())
    size = db.Column(db.Integer)
    type = db.Column(db.Integer)

    def __init__(self, propertyId='', uid='', name='', hashname='', size=0, type=0, deleted=False):
        self.propertyId = propertyId
        self.uid = uid
        self.name = name
        self.hashname = hashname
        self.size = size
        self.type = type