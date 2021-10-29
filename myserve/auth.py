import json
from flask import Flask, redirect, request, url_for, Blueprint, render_template, flash
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
import os
from myserve.models import User

auth = Blueprint('auth', __name__)

# this code is adapted from realpython.com
# get the various info we need from the environment for security purposes
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route("/login")
def login():
    # find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["email", "profile"],
    )
    return redirect(request_uri)


@auth.route("/login/callback")
def callback():
    # get authorization code Google sent back to
    code = request.args.get("code")

    if not code:
        flash("User email not available or not verified by Google.", "error")
        return redirect(url_for("auth.index"))

    # find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # prepare and send request to get tokens
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

    # parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # request profile info from Google server.
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # get verified user's profil info
    if userinfo_response.json().get("email_verified"):
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        first_name = userinfo_response.json()["given_name"]
        last_name = userinfo_response.json()["family_name"]
    else:
        flash("User email not available or not verified by Google.", "error")
        return redirect(url_for("auth.index"))

    user = User.load_by_email(users_email)
    if user:
        # updates the user's record with their info from Google in case
        # anything e.g. picture has changed
        user.update(first_name, last_name, picture)

        login_user(user, remember=True)
        # due to redirects, this wil still send staff to their dashboard
        redirect_to = "student.dashboard"
    else:
        redirect_to = "auth.index"
        flash("This account hasn't been granted access to MyServe. This service is only accessible to Year 13 students and staff. If you believe you should have access, please your system administrator.", "error")
    return redirect(url_for(redirect_to))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))
