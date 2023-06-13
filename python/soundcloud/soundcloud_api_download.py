import os
import soundcloud
import wget

client = soundcloud.Client(client_id='YOUR_CLIENT_ID')


def download_track(track):
    try:
        stream_url = client.get(track.stream_url, allow_redirects=False)
        print(f'Downloading: {track.title}')
        wget.download(stream_url.location)
    except:
        print(f"Track {track.title} is not streamable")


def download_playlist(playlist_url):
    playlist = client.get('/resolve', url=playlist_url)
    for track in playlist.tracks:
        download_track(track)


def download_artist_tracks(artist_url):
    artist = client.get('/resolve', url=artist_url)
    tracks = client.get('/users/{0}/tracks'.format(artist.id))
    for track in tracks:
        download_track(track)


def main():
    option = input("Enter 'P' for Playlist or 'A' for Artist: ")
    if option.lower() == 'p':
        playlist_url = input("Enter the Soundcloud playlist URL: ")
        download_playlist(playlist_url)
    elif option.lower() == 'a':
        artist_url = input("Enter the Soundcloud artist URL: ")
        download_artist_tracks(artist_url)
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
