import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict
import os
from collections import defaultdict
from sklearn.metrics import euclidean_distances
from scipy.spatial.distance import cdist
import difflib
from fastapi import FastAPI,Request,File, Form, UploadFile
import uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd, numpy as np
import ast
import pickle
import itertools
with open("model.pkl", "rb") as f:
    song_cluster_pipeline = pickle.load(f)
app = FastAPI()
spotify_data = pd.read_csv("data.csv")
load_dotenv()

# class Item(BaseModel):
#     song_list, spotify_data, n_songs=5
#     song_list: list
#     description: Union[str, None] = None
#     price: float
#     tax: Union[float, None] = None

@app.get("/")
def read_root():
    return {"Message": "Yaay! I'm running successfully"}


# SPOTIPY_CLIENT_ID = os.environ.get('client_id')
# client_secret = os.environ.get('client_secret')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id='17c2183917474c9ca53085e93a30bb83',client_secret='fe0691cee0314448b731ffe483481bf5'))
print('Auth success')

def find_song(name, year):
    song_data = defaultdict()
    results = sp.search(q= 'track: {} year: {}'.format(name,year), limit=1)
    if results['tracks']['items'] == []:
        return None

    results = results['tracks']['items'][0]
    track_id = results['id']
    audio_features = sp.audio_features(track_id)[0]

    song_data['name'] = [name]
    song_data['year'] = [year]
    song_data['explicit'] = [int(results['explicit'])]
    song_data['duration_ms'] = [results['duration_ms']]
    song_data['popularity'] = [results['popularity']]

    for key, value in audio_features.items():
        song_data[key] = value

    return pd.DataFrame(song_data)
    
number_cols = ['valence', 'year', 'acousticness', 'danceability', 'duration_ms', 'energy', 'explicit',
 'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'popularity', 'speechiness', 'tempo']


def get_song_data(song, spotify_data):
    
    try:
        song_data = spotify_data[(spotify_data['name'] == song['name']) 
                                & (spotify_data['year'] == song['year'])].iloc[0]
        return song_data
    
    except IndexError:
        return find_song(song['name'], song['year'])
        

def get_mean_vector(song_list, spotify_data):
    
    song_vectors = []
    
    for song in song_list:
        song_data = get_song_data(song, spotify_data)
        if song_data is None:
            print('Warning: {} does not exist in Spotify or in database'.format(song['name']))
            continue
        song_vector = song_data[number_cols].values
        song_vectors.append(song_vector)  
    
    song_matrix = np.array(list(song_vectors))
    return np.mean(song_matrix, axis=0)


def flatten_dict_list(dict_list):
    
    flattened_dict = defaultdict()
    for key in dict_list[0].keys():
        flattened_dict[key] = []
    
    for dictionary in dict_list:
        for key, value in dictionary.items():
            flattened_dict[key].append(value)
            
    return flattened_dict

def return_df(csv):
    return pd.DataFrame(csv)

@app.post("/recommend_songs/")
async def recommend_songs(request: Request,song_list: list = Form(...),n_songs: int = Form(...)):
    metadata_cols = ['name', 'year', 'artists']
    #print(song_list,type(song_list))
    # if len(song_list)>1:
    #     song_list = [item for songs in song_list for item in songs]
    # song_list = list(itertools.chain(*song_list))
    song_list = [ast.literal_eval(song) for song in song_list]
    print(song_list,type(song_list))
    song_dict = flatten_dict_list(song_list)
    song_center = get_mean_vector(song_list, spotify_data)
    scaler = song_cluster_pipeline.steps[0][1]
    scaled_data = scaler.transform(spotify_data[number_cols])
    scaled_song_center = scaler.transform(song_center.reshape(1, -1))
    distances = cdist(scaled_song_center, scaled_data, 'cosine')
    index = list(np.argsort(distances)[:, :n_songs][0])
    
    rec_songs = spotify_data.iloc[index]
    rec_songs = rec_songs[~rec_songs['name'].isin(song_dict['name'])]
    return rec_songs[metadata_cols].to_dict(orient='records')




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000,debug=True)