from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
from collections import Counter

app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb://localhost', 27017)
db = client.fav_movie


# objectId to str
def objectId_to_str(movie):
    movie['_id'] = str(movie['_id'])
    return movie


def favorite_category():
    # 저장한 찜목록 load
    fav_movie_list = list(db.user_movie.find({} ))
    fav_movie_list = [objectId_to_str(movie) for movie in fav_movie_list]
    id_list = [ObjectId(movie["fav_movie"]) for movie in fav_movie_list]
    # 몽고 db 명령어를 굳이 사용해서 집계 데이터획득하기
    # 조건절 : 찜목록의 아이디를 가진 영화중에서 감독별 카운팅
    director_list = db.movie.aggregate([{"$match": {"_id": {"$in": id_list}}},
        {"$group": {"_id": "$director", "count": {"$sum": 1}, }}
        , {"$limit": 5}
    ])
    top_5_director = list(director_list)

    # 최애 배우, genre 조회
    actor_genre_list = db.movie.find({"_id": {"$in": id_list}}, {"actors": 1, "genre": 1})
    actor_total_list = []
    genre_total_list = []
    for actors in list(actor_genre_list):
        actor_total_list += actors['actors']
        genre_total_list += actors['genre'].split(',')
    # 조회 한걸로 뽑기
    top_5_actor = [actor[0] for actor in Counter(actor_total_list).most_common(5)]
    top_5_genre = [genre[0] for genre in Counter(genre_total_list).most_common(5)]

    return  {"top_5_director": top_5_director,
             "top_5_actor": top_5_actor,
             "top_5_genre": top_5_genre}



if __name__ == '__main__':
    result = favorite_category()
