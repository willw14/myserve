#!/bin/bash
export source FLASK_APP="flaskr"
export source FLASK_DEBUG=1
export source GOOGLE_CLIENT_ID='201549234557-q6qrci2pp2m6mt077crps8s68co2s6gl.apps.googleusercontent.com'
export source GOOGLE_CLIENT_SECRET='RQjP5bin1qvQgHrVKCahcD1D'
flask run --cert='cert.pem' --key='key.pem'