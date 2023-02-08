from ytmusicapi import YTMusic
from bs4 import BeautifulSoup
import pandas as pd
from alive_progress import alive_bar

import re
import urllib
import requests
from requests.exceptions import InvalidURL

def scrape_einslive():
    eins_live_base_url = 'https://www1.wdr.de'
    eins_live_url = '/radio/1live/musik/'

    play_list_links = get_einslive_links(eins_live_url, base_page=eins_live_base_url)
    play_list_links_filtered = [link for link in play_list_links if link.startswith('https://www1.wdr.de/radio/1live/musik')]
    return list(play_list_links_filtered)

def get_einslive_links(url, base_page, depth=2):
    links_to_process = [(base_page + url, 0)]
    processed = set()

    while len(links_to_process) > 0:
        link, level = links_to_process.pop(0)
        print(link, ' - ', level)
        processed.add(link)

        try:
            html = requests.get(link).content
        except InvalidURL:
            continue
        bsObj = BeautifulSoup(html, 'lxml')

        links = bsObj.findAll('a')
        finalLinks = set()
        for link in links:
            if 'href' not in link.attrs.keys(): continue
            if link.attrs['href'].startswith('http'): continue

            if level + 1 < depth and base_page + link.attrs['href'] not in processed:
                links_to_process.append((base_page + link.attrs['href'], level + 1))
            elif level + 1 == depth and link not in processed:
                processed.add(base_page + link.attrs['href'])
    return processed

def process_playlist_link(yt, link, current_playlist_names):

    data = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(markup=data, features="lxml")
    name = soup.find('span', attrs={'class': "mediaSerial"}).text
    date = soup.find('span', attrs={'class': "mediaDate"}).text

    header = soup.find('h1', attrs={'class': "articleHeader headline small"}).text

    playlist_name = name + ' - ' + date
    # read playlist from html
    if playlist_name not in current_playlist_names:
        playlist_table = soup.find("div", {"class": "box modTable"})
        if playlist_table:
            playlist = pd.read_html(str(playlist_table.contents[1]))[0]
            playlist.dropna(inplace=True)
            playlistId = yt.create_playlist(playlist_name, header + '\n' + 'THIS is an automatically generated Playlist. GENERATED based on: \n' + link, 'PUBLIC',)

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
            print('Sucessfully Created Playlist: ', playlist_name)
            print('Playlist link: ', 'https://music.youtube.com/playlist?list=' + playlistId)
            return ('https://music.youtube.com/playlist?list=' + playlistId, playlist_name)
        else:
            return (False, False)


if __name__ == "__main__":
    # the user is set via x-authuser....

    # Should automate the receiving of the cookie credentials on new login...

    # scrape 1Live
    playlist_links = scrape_einslive()

    # connect to YT Music and get current playlists
    yt = YTMusic('headers_auth.json')
    # need to find out for whihc account the auth is...
    current_playlists = yt.get_library_playlists(None)
    current_playlist_names = [playlist['title'] for playlist in current_playlists]

    if 'https://www1.wdr.de/radio/1live-diggi/onair/1live-diggi-playlist/index.html' in current_playlist_names:
        current_playlist_names.remove('https://www1.wdr.de/radio/1live-diggi/onair/1live-diggi-playlist/index.html')
    if 'https://www1.wdr.de/radio/1live/musik/playlist/index.html' in current_playlist_names:
        current_playlist_names.remove('https://www1.wdr.de/radio/1live/musik/playlist/index.html')

    with alive_bar(len(playlist_links)) as bar:
        for idx, link in enumerate(playlist_links):
            bar()

            playlist_link, playlist_name = process_playlist_link(yt, link, current_playlist_names)
            if playlist_link:
                link_match = pd.read_csv('1Live_link_match.csv')
                add_row = {'1live_link':link,
                 'playlist_name': playlist_name,
                 'yt_music_link': playlist_link}
                link_match = link_match.append(add_row, ignore_index=True)
                link_match.to_csv('1Live_link_match.csv', index=False)

# email: 1.live.playlist.bot@gmail.com
# pw -> same as marius96meyer
