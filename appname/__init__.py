#! ../env/bin/python

from flask import Flask, render_template, make_response, request, g, jsonify
from flask_cors import CORS
from webassets.loaders import PythonLoader as PythonAssetsLoader

from appname import assets
from appname import constants
from appname.models import db
from appname.api.resources import api_blueprint
from appname.api import handle_api_error
from appname.controllers.main import main
from appname.controllers.auth import auth
from appname.controllers.oauth import google_blueprint
from appname.controllers.store import store
from appname.controllers.settings import settings_blueprint
from appname.controllers.admin.jobs import jobs
from appname.controllers.webhooks.stripe import stripe_blueprint
from appname.controllers.dashboard import dashboard_blueprints
from appname.controllers.property import properties
from appname.controllers.billing import billings
from appname.controllers.geo import geo
from appname.controllers.elasticsearch.listbuilder import listbuilder
from appname.controllers.mylist import mylist
from appname.controllers.skiptrace import skiptrace
from appname.controllers.profile import profile 
from appname.controllers.buyerview import buyerView 
from appname.controllers.privateLenders.lenders import lenders
from appname.helpers import view as view_helpers
from appname.helpers.cloudwatch_logger import setup_cloudwatch_logger
from appname.converter import custom_converters
from appname.extensions import (
    admin,
    assets_env,
    cache,
    csrf,
    debug_toolbar,
    hashids,
    login_manager,
    limiter,
    mail,
    rq2,
    sentry,
    stripe,
    token
)
from appname.forms import SimpleForm

import jwt
import os
import traceback
from datetime import datetime, timedelta
from appname.controllers.token import token_required

def create_app(object_name):

    app = Flask(__name__)
    setup_cloudwatch_logger()

    CORS(app)

    app.config.from_object(object_name)

    # initialize the cache
    cache.init_app(app)

    # initialize the debug tool bar
    debug_toolbar.init_app(app)

    # initialize SQLAlchemy
    db.init_app(app)

    # initalize Flask Login
    login_manager.init_app(app)

    # initialize Flask-RQ2 (job queue)
    rq2.init_app(app)

    # CSRF Protection
    # csrf.init_app(app)

    # Special URL converters
    custom_converters.init_app(app)

    token.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    stripe.init_app(app)
    hashids.init_app(app)

    def log_error(error, status_code):
        stack_trace = traceback.format_exc()
        app.logger.error(dict(
            request_id=g.request_id,
            type='ERROR',
            http_status=status_code,
            message=str(error),
            traceback=stack_trace 
        ))

    if app.config.get('SENTRY_DSN') and not app.debug:
        sentry.init_app(app, dsn=app.config.get('SENTRY_DSN'))

        @app.errorhandler(500)
        def internal_server_error(error):
            log_error(error, 500)
            return render_template('errors/500.html',
                                   event_id=g.sentry_event_id,
                                   public_dsn=sentry.client.get_public_dsn(
                                       'https')
                                   ), 500

    @app.errorhandler(404)
    def not_found_error(error):
        log_error(error, 404)
        if request.path.startswith("/api"):
            return handle_api_error(error)
        return render_template('errors/404.html'), 404

    @app.errorhandler(401)
    def permission_denied_error(error):
        log_error(error, 401)
        if request.path.startswith("/api"):
            return handle_api_error(error)
        return render_template('tabler/401.html'), 401
    
    # Handle all other errors
    @app.errorhandler(Exception)
    def handle_general_error(error):
        log_error(error, 500)
        return render_template('errors/500.html'), 500

    @app.before_request
    @token_required
    def before_request(current_user):
        if(current_user != ''):
            g.uid = current_user.id
        pass

    @app.after_request
    def after_request(response):
        app.logger.info(
            dict(
                request_id=g.request_id,
                type='RESPONSE',
                http_status=response.status_code
            )
        )
        return response

    # Import and register the different asset bundles
    assets_env.init_app(app)
    assets_loader = PythonAssetsLoader(assets)
    for name, bundle in assets_loader.load_bundles().items():
        assets_env.register(name, bundle)

    # register our blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(properties)
    app.register_blueprint(billings)
    app.register_blueprint(geo)
    app.register_blueprint(listbuilder)
    app.register_blueprint(google_blueprint, url_prefix='/oauth')
    app.register_blueprint(store)
    app.register_blueprint(settings_blueprint)
    app.register_blueprint(mylist)
    app.register_blueprint(skiptrace)
    app.register_blueprint(profile)
    app.register_blueprint(lenders)
    app.register_blueprint(buyerView)

    # Register user dashboard blueprints
    for blueprint in dashboard_blueprints:
        app.register_blueprint(blueprint, url_prefix='/dashboard')

    # API
    app.register_blueprint(api_blueprint, url_prefix='/api')
    csrf.exempt(api_blueprint)

    app.register_blueprint(stripe_blueprint, url_prefix='/webhooks')
    csrf.exempt(stripe_blueprint)

    # Admin Tools
    app.register_blueprint(jobs, url_prefix='/admin/rq')
    admin.init_app(app)
    
    @app.route("/api/auth/refresh", methods=["POST"])
    @token_required
    def refresh(current_user):
        access_token = jwt.encode({
            'id': g.uid,
            'exp' : datetime.utcnow() + timedelta(hours = 1)
        }, os.getenv('SECRET_KEY'))
        return make_response(jsonify(access_token=access_token.decode('UTF-8')), 200)
    
    @app.route("/api/auth/validate", methods=["GET"])
    def authValidate():
        return make_response(jsonify(
            status='ok'
        ), 200)

    return app