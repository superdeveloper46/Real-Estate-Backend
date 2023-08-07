from flask import Blueprint, make_response, jsonify, request, g
from flask import jsonify

from appname.models import db
from appname.models.user import User
from appname.models.billingHistory import BillingHistory
from appname.models.subscriptions import Subscriptions
from appname.services.stripe import Stripe

from datetime import date, datetime, timedelta

import os


billings = Blueprint('billing', __name__)

@billings.route("/api/stripe/subscription/create", methods=["POST"])
def createSubscription():
    # Params
    params = request.get_json()
    email = params['email']
    name = params['name']
    msas = params['msas']
    amount = 1250 * (len(msas) + 1)
    billing_plan = params['billingPlan']
    billing_period = params['billingPeriod']
    paymentmethod_id = params['paymentMethodId']
    
    # Select current user
    user = User.query.filter_by(id=g.uid).first()
    
    # Get customer id
    if user.billing_customer_id:
        customer_id = user.billing_customer_id
        Stripe.attach_paymentmethod_to_customer(paymentmethod_id=paymentmethod_id, customer_id=customer_id)
    else:
        customer_id = Stripe.create_customer(name=name, paymentmethod_id=paymentmethod_id)
        
    # Modify selected payment method as default
    Stripe.modify_paymentmethod_to_default(paymentmethod_id=paymentmethod_id, customer_id=customer_id)
    
    # get all product/price list
    price_id = ''
    priceData = Stripe.get_prices()
    for price in priceData:
        if(price.unit_amount == amount):
            price_id = price.id
            
    # create product
    if(price_id == ''):
        price_id = Stripe.create_product(product_name='SFRA Yearly Paid Plan - '+str(amount), amount=amount*100, currency='usd', description='This is auto created product')
    
    # create subscription
    subscription_id = Stripe.create_subscription(customer_id=customer_id, price_id=price_id)
    
    user.billing_customer_id = customer_id
    user.subscription_id = subscription_id
    user.billing_start_date = datetime.now()
    user.billing_end_date = datetime.now() + timedelta(days=365)
    user.billing_period = billing_period
    user.msas = msas
    
    db.session.add(user)
    db.session.commit()
    
    BillingHistory.create(g.uid, subscription_id, amount, billing_period, "card_number", name, msas, "created")
    
    return make_response(jsonify(
        subscriptionId=subscription_id
    ), 200)

@billings.route("/api/stripe/subscription/retrieve", methods=["POST"])
def retrieveSubscription():
    # Params
    params = request.get_json()
    email = params['email']

    # Select current user
    user = User.query.filter_by(email=email).first()

    try:
        # Get subscription id and data
        subscription_id = user.subscription_id
        
        subscription = Subscriptions.query.filter_by(subscription_id=subscription_id).first()
        return make_response(jsonify(
            priceId=subscription.price_id,
            plan=subscription.plan,
            period=subscription.period,
            subscriptionId=subscription.subscription_id,
        ), 200)
    except:    
        return make_response(jsonify(
            response_error_message='Subscription does not exist'
        ), 204)

@billings.route("/api/stripe/savedcards/get", methods=["POST"])
def getSavedCards():
    # Params
    params = request.get_json()
    email = params['email']
    
    # Select current user
    user = User.query.filter_by(email=email).first()
    
    # If user exists, return saved payment methods list
    if user.billing_customer_id:
        savedCards = Stripe.get_savedcards(customer_id=user.billing_customer_id)
        return make_response(jsonify(savedCards), 200)
    else:
        return make_response(jsonify([]), 200)
    