from flask import Flask, redirect, render_template
from app import app
import urllib 
from urllib.parse import quote 
from flask import request

from musixmatch import Musixmatch
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
#  Client Keys
CLIENT_ID = "d79bd6c44fe04825b363c0761898eb79"
CLIENT_SECRET = "24293f3a384a4df692e773ef929e6fff"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1:5000/"
REDIRECT_URI = "http://127.0.0.1:5000/spotify_sentiment_main/"
SCOPE = 'user-read-private user-read-playback-state user-modify-playback-state user-library-read'
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}
'''
 NEW LINES AFTER SEEING VID START
 '''
@app.route('/')
def home():
    return redirect('/spotify_sentiment_landing/')
'''
NEW LINES AFTER SEEING VID END
'''  
#@app.route('/spotify_sentiment_analysis_login')
#def spotify():
  #  return render_template('spotify_authentication.html')

@app.route('/spotify_sentiment_analysis_login')
def spotify_auth():
    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)
 
@app.route('/spotify_sentiment_landing/')
def spotify_sentiment_analysis():
    return render_template('spotify_sentiment_analysis.html')
 
    #EXPERIMENTATION DATA SPOTIFY AUTH
@app.route('/spotify_sentiment_main/')
def spotify_sentiment_analysis_home():
    import requests
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    
    import base64
    import json
    import pandas as pd
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET).encode())
    headers = {"Authorization": "Basic {}".format(base64encoded.decode())}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    authorization_header = {"Authorization":"Bearer {}".format(access_token)}
    
    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)
    
    print(profile_data)

    user_id = profile_data['id']
    username = profile_data['display_name']
    profile_picture = profile_data['images'][0]['url']
    profile_url = profile_data['external_urls']['spotify'] #URL FOR spotify DP
    playlist_api_endpoint = "{}/tracks".format(user_profile_api_endpoint)

    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)

    playlist_data = playlists_response.text
    playlist_data = playlist_data[83:-142]
    playlist_data = json.loads(playlist_data)

    playlist_list = []

    for i in playlist_data:
        tmp = [i['added_at'][:-10], 
            i['track']['name'], 
            i['track']['artists'][0]['name'], 
            i['track']['album']['images'][0]['url'],
            i['track']['external_urls']['spotify'],
            i['track']['id']]
    playlist_list.append(tmp)

    playlist_df = pd.DataFrame(playlist_list, columns=['Date', 'Track_Name', 'Artist', 'Cover_Image', 'URL', 'Track_ID'])
    musixmatch = Musixmatch('4fed4d6c16ffecbe4918a4802a19a3c0')

    analyser = SentimentIntensityAnalyzer()

    sentiment_list = []
    sentiment_score_list = []

    for i in playlist_df[['Track_Name', 'Artist']].values:
        track_name=playlist_df[['Track_Name']].values
        artist=playlist_df[['Artist']].values
        album_art=playlist_df[['Cover_Image']].values
        try:
            song = musixmatch.matcher_lyrics_get(i[1], i[0])
            song = song['message']['body']['lyrics']['lyrics_body']
            sentiment_score = analyser.polarity_scores(song)
            test_lyrics=song
            print(test_lyrics)
            if sentiment_score['compound'] >= 0.05:
                sentiment_percentage = sentiment_score['compound']
                sentiment = 'Positive'
            elif sentiment_score['compound'] > -0.05 and sentiment_score['compound'] < 0.05:
                sentiment_percentage = sentiment_score['compound']
                sentiment = 'Neutral'
            elif sentiment_score['compound'] <= -0.05:
                sentiment_percentage = sentiment_score['compound']
                sentiment = 'Negative'

            sentiment_list.append(sentiment)
            sentiment_score_list.append((abs(sentiment_percentage) * 100))
        
        except:
            sentiment_list.append('None')
            sentiment_score_list.append(0)

    playlist_df['Sentiment'] = sentiment_list
    playlist_df['Sentiment_Score'] = sentiment_score_list
    
    return render_template('landing-page.html',album_art=album_art,test_lyric=test_lyrics, profile_picture=profile_picture,sentiment_list=sentiment_list,track_name=track_name,artist=artist,sentiment_score_list=sentiment_score_list)

   