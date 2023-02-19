import requests
import json

def create_playlist(playlist_name, spotify_user_id, spotify_token):
	"""Create A New Playlist"""
	request_body = json.dumps(
		{
			"name": playlist_name,
			"description": "Songs",
			"public": True,
		}
	)

	query = "https://api.spotify.com/v1/users/{}/playlists".format(
		spotify_user_id)
	response = requests.post(
		query,
		data=request_body,
		headers={
			"Content-Type": "application/json",
			"Authorization": "Bearer {}".format(spotify_token),
		},
	)

	return response.json()

def get_spotify_uri(track, artist):
    """Search For the Song"""

    query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track".format(
        track,
        artist
    )
    response = requests.get(
        query,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format("spotify_token")
        }
    )
    songs = response["tracks"]["items"]

    url = songs[0]["uri"]

    return url

def add_song(playlist_id, urls):
    """Add all songs into the new Spotify playlist"""

    request_data = json.dumps(urls)

    query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
        playlist_id)

    response = requests.post(
        query,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format("spotify_token")
        }
    )

    return response

if __name__=='__main__':
	spotify_user_id = "31uwabxif5ogkvkuy74iq3ttewsq"
	spotify_token = "BQB40N7ceR3GI0xmGZy0fXGZR17i6LQUUv6teN8aaLN6pLfmad8ym3roniXtlZPhBf5vJPCZw7oiXXhgkwVTCEroU9sSzoRxxrTs_eb_lfLK1ABca31N1MsrssGNn1NzaJ7-wXcx-wT1yZfdSiau2w6Ud6LG4MgdrxB4LJyxLndKgy0frOcmV8vODYgH9rCYZ7KceLxk4tvfa1UEeA10xLMnI48WLEP4Y8GC4QEi3O_v-DySyoeNwYak7G2wFj85IgCQCbcjN7UG3FgGRg1s2YEZBLbAmejioROJ"
	my_response = create_playlist('test_creation', spotify_user_id, spotify_token)
	print('here')
	# my_response.status_code == 201
    playlist_external_url = my_response.json()['external_urls']['spotify']
	playlist_link = my_response["external_urls"]
