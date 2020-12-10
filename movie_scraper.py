import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
# aws-ec2
client = MongoClient('mongodb://admin:darksm!!e1@13.59.145.218', 27017)

# local
#client = MongoClient('mongodb://localhost', 27017)
db = client.fav_movie

def scrapping_poster(naver_code):
    URL = "https://movie.naver.com/movie/bi/mi/photoViewPopup.nhn?movieCode="+naver_code
    headers = {
        'User-Agent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    data = requests.get(URL, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    poster = soup.select_one("#targetImage").get("src")
    return poster

def scraping_synopsys(naver_code):
    URL = "https://movie.naver.com/movie/bi/mi/basic.nhn?code=" +naver_code

    headers = {
        'User-Agent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    data = requests.get(URL, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    synopsys = soup.select_one("#content > div.article > div.section_group.section_group_frst > div:nth-child(1) > div > div.story_area").text
    synopsys = re.sub("줄거리", "", synopsys)
    synopsys = re.sub("제작노트 보기", "", synopsys)
    synopsys = re.sub("[!?.]{1,}", "(\g<0>)\n", synopsys)
    doc = {
        "naver_code": naver_code,
        "synopsys": synopsys
    }
    db.synopsys.insert_one(doc)


def scrap_naver_movie():
    URL = "https://movie.naver.com/movie/running/current.nhn"
    headers = {
        'User-Agent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    # URL 과 연결 확인
    data = requests.get(URL, headers=headers)
    # BeautifulSoup 적용시키기
    soup = BeautifulSoup(data.text, 'html.parser')
    movie_lst = soup.select("#content > div.article > div:nth-child(1) > div.lst_wrap > ul > li")

    for movie in movie_lst:
        naver_code = movie.select_one("li > div.thumb > a").get("href").split("=")[1]
        title = movie.select_one("dl > dt > a").text
        thumbnail  = movie.select_one("div > a > img").get("src")
        star = movie.select_one("dl > dd.star > dl.info_star > dd > div > a > span.num").text
        director = movie.select_one("dl > dd:nth-child(3) > dl > dd:nth-child(4) > span > a").text
        act = movie.select("dl > dd:nth-child(3) > dl > dd:nth-child(6) > span > a")
        time_and_release = movie.select_one("dl > dd:nth-child(3) > dl > dd:nth-child(2)")
        actors = [actor.text for actor in act]
        movieContext = re.sub('\s', '', time_and_release.text)
        movieContext = movieContext.split('|')
        if len(movieContext) < 3:
            continue
        genre = movieContext[0]
        runningtime =movieContext[1]
        releaseDt = movieContext[2]
        poster = scrapping_poster(naver_code)
        doc = {
            "naver_code": naver_code,
            "title": title,
            "thumbnail": thumbnail,
            "poster": poster,
            "star": star,
            "director": director,
            "actors": actors,
            "genre": genre,
            "runningtime": runningtime,
            "releaseDt": releaseDt
        }
        db.movie.insert_one(doc)
        scraping_synopsys(naver_code)

# db 확인
if __name__ == '__main__':
    scrap_naver_movie()