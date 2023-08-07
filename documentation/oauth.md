OAuth is backed by Flask-Dance

## Setup

## Providers

### Google

#### Configuration:

* Get API Keys here: https://console.developers.google.com/apis/credentials
* Add "http://localhost:5000/oauth/google/authorized" and "https://[your production website]/oauth/google/authorized" to the authorized redirects

Make sure you set the following environment variables so that you can try this locally.

```
export OAUTHLIB_INSECURE_TRANSPORT=1 # To allow local logins without having to use  HTTPs locally
export GOOGLE_CONSUMER_KEY='your-code.apps.googleusercontent.com'
export GOOGLE_CONSUMER_SECRET='your-secret'
```

#### Implementation:

See `appname/controllers/google.py`.

