from appname.models import db, Model
from datetime import date
class Notes(Model):
    __tablename__= "sfra_notes"

    id = db.Column(db.Integer, primary_key=True)
    propertyId = db.Column(db.Integer)
    uid = db.Column(db.Integer)
    note = db.Column(db.String())
    archived = db.Column(db.Boolean, default=False)
    createAt = db.Column(db.Date, default=date.today())

    def __init__(self, propertyId='', uid='', note='', archived=False, createAt=None, deleted=False):
        self.propertyId = propertyId
        self.uid = uid
        self.note = note
        self.archived = archived
        self.createdAt = createAt