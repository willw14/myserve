import json
from flask import Flask, redirect, request, url_for, Blueprint, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
#from flaskr import init_db_command
from oauthlib.oauth2 import WebApplicationClient
import requests
import os
from flaskr.models import User

auth = Blueprint('auth', __name__)

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

#ADD ERROR HANDLING
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@auth.route('/')
def index():
    return render_template('auth/index.html')

@auth.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@auth.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        first_name = userinfo_response.json()["given_name"]
        last_name = userinfo_response.json()["family_name"]
    else:
        return "User email not available or not verified by Google.", 400
    users_email = "17087@burnside.school.nz"
    if User.is_user(users_email):
        user = User.load(users_email)

        #Updates the user's record with their info from Google in case anything e.g. picture has changed
        user.update(unique_id, first_name, last_name, picture)

        login_user(user, remember=True)
        redirect_to = "student.dashboard"
    else:
        redirect_to = "auth.index"
    #ADD SOME SORT OF HANDLING IF USER HASN'T BEEN GRANTED ACCESS
    return redirect(url_for(redirect_to))
    

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))



