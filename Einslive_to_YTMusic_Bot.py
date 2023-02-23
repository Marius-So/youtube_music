#from ytmusicapi import YTMusic
from bs4 import BeautifulSoup
import pandas as pd
from alive_progress import alive_bar
from YTmusic_handler import *
from time import sleep
import dateutil.parser as dparser

#from concurrent.futures import ThreadPoolExecutor

import re
import urllib
import requests
from requests.exceptions import InvalidURL


def scrape_einslive():
  eins_live_base_url = 'https://www1.wdr.de'
  eins_live_url = '/radio/1live/musik/'

  play_list_links = get_einslive_links(eins_live_url,
                                       base_page=eins_live_base_url)
  play_list_links_filtered = [
    link for link in play_list_links
    if link.startswith('https://www1.wdr.de/radio/1live/musik')
  ]
  return list(play_list_links_filtered)


def parse_url(url):
  try:
    html = requests.get(url).content
  except InvalidURL:
    return []
  bsObj = BeautifulSoup(html, 'lxml')
  links = bsObj.findAll('a')

  # if this gives a result then a playlist is present
  playlist = bsObj.find("div", {"class": "box modTable"})

  return links


def get_einslive_links(url, base_page, depth=2):
  links_to_process = [(base_page + url, 0)]
  processed = set()

  while len(links_to_process) > 0:
    link, level = links_to_process.pop(0)
    print(link, ' - ', level)
    processed.add(link)

    links = parse_url(link)

    for link in links:
      if 'href' not in link.attrs.keys(): continue
      if link.attrs['href'].startswith('http'): continue
      if level + 1 < depth and base_page + link.attrs['href'] not in processed:
        links_to_process.append((base_page + link.attrs['href'], level + 1))
      elif level + 1 == depth and base_page + link.attrs[
          'href'] not in processed:
        processed.add(base_page + link.attrs['href'])
  return processed


def process_playlist_link(link, current_playlist_names):
  data = urllib.request.urlopen(link).read()
  soup = BeautifulSoup(markup=data, features="lxml")
  try:
    name = soup.find('span', attrs={'class': "mediaSerial"}).text
    date = soup.find('span', attrs={'class': "mediaDate"}).text
    # okay this only exists if there is a table...
  except AttributeError:
    return
  try:
    header = soup.find('h1', attrs={
      'class': "articleHeader headline small"
    }).text
  except AttributeError:
    header = ''

  playlist_name = name + ' - ' + date

  # read playlist from html
  playlist_table = soup.find("div", {"class": "box modTable"})
  if playlist_table:
    # here we check again for the name...
    try:
      caption_date = dparser.parse(soup.find("caption"),fuzzy=True,dayfirst=True).strftime("%d.%m.%Y")
      if date != caption_date:
      # only here i know that there is this caption...
        date = caption_date
        playlist_name = name + ' - ' + date
    except ValueError:
      pass

    if playlist_name in current_playlist_names: return

    playlist = pd.read_html(str(playlist_table.contents[1]))[0]
    playlist.dropna(inplace=True)

    service = create_service()
    playlistId = create_playlist(
      service, playlist_name, header + '\n' +
      'THIS is an automatically generated Playlist. GENERATED based on: \n' +
      link)
    print('Sucessfully Created Playlist: ', playlist_name)

    for idx in range(playlist.shape[0]):
      print(idx, ' of ', playlist.shape[0])
      song_name = playlist.iloc[idx][0] + ' ' + playlist.iloc[idx][1]
      response = get_song_id(service, song_name, use_free=True)

      try:
        if response:
          sleep(5)
          add_song_to_playlist(service, playlistId, response[0])

      except HttpError as e:
        print(service, playlistId, response[0])
        print(e)
        with open('playlist_to_delete.txt', 'a') as f:
          f.write(playlistId + '\n')
        return

    return ('https://music.youtube.com/playlist?list=' + playlistId,
            playlist_name)
  else:
    return


def do_daily_bot_update():
  # scrape 1Live
  # need to upate / improve the scraper
  write = True
  if write:
    playlist_links = scrape_einslive()
    with open('playlist_links.txt', 'w') as f:
      for e in playlist_links:
        f.write(e + '\n')
  else:
    playlist_links = []
    with open('playlist_links.txt', 'r') as f:
      for line in f:
        playlist_links.append(line[:-1])

  # connect to YT Music and get current playlists
  service = create_service()
  current_playlist_names = retrieve_playlists_names(
    service, channel_id='UC3zfYmvoC45lsNz01Ow_nrA')

  # remove playlists that threw an error in creation:
  with open('playlist_to_delete.txt', 'r') as f:
    playlist_ids = [e[:-1] for e in f.readlines()]

    for playlist_id in playlist_ids:
      response = remove_playlist(service, playlist_id)

    # clear the ids
    open('playlist_to_delete.txt', 'w')

  # filter for live playlists
  if 'https://www1.wdr.de/radio/1live-diggi/onair/1live-diggi-playlist/index.html' in current_playlist_names:
    current_playlist_names.remove(
      'https://www1.wdr.de/radio/1live-diggi/onair/1live-diggi-playlist/index.html'
    )
  if 'https://www1.wdr.de/radio/1live/musik/playlist/index.html' in current_playlist_names:
    current_playlist_names.remove(
      'https://www1.wdr.de/radio/1live/musik/playlist/index.html')

  # playlists already processed
  link_match = pd.read_csv('1Live_link_match.csv')
  links_processed = link_match['1live_link'].to_list()

  with alive_bar(len(playlist_links)) as bar:
    for idx, link in enumerate(playlist_links):
      bar()

      playlist_info = process_playlist_link(link, current_playlist_names)

      if playlist_info:
        playlist_link, playlist_name = playlist_info
        link_match = pd.read_csv('1Live_link_match.csv')
        add_row = {
          '1live_link': link,
          'playlist_name': playlist_name,
          'yt_music_link': playlist_link
        }
        link_match = link_match.append(add_row, ignore_index=True)
        link_match.to_csv('1Live_link_match.csv', index=False)

      else:
        pass


if __name__ == '__main__':
  do_daily_bot_update()
