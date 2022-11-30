from ytmusicapi import YTMusic
import pandas as pd

from bs4 import BeautifulSoup
import re
import urllib


# TODO: webscraper searching for new playlists on 1Live music -> https://www1.wdr.de/radio/1live/musik/index.html

data = urllib.request.urlopen('https://www1.wdr.de/radio/1live/musik/1live-go/index.html').read()
soup = BeautifulSoup(markup=data, features="lxml")
name = soup.find('span', attrs={'class': "mediaSerial"}).text
date = soup.find('span', attrs={'class': "mediaDate"}).text

playlist_name = name + ' - ' + date
yt = YTMusic('headers_auth.json')
current_playlists = yt.get_library_playlists(None)
playlist_names = [playlist['title'] for playlist in current_playlists]

# read playlist from html
if playlist_name not in playlist_names:
    playlist = pd.read_html("https://www1.wdr.de/radio/1live/musik/1live-go/index.html")[0]
    playlist = playlist.dropna()

    playlistId = yt.create_playlist(playlist_name, 'This is an automatic generated Playlist', 'PUBLIC',)

    for idx in range(playlist.shape[0]):
        print(idx, ' of ', playlist.shape[0])
        songname = playlist.iloc[idx][0] + ' ' +  playlist.iloc[idx][1]
        search_results = yt.search(songname)

        # get videoId
        vidID = None
        for result in search_results:
            if 'videoId' in result:
                vidID = result['videoId']
                break
        if vidID:
            yt.add_playlist_items(playlistId, [vidID])


#yt.add_playlist_items(playlistId, [search_results[0]['videoId']])
