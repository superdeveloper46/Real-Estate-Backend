from appname.models import db, Model

class Filters(Model):
    __tablename__= "sfra_filters"

    id = db.Column(db.Integer, primary_key=True)
    listId = db.Column(db.Integer)
    dataId = db.Column(db.String())
    key = db.Column(db.String())
    value = db.Column(db.String())

    def __init__(self, listId='', dataId='', key='', value='', deleted=False):
        self.listId = listId
        self.dataId = dataId
        self.key = key
        self.value = value