from appname.models import db, Model

class ListName(Model):
    __tablename__= "sfra_listName"

    id = db.Column(db.Integer, primary_key=True)
    listName = db.Column(db.String())
    dmi = db.Column(db.Boolean, default=False)
    totalCount = db.Column(db.Integer)
    newCount = db.Column(db.Integer)
    filterCount = db.Column(db.Integer)
    createAt = db.Column(db.Date)
    updateAt = db.Column(db.Date)
    uid = db.Column(db.Integer)

    def __init__(self, listName='', dmi=False, totalCount=0, newCount=0, filterCount=0, createAt=None, updateAt=None, uid='', deleted=False):
        self.listName = listName
        self.dmi = dmi
        self.totalCount = totalCount
        self.newCount = newCount
        self.filterCount = filterCount
        self.createAt = createAt
        self.updateAt = updateAt
        self.uid = uid
        
    def create(listName, dmi, totalCount, newCount, filterCount, createAt, updateAt, uid):
        data = ListName(listName, dmi, totalCount, newCount, filterCount, createAt, updateAt, uid)
        db.session.add(data)
        db.session.flush()
        db.session.commit()
        return data.id