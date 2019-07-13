import os
import re
import secrets
from collections import defaultdict
from functools import wraps
from typing import List, Tuple

import flask
import lxml.html
import requests

import db
import rapde
import youtube

app = flask.Flask(__name__)
app.secret_key = secrets.SECRET_KEY


@app.route("/")
def index():
    return links()


def authorized(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "credentials" not in flask.session:
            return flask.redirect("/authorize")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/add")
@authorized
def add():
    posts: List[Tuple[int, str, str]] = rapde.fetch_posts(200)
    video_ids: List[str] = rapde.extract_video_ids(posts)
    unique_video_ids: List[str] = list(set(video_ids))

    db.insert_posts(posts)

    for video_id in unique_video_ids:
        youtube.add_video_to_playlist(video_id=video_id)

    return links()


@app.route("/list")
@authorized
def list_playlist_items():
    items = youtube.get_all_playlist_items()
    return flask.jsonify(items)


@app.route("/duplicates")
@authorized
def duplicates():
    items = youtube.get_all_playlist_items()

    grouped_items = defaultdict(list)
    for item in items:
        grouped_items[item["snippet"]["resourceId"]["videoId"]].append(item)

    duplicate_groups = {
        video_id: values
        for video_id, values in grouped_items.items()
        if len(values) > 1
    }
    # duplicate_groups["_size"] = len(duplicate_groups)

    return flask.jsonify(duplicate_groups)


@app.route("/clear")
@authorized
def clear():
    items = youtube.get_all_playlist_items()
    for item in items:
        youtube.delete_playlist_item(playlist_item_id=item["id"])

    return links()


def links():
    return """<ul>
<li><a href="/">Index</a></li>
<li><a href="/list">List</a></li>
<li><a href="/duplicates">Duplicates</a></li>
<li><a href="/add">add</a></li>
<li><a href="/clear">clear</a></li>
</ul>"""


@app.route("/initdb")
def initdb():
    db.init_db()
    return links()


@app.route("/authorize")
def authorize():
    authorization_url = youtube.authorize()
    return flask.redirect(authorization_url)


@app.route("/oauth-callback")
def oauth_callback():
    youtube.oauth_callback()
    return flask.redirect("/")


@app.teardown_appcontext
def close_connection(exception):
    db.close_connection(exception)


if __name__ == "__main__":
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run("localhost", 5000, debug=True)
