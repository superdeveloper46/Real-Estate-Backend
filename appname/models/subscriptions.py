from appname.models import db, Model

class Subscriptions(Model):
    __tablename__= "stripe_subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    price_id = db.Column(db.String())
    plan = db.Column(db.String())
    period = db.Column(db.String())
    customer_id = db.Column(db.String())
    subscription_id = db.Column(db.String())
    
    def __init__(self, price_id=None, plan=None, period=False,
                 customer_id=False, subscription_id=None, deleted=False):
        self.price_id=price_id
        self.plan=plan
        self.period=period
        self.customer_id=customer_id
        self.subscription_id=subscription_id