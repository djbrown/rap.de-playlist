import secrets

import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

PLAYLIST_ID = secrets.PLAYLIST_ID


def _api():
    credentials = google.oauth2.credentials.Credentials(**flask.session["credentials"])
    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials
    )


def get_all_playlist_items(items=[], pageToken=None, api=_api):
    y = api()
    if pageToken is None:
        request = y.playlistItems().list(
            part="snippet", playlistId=PLAYLIST_ID, maxResults=50
        )
    else:
        request = y.playlistItems().list(
            part="snippet", playlistId=PLAYLIST_ID, maxResults=50, pageToken=pageToken
        )

    response = request.execute()

    new_items = items + response.get("items")
    nextPageToken = response.get("nextPageToken")

    if nextPageToken is None:
        return new_items
    else:
        return get_all_playlist_items(
            items=new_items, pageToken=nextPageToken, api=api()
        )


def add_video_to_playlist(video_id, playlist_id=PLAYLIST_ID, api=_api):
    y = api()
    y.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": 0,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


def delete_playlist_item(playlist_item_id, api=_api):
    request = api().playlistItems().delete(id=playlist_item_id)
    response = request.execute()
    return response


# AUTH


def authorize():

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )

    flow.redirect_uri = flask.url_for("oauth_callback", _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )

    # Store the state so the callback can verify the auth server response.
    flask.session["state"] = state

    return authorization_url


def oauth_callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session["state"]

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = flask.url_for("oauth_callback", _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session["credentials"] = _credentials_to_dict(credentials)


def _credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
