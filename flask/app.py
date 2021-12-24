from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import json
import boto3


application = Flask(__name__)

# ======Flask 에 필요한 설정 정보 config.json 에서 가져오기======
with open('config.json', 'r') as f:
    config = json.load(f)
bucket_info = config['BUCKET']
storage_info = config['STORAGE']
db_info = config['DB']
before_date = config['BEFORE_DATE']


@application.route("/")
def home():
    """
    화면에 접속
    """
    return render_template("index.html")


@application.route("/privacy")
def privacy():
    return render_template("privacy.html")    


@application.route("/api/audios")
def get_audios():
    """
    audio 파일 보내기
    """
    result = {}
   
    # ======before_date일 전 날짜 형태로 폴더명 만들기=======
    target_date = cal_datetime_kst(before_date)
    
    target_date_str = target_date['date_st'].strftime("%Y-%m-%d")
    folder = target_date_str
    print(f'audio folder: {folder}')
    print(get_storage_filelist(bucket_info, folder))


    result['audio_list'] = get_storage_filelist(bucket_info, folder)

    return jsonify(result)


@application.route("/api/news")
def send_news():
    """
    지금으로부터 before_date 만큼 전 일자 뉴스 데이터 가져오기
    """

    # TODO : 특정 일자 데이터 조회하기
    client = MongoClient(host=db_info['my_ip'], port=27017,
                         username=db_info['username'], password=db_info['password'])
    db = client[db_info['db_name']]
    collection = db[db_info['collection_name']]

    # ======before_date 일 전 데이터 조회하기=======
    target_date = cal_datetime_utc(before_date)

    news_items = list(collection.find(
        {'date': {'$gte': target_date['date_st'], '$lte': target_date['date_end']}}, {'_id': False}).sort('date', 1))

    return jsonify({"news": news_items})


def get_storage_filelist(bucket_info, folder):
    """
    내 bucket 에서 특정 폴더에 있는 파일 목록을 반환
    :param bucket_info: bucket 정보
    :param folder: bucket안 특정 폴더명
    :return: 특정 폴더에 있는 파일 url 목록
    :rtype: list of dictionaries
    """

    service_name = 's3'
    endpoint_url = 'https://kr.object.ncloudstorage.com/'

    bucket_url = endpoint_url + bucket_info['bucket_name'] + '/'

    s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=storage_info['access_key'],
                      aws_secret_access_key=storage_info['secret_key'])

    result = []
    objects = s3.list_objects_v2(
        Bucket=bucket_info['bucket_name'], Prefix=folder)

    entries = objects.get('Contents') or []

    for entry in entries:
        if entry['Size'] != 0:
            result.append({'source': bucket_url + entry['Key']})

    return result

def cal_datetime_utc(before_date, timezone='Asia/Seoul'):
    '''
    현재 일자에서 before_date 만큼 이전의 일자를 UTC 시간으로 변환하여 반환
    :param before_date: 이전일자
    :param timezone: 타임존
    :rtype: dict of datetime object
    '''
    today = pytz.timezone(timezone).localize(datetime.now())
    target_date = today - timedelta(days=before_date)

    # 같은 일자 same date 의 00:00:00 로 변경 후, UTC 시간으로 바꿈
    start = target_date.replace(hour=0, minute=0, second=0,
                                microsecond=0).astimezone(pytz.UTC)

    # 같은 일자 same date 의 23:59:59 로 변경 후, UTC 시간으로 바꿈
    end = target_date.replace(
        hour=23, minute=59, second=59, microsecond=999999).astimezone(pytz.UTC)

    return {'date_st': start, 'date_end': end}


def cal_datetime_kst(before_date, timezone='Asia/Seoul'):
    '''
    현재 일자에서 before_date 만큼 이전의 일자의 시작시간,끝시간 반환
    :param before_date: 이전일자
    :param timezone: 타임존
    :rtype: dict of datetime object
    '''
    today = pytz.timezone(timezone).localize(datetime.now())
    target_date = today - timedelta(days=before_date)

    # 같은 일자 same date 의 00:00:00 로 변경
    start = target_date.replace(hour=0, minute=0, second=0,
                                microsecond=0)

    # 같은 일자 same date 의 23:59:59 로 변경
    end = target_date.replace(
        hour=23, minute=59, second=59, microsecond=999999)

    return {'date_st': start, 'date_end': end}

if __name__ == '__main__':
    application.run('0.0.0.0', debug=True)