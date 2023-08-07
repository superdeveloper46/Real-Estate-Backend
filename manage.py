#!/usr/bin/env python

import os
import binascii

import click

from flask_migrate import Migrate

from appname import create_app
from appname.models import db
from appname.extensions import cache
# Explictly import models here to to get Flask Migrate to pick them up
from appname.models import *  # noqa
from appname.models.user import User
from appname.controllers.elasticsearch.listbuilder import injectPropertyListDataToElasticsearch
from appname.controllers.elasticsearch.base import esDelete, esCount

# default to dev config because this should not be run in production
env = os.environ.get('APPNAME_ENV', 'dev')
app = create_app('appname.settings.%sConfig' % env.capitalize())

migrate = Migrate(app, db)

@app.cli.command("server")
def server():
    """ Run a debug server. When possible use 
    ` $ FLASK_APP=manage FLASK_ENV=development flask run `
    Do not use this for production (since it runs in debug mode)
    """
    return app.run(host='0.0.0.0', port=5000, debug=True)

@app.cli.command()
def initdb():
    """ Creates a database with all of the tables defined in
        your SQLAlchemy models
    """
    click.echo('Initalizing the db')
    db.create_all()

def actually_drop_tables():
    if env != 'dev':
        confirm = input("Are you sure you want to run this on {}?".format(env))
        if confirm.lower().strip() != 'yes':
            return
    click.echo('Dropping the db')
    db.drop_all()

@app.cli.command()
def dropdb():
    """ Drops the tables.
        In dev: loads seed data
    """
    actually_drop_tables()

def seed_data():
    """ Create test users. """
    default_user = User("user@example.com", "test", admin=False)
    db.session.add(default_user)
    click.echo("Added user@example.com")
    admin = User("admin@example.com", "admin", admin=True, email_confirmed=True)
    db.session.add(admin)
    click.echo("Added admin@example.com")

@app.cli.command("reset-db")
def resetdb():
    """ Drops the tables & loads seed data
    """
    actually_drop_tables()
    db.create_all()
    if env == 'dev':
        # If you get a bunch of models, it might make sense to specify these
        seed_data()

@app.cli.command("clear-cache")
def clear_cache():
    """ Flush the cache."""
    cache.clear()
    click.echo("Cache Flushed")

@app.cli.command()
def generate_session_key():
    """ Helper for admins to generate random 26 character string. Used as the
        secret key for sessions. Must be consistent (and secret) per environment.
        Output: b'random2323db3....1abna'
        Copy the value in between the quotation marks to the settings file
    """
    click.echo(binascii.hexlify(os.urandom(26)))

@app.cli.command("create-seeds")
def create_seeds():
    seed_data()

# inject - indexing necessary data from main db (postgresql) to Elasticsearch 
@app.cli.command("es-inject")
def es_inject_all_index_data():
    try:
        injectPropertyListDataToElasticsearch()
        click.echo('Successfully created indices and injected data to Elasticsearch')
    except Exception as e:
        click.echo(e)
        
# delete all given indices from Elasticsearch
@app.cli.command("es-delete")
def es_delete_all_indices():
    try:
        esDelete('sfra_propertylist')
        click.echo('Successfully deleted Elasticsearch indices')
    except Exception as e:
        click.echo(e)
        
@app.cli.command("es-count")
def es_count_all_indices():
    try:
        count = esCount('sfra_propertylist')
        print(count)
        click.echo('Successfully counted Elasticsearch indices')
    except Exception as e:
        click.echo(e)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User)


if __name__ == "__main__":
    # For flask scripts to work, an application needs to be discovered.
    # We can do that by setting the FLASK_APP environment variable to point to this file
    # Read more: http://flask.pocoo.org/docs/0.12/cli/
    os.environ['FLASK_APP'] = __file__
    app.cli()
