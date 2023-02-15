import json
# from pprint import pprint
import datetime
import re
import requests

import math
import re
from collections import Counter

import pandas as pd # pip install pandas
from googleapiclient.errors import HttpError

import sys
sys.path.append('/Users/msommerfeld/Desktop/projects/youtube_music/')
from Google import Create_Service

def retrieve_playlists(service, channel_id):
    playlists = []
    try:
        response = service.playlists().list(
            part='contentDetails,snippet,status',
            channelId=channel_id,
            maxResults=50
        ).execute()

        playlists.extend(response.get('items'))
        nextPageToken = response.get('nextPageToken')

        while nextPageToken:
            response = service.playlists().list(
                part='contentDetails,snippet,status',
                channelId=channel_id,
                maxResults=50,
                pageToken=nextPageToken
            ).execute()
            playlists.extend(response.get('items'))
            nextPageToken = response.get('nextPageToken')
        return playlists
    except HttpError as e:
        errMsg = json.loads(e.content)
        print('HTTP Error:')
        print(errMsg['error']['message'])
        return []

def retrieve_playlist_items(service, playlist_id):
    playlist_items = []
    try:
        response = service.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50
        ).execute()

        playlist_items.extend(response['items'])
        nextPageToken = response.get('nextPageToken')

        while nextPageToken:
            response = service.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=nextPageToken
            ).execute()

            playlist_items.extend(response['items'])
            nextPageToken = response.get('nextPageToken')
            print('Token {0}'.format(nextPageToken))
        return playlist_items
    except HttpError as e:
        errMsg = json.loads(e.content)
        print('HTTP Error:')
        print(errMsg['error']['message'])
        return []
    except Exception as e:
        errMsg = json.loads(e.content)
        print('Error:')
        print(errMsg['error']['message'])
        return []

def create_service():
    CLIENT_SECRET_FILE = 'client_secret.json'
    API_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    return Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def retrieve_playlists_names(service, channel_id):
    playlists = retrieve_playlists(service, channel_id)

    if not playlists:
        print('No pliaylist found.')
        return

    playlist_names = [pl['snippet']['title'] for pl in playlists]
    return playlist_names

def create_playlist(service, playlist_name, playlist_desc):
    # gives back id of the created playlist
    request_body = {
        'snippet': {
            'title': playlist_name,
            'description': playlist_desc,
        },
        'status':{
            'privacyStatus': 'public',
        }
    }

    response = service.playlists().insert(
        part=['snippet', 'status'],
        body=request_body
    ).execute()

    return response['id']

def remove_playlist(service, playlist_id):
    response = service.playlists().delete(id=playlist_id).execute()
    return response

def get_song_id(service, song_name, use_free=True):
    # https://yt.lemnoslife.com/noKey/search?part=snippet&q=angels%20Robie%20williams&type=video&videoCategoryId=10&maxResults=1
    if not use_free:
        search_results = service.search().list(q=song_name, part='snippet', type='video', videoCategoryId=10, maxResults=5).execute()
        search_results = search_results['items']
        for result in search_results:
            if 'videoId' in result['id'].keys():
                return result['id']['videoId']
    else:
        pass
        query = {'part': 'snippet',
                    'q': song_name,
                    'type': 'video',
                    'videoCategoryId': '10',
                   'maxResults':'5'}

        api_url = f"https://yt.lemnoslife.com/noKey/search?"
        search_results = requests.get(api_url, query).json()
        search_results = search_results['items']
        for result in search_results:
            if 'videoId' in result['id'].keys():
                # okay this is a hard coded barrier I make it quite relaxed because the cost of not having a song is higher
                if compare_two_strings(song_name, result['snippet']['title']) < 0.5: continue
                return result['id']['videoId'], result['snippet']['title']

def add_song_to_playlist(service, playlistId, videoId):
    request_body = {
        'snippet': {
            'playlistId': playlistId,
            'resourceId': {
                'kind': 'youtube#video',
                'videoId': videoId
            }
        }
    }

    service.playlistItems().insert(
        part='snippet',
        body=request_body
    ).execute()

### helper functions

WORD = re.compile(r"\w+")

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)

def compare_two_strings(s1, s2):
    v1 = text_to_vector(s1.lower())
    v2 = text_to_vector(s2.lower())
    cos_similarity = get_cosine(v1, v2)
    return cos_similarity

if __name__ == "__main__":
    compare_two_strings('poolblood - shabby [OFFICIAL VIDEO]', 'poolblood - shabby')
    pass
