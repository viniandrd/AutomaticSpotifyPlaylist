import json
from secrets import spotify_user_id, spotify_token, channelID
import requests
import os
import googleapiclient.discovery
import google_auth_oauthlib.flow
import googleapiclient.errors
import youtube_dl

scopes = ["https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtubepartner"]


class CreatePlaylist:
    def __init__(self):
        self.user_id = spotify_user_id
        self.youtube_client = self.get_youtube_client()
        #self.youtube_playlist = self.get_playlist_from_user()
        self.all_song_info = {}

    #Log into Youtube
    def get_youtube_client(self):
        #Copied from Youtube Data API

        #Disable OAuthlibb's HTTPS verification when running locally
        # *DO NOT* leave ths option enabled in production

        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        api_service_name = 'youtube'
        api_version = 'v3'
        client_secrets_file = 'client_secret.json'

        #Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube",
                  "https://www.googleapis.com/auth/youtube.force-ssl",
                  "https://www.googleapis.com/auth/youtube.readonly",
                  "https://www.googleapis.com/auth/youtubepartner"]

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client



    def ask_user_which_playlist(self, info):
        os.system('clear')
        print("------------------ Playlists ------------------")
        print(' - Which playlist do you wanna create a copy in Spotify?')
        for i in range(0, len(info)):
            print('%d - %s' % (i, info[i]['name']))
        print("-----------------------------------------------")
        print()
        opc = int(input('Choose one: '))

        return opc


    def get_playlist_from_user(self):
        request = self.youtube_client.playlists().list(
            part="snippet",
            channelId=channelID
        )
        response = request.execute()

        totalPlaylists = response["pageInfo"]["totalResults"]
        playlists_infos = {}

        for i in range(0, totalPlaylists):
            playlist_name = response["items"][i]["snippet"]["title"]
            playlist_id = response["items"][i]["id"]

            playlists_infos[i] = {
                'name': playlist_name,
                'id': playlist_id,
            }

        opt = self.ask_user_which_playlist(playlists_infos)
        return playlists_infos[opt]['id']




    #Grab our liked videos
    def get_videos(self):

        playlist_id = self.get_playlist_from_user()

        request = self.youtube_client.playlistItems().list(
            part="snippet",
            playlistId=playlist_id
        )
        response = request.execute()

        totalVideos = response["pageInfo"]["totalResults"]

        # collect each video and its information
        for i in range(0, totalVideos):
            video_title = response["items"][i]["snippet"]["title"]
            youtube_url = 'https://www.youtube.com/watch?v={}'.format(response['items'][i]["snippet"]["resourceId"]["videoId"])

            # use youtube_dl to collect the song's info
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video['track']
            artist = video['artist']

            print('-----------------------------------------------------------')
            print('youtube_url : ', youtube_url)
            print('song_name : ', song_name)
            print('artist : ', artist)
            print('-----------------------------------------------------------')

            # save the info
            self.all_song_info[video_title] = {
                'youtube_url': youtube_url,
                'song_name': song_name,
                'artist': artist,


                # add the uri, easy to get song to put into playlist
                'spotify_uri': self.get_spotify_uri(song_name, artist)
            }


    #Create a new playlist
    def create_playlist(self):

        # Playlist's info
        request_body = json.dumps({
            "name": "Musics from YT",
            "description": "Musics that you like",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        # playlist id
        return response_json["id"]


    #Search for the song
    def get_spotify_uri(self, song_name, artist):

        #Search for this song by this artist
        print(song_name, artist)
        print()


        #'https://open.spotify.com/search/roddy%20rich%20the%20box'
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )

        response = requests.get(
            query,
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        #Result of the query
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # Only use the first index, cause its where will be returned the query, URI is the link of the song
        uri = songs[0]["uri"]
        return uri

    #Add this song into spotify playlist
    def add_song_to_playlist(self):
        #Get the info of Youtube Liked Videos
        self.get_videos()

        print('Songs from youtube: ')
        print(self.all_song_info)
        print()
        # collect all of uri
        uris = []
        for song,info in self.all_song_info.items():
            uris.append(info['spotify_uri'])

        # Links of the musics that will be added into spotify playlist
        print('Uris: ')
        print(uris)
        print()

        # Create a new playlist. (In this case i'm using an arealdy created playlist)
        #playlist_id = "0ecqeevxuNleRFGiEDpRBK"
        playlist_id = self.create_playlist()

        # Add the songs in URIS into the playlist
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                'Content-Type': 'application/json',
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()

        return response_json

if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
    os.system('clear')
    print('---------Success-----------')