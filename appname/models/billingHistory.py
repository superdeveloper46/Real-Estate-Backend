from appname.models import db, Model

class BillingHistory(Model):
    __tablename__= "sfra_billingHistory"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer)
    subscription_id = db.Column(db.String())
    amount = db.Column(db.Float)
    billing_period = db.Column(db.String())
    card_number = db.Column(db.String())
    card_name = db.Column(db.String())
    msas = db.Column(db.String())
    transaction_type = db.Column(db.String())

    def __init__(self, uid=None, subscription_id=None, amount=None, billing_period=None, card_number=None, card_name=None, msas=None, transaction_type=None, deleted=False):
        self.uid = uid
        self.subscription_id = subscription_id
        self.amount = amount
        self.billing_period = billing_period
        self.card_number = card_number
        self.card_name = card_name
        self.msas = msas
        self.transaction_type = transaction_type
        
    def create(uid, subscription_id, amount, billing_period, card_number, card_name, msas, transaction_type):
        data = BillingHistory(uid, subscription_id, amount, billing_period, card_number, card_name, msas, transaction_type)
        db.session.add(data)
        db.session.flush()
        db.session.commit()
        return data.id