import stripe

class Stripe:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
        if app.debug:
            stripe.verify_ssl_certs = False
            
    def modify_paymentmethod_to_default(paymentmethod_id, customer_id):
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                "default_payment_method": paymentmethod_id
            }
        )
    
    def attach_paymentmethod_to_customer(paymentmethod_id, customer_id):
        stripe.PaymentMethod.attach(
            paymentmethod_id,
            customer=customer_id
        )

    def create_customer(name, paymentmethod_id):       
        customer = stripe.Customer.create(name=name)
        stripe.PaymentMethod.attach(paymentmethod_id, customer=customer.id)
        return customer.id   
 
    def create_subscription(customer_id, price_id):
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[
                {"price": price_id},
            ],
        )
        
        return subscription.id
    
    def cancel_subscription(subscription_id):
        return stripe.Subscription.delete(
            subscription_id,
        )
            
    def retrieve_subscription(subscription_id):
        return stripe.Subscription.retrieve(subscription_id)
    
    def retrieve_invoice(invoice_id):
        return stripe.Invoice.retrieve(invoice_id)
    
    def create_refund(charge_id, amount):
        stripe.Refund.create(charge=charge_id, amount=amount)
        
    def get_savedcards(customer_id):
        savedCards = stripe.Customer.list_payment_methods(
            customer_id,
            type="card",
            limit=3,
        )
        
        return savedCards
    
    def create_product(product_name, amount, currency, description):
        product = stripe.Product.create(
            name=product_name,
            description=description,
        )
        
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=currency,
            recurring={"interval": "year"},
        )
        return price.id 
    
    def get_products():
        products = stripe.Product.list()
        return products.data
    
    def get_prices():
        prices = stripe.Price.list()
        return prices.data
    
    
    