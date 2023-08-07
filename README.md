## SFR Analytics - SaaS Backend in Flask

## Setup
Usage of Python 3 is required. It can be installed [on Python.org](https://www.python.org/downloads/)
```
# Optional but recommended:
python3 -m venv env;
source env/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
python3 manage.py server # or `FLASK_APP=manage FLASK_ENV=development flask run`
```
## Running

```
# Development
# If using a virtual env: source env/bin/activate
./manage.py reset-db # to seed data
FLASK_APP=manage FLASK_ENV=development flask run

# Go to localhost:5000 in a browser and click on Login
# Login with the following credentials "user@example.com", "test

# Production documentation in the repository.
```

### Enabling Cloudwatch Prerequisite (Optional)
Run this environment on terminal. Make sure the credential provided is the credential that have access to cloudwatch
```
export AWS_ACCESS_KEY_ID=<aws-access-key>
export AWS_SECRET_ACCESS_KEY=<aws-secret-access-key>
```
Then restart the webserver

### Local Secrets

To configure OAuth login and Stripe billing in development, you will need to set some environment variables. See `.env.local.sample` for an example.

```bash
cp .env.local.sample .env.local
# Edit .env.local with your Database Credentials (Host, Port, Username, Password, DB Name)
postgresql://username:password@host:port/dbname
# Edit .env.local with your Stripe & Google test keys
source .env.local
flask run
```

You may also want to change some of the constants in `appname.constants`

### Elastichsearch
# inject - indexing necessary data from main db (postgresql) to Elasticsearch 
```
# Go to project folder and run the command
es-inject
```
# delete all given indices from Elasticsearch
```
# Go to project folder and run the command
es-delete
```