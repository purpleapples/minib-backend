from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
from collections import Counter
app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb://admin:darksm!!e1@13.59.145.218', 27017)
db = client.fav_movie

# api 설계하기

# objectId to str
def objectId_to_str(movie):
    movie['_id'] = str(movie['_id'])
    return movie

# 전체 영화 목록 보여주기
# "/movie/list" - GET
@app.route("/movie/list", methods=['GET'])
def movie_list():
    movie_lst = list(db.movie.find({}))

    # ObjectId는 JSON 자체에서는 지원이 불가능..
    # 따라서 ObjectId를 문자열 형태로 바꿔주는 코드가 필요하다.

    # 1. ObjectId를 문자열로 만들어주는 함수를 정의

    # 2. movie_lst를 comprehension으로 text화
    movie_lst = [objectId_to_str(movie) for movie in movie_lst]

    return jsonify({'results': movie_lst})

# 영화 등록
# "/movie/register" - GET
# parameter : 영화의 _id
@app.route("/movie/register/<oid>", methods=["GET"])
def movie_register(oid):
    # 보고 싶은 영화가 이미 등록이 되어 있으면 새롭게 등록 안한다.
    # 등록이 안되어있으면 새롭게 추가

    # 사용자가 좋아하는 영화의 문서구조
    print("oid", oid)
    fav_movie = db.user_movie.find_one({"fav_movie": oid})

    if not fav_movie:
        db.user_movie.insert_one({"fav_movie": oid})
    # 좋아요 결과 반환
    return jsonify({"result": True})

# 영화 등록 해제
# "/movie/unregister" - GET
@app.route("/movie/unregister/<oid>", methods=["GET"])
def movie_unregister(oid):
    fav_movie = db.user_movie.find_one({"fav_movie": oid})

    if fav_movie:
        db.user_movie.delete_one({"fav_movie": oid})
    # 싫어요 결과 반환
    return jsonify({"result": False})

# 장바구니 영화 리스트 확인
# "/movie/user_favorite"
@app.route("/movie/user-favorite", methods=["GET"])
def movie_user_favorite():
    movie_lst = db.user_movie.find({})
    fav_movie_list = list(movie_lst)
    fav_movie_list = [ObjectId(movie['fav_movie']) for movie in fav_movie_list]

    movie_detail_info = db.movie.find({"_id": {"$in": fav_movie_list}})

    movie_lst = [objectId_to_str(movie) for movie in movie_detail_info]
    top5 = favorite_category()

    return jsonify({'result': {"movie_lst": movie_lst, "top5": top5}})


# 찜하기목록으로 장르, 감독, 배우 순위 counting 해서 5개씩 목록 뽑기
# 작업중
def favorite_category():
    # 저장한 찜목록 load
    fav_movie_list = list(db.user_movie.find({}))
    fav_movie_list = [objectId_to_str(movie) for movie in fav_movie_list]
    id_list = [ObjectId(movie["fav_movie"]) for movie in fav_movie_list]
    # 몽고 db 명령어를 굳이 사용해서 집계 데이터획득하기
    # 조건절 : 찜목록의 아이디를 가진 영화중에서 감독별 카운팅
    director_list = db.movie.aggregate([{"$match": {"_id": {"$in": id_list}}},
        {"$group": {"_id": "$director", "count": {"$sum": 1}, }}
        , {"$limit": 5}, {"$project": {"_id": 1}}, {"$sort": {"count": -1}}
    ])
    top_5_director = [director["_id"] for director in list(director_list)]

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

    return  {"director": top_5_director,
             "actor": top_5_actor,
             "genre": top_5_genre}


# "/movie/detail/id
# naver_code 되돌리기 너무...
@app.route("/movie/detail/<naver_code>", methods=["GET"])
def get_movie_synopsys(naver_code):
    movie = db.movie.find_one({"naver_code": {"$eq": naver_code}})
    synopsys = db.synopsys.find_one({"naver_code": {"$eq": naver_code}}, {"_id": 0})
    movie = objectId_to_str(movie)

    # 좋아요 조회
    like = db.user_movie.find_one({"fav_movie": {"$eq": str(movie['_id'])}})
    print(like)
    print(str(movie['_id']))
    if like == None:
        like = False
    else:
        like = True
    movie['like'] = like

    movie['synopsys'] = synopsys['synopsys']

    movie = objectId_to_str(movie)
    return jsonify({'result': movie})


if __name__ == '__main__':
    print("run server.......")
    app.run("0.0.0.0", 5000, debug=True)
