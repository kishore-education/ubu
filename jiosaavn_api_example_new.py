def is_song_uploaded(song_id):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, 'songs_metadata.csv')
    if not os.path.isfile(csv_file):
        return False
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        for line in csvfile:
            if line.strip().startswith('song_id'):
                continue
            if f',{song_id},' in line or line.strip().endswith(f',{song_id}'):
                return True
    return False
import csv
import uuid
import os
import requests
import telegram
import asyncio

import mimetypes

def send_test_message():
    try:
        async def send():
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Test message: Upload is working!")
        asyncio.run(send())
    except Exception as e:
        print(f"Failed to send test message: {e}")

# API configuration
BASE_URL = "http://64.227.132.105:3000"

TELEGRAM_BOT_TOKEN = '7311171550:AAGXZ6fQWsPO30_FRZl3MCgXssvRaYFgiQM'
TELEGRAM_CHAT_ID = '5408718071'

def search_songs(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/songs"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_albums(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/albums"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_artists(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/artists"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_playlists(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/playlists"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def get_song_by_id(song_id):
    url = f"{BASE_URL}/api/songs/{song_id}"
    response = requests.get(url)
    return response.json()

def send_song_to_telegram(song_url, song_name, quality_label=None, image_url=None):
    # Modified: Accepts quality_label and image_url, returns file_ids
    async def send(quality_label=None, image_url=None):
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        image_file_id = image_file_unique_id = None
        temp_image_filename = None
        temp_filename = None
        try:
            # Handle image
            if image_url:
                try:
                    temp_image_filename = f"temp_{song_name}.jpg"
                    img_resp = requests.get(image_url, stream=True)
                    if img_resp.status_code == 200:
                        with open(temp_image_filename, 'wb') as img_file:
                            for chunk in img_resp.iter_content(chunk_size=8192):
                                if chunk:
                                    img_file.write(chunk)
                        with open(temp_image_filename, 'rb') as img_file:
                            msg = await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=img_file, caption=f"{song_name} cover art")
                            if msg and msg.photo:
                                photo_info = msg.photo[-1]
                                image_file_id = photo_info.file_id
                                image_file_unique_id = photo_info.file_unique_id
                                print(f"Image for '{song_name}' sent to Telegram chat.")
                except Exception as e:
                    print(f"Failed to send image for '{song_name}': {e}")
                finally:
                    if temp_image_filename and os.path.exists(temp_image_filename):
                        try:
                            os.remove(temp_image_filename)
                        except Exception:
                            pass

            # Download the song file
            temp_filename = f"temp_{song_name}_{quality_label or 'audio'}.mp3"
            file_response = requests.get(song_url, stream=True)
            with open(temp_filename, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Send the file to Telegram
            audio_file_id = audio_file_unique_id = None
            with open(temp_filename, 'rb') as audio_file:
                msg = await bot.send_audio(chat_id=TELEGRAM_CHAT_ID, audio=audio_file, title=song_name)
                if msg and msg.audio:
                    audio_file_id = msg.audio.file_id
                    audio_file_unique_id = msg.audio.file_unique_id
                    print(f"Audio '{song_name}' ({quality_label}) sent to Telegram chat.")
            return audio_file_id, audio_file_unique_id, image_file_id, image_file_unique_id
        except Exception as e:
            print(f"Failed to send audio or image for '{song_name}': {e}")
            return None, None, None, None
        finally:
            # Always try to remove temp files
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass
            if temp_image_filename and os.path.exists(temp_image_filename):
                try:
                    os.remove(temp_image_filename)
                except Exception:
                    pass
    try:
        return asyncio.run(send(quality_label=quality_label, image_url=image_url))
    except Exception as e:
        print(f"Failed to send audio or image for '{song_name}': {e}")
        return None, None, None, None

def get_album_by_id(album_id):
    url = f"{BASE_URL}/api/albums?id={album_id}"
    response = requests.get(url)
    return response.json()

def get_artist_by_id(artist_id):
    url = f"{BASE_URL}/api/artists/{artist_id}"
    response = requests.get(url)
    return response.json()

def get_playlist_by_id(playlist_id):
    url = f"{BASE_URL}/api/playlists?id={playlist_id}"
    response = requests.get(url)
    return response.json()



# Function to search and upload all Tamil songs, saving metadata to CSV
def upload_all_tamil_songs():
    print("Searching and uploading all Tamil songs by year and month...")
    fieldnames = [
        'song_id', 'song_name', 'quality', 'audio_file_id', 'audio_file_unique_id',
        'image_file_id', 'image_file_unique_id', 'album', 'artist', 'release_date', 'duration', 'download_url', 'image_url'
    ]
    csv_file = 'songs_metadata.csv'
    csv_exists = os.path.isfile(csv_file)
    if not csv_exists:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    limit = 10
    for year in range(1990, 2026):
        for month in range(1, 13):
            page = 0
            while True:
                # Try to search with year and month in the query
                query = f"tamil {year}-{month:02d}"
                songs = search_songs(query, page=page, limit=limit)
                if not (songs and songs.get('data') and songs['data'].get('results')):
                    break
                results = songs['data']['results']
                if not results:
                    break
                for song in results:
                    song_id = song.get('id')
                    song_name = song.get('title') or song.get('name') or ''
                    if not song_id or not song_name:
                        continue
                    if is_song_uploaded(song_id):
                        print(f"Song '{song_name}' already uploaded. Skipping.")
                        continue
                    details = get_song_by_id(song_id)
                    if not (details and details.get('data') and len(details['data']) > 0):
                        print(f"Could not fetch details for song '{song_name}'. Skipping.")
                        continue
                    data = details['data'][0]
                    download_url = data.get('downloadUrl')
                    # Get image url (prefer 500x500)
                    img_field = data.get('image') or data.get('imageUrl')
                    image_url = None
                    if isinstance(img_field, list):
                        best_img = None
                        for img in img_field:
                            if isinstance(img, dict) and img.get('quality') == '500x500':
                                best_img = img.get('url')
                                break
                        if not best_img and img_field:
                            best_img = img_field[-1].get('url') if isinstance(img_field[-1], dict) else None
                        image_url = best_img
                    elif isinstance(img_field, str):
                        image_url = img_field

                    for quality in ['160kbps', '320kbps']:
                        quality_url = None
                        if isinstance(download_url, dict):
                            quality_url = download_url.get(quality)
                        elif isinstance(download_url, list):
                            for item in download_url:
                                if isinstance(item, dict) and (item.get('quality') == quality):
                                    quality_url = item.get('url')
                                    break
                        elif isinstance(download_url, str):
                            quality_url = None
                        if not quality_url:
                            print(f"No {quality} download URL found for the song '{song_name}'. Skipping {quality}.")
                            continue
                        # Send to Telegram
                        audio_file_id = audio_file_unique_id = image_file_id = image_file_unique_id = None
                        audio_file_id, audio_file_unique_id, image_file_id, image_file_unique_id = send_song_to_telegram(
                            quality_url, song_name, quality_label=quality, image_url=image_url if quality == '160kbps' else None
                        )
                        if audio_file_id:
                            row_data = {
                                'song_id': song_id,
                                'song_name': song_name,
                                'quality': quality,
                                'audio_file_id': audio_file_id,
                                'audio_file_unique_id': audio_file_unique_id,
                                'image_file_id': image_file_id if quality == '160kbps' else '',
                                'image_file_unique_id': image_file_unique_id if quality == '160kbps' else '',
                                'album': data.get('album', ''),
                                'artist': data.get('primaryArtists', ''),
                                'release_date': data.get('releaseDate', ''),
                                'duration': int(data.get('duration')) if data.get('duration') else '',
                                'download_url': quality_url,
                                'image_url': image_url if quality == '160kbps' else ''
                            }
                            with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow(row_data)
                            print(f"Uploaded and saved metadata for '{song_name}' ({quality})!")
                        else:
                            print(f"Failed to upload '{song_name}' ({quality}) to Telegram.")
                page += 1
    print("All Tamil songs processed by year and month.")

if __name__ == "__main__":
    print("JioSaavn API Python Example")
    send_test_message()
    upload_all_tamil_songs()
