import boto3
from flask import Flask, request, redirect
from Config import *

s3 = boto3.client('s3')
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400

    file = request.files['file']

    if file.filename == '':
        return "파일을 선택하지 않았습니다.", 400

    try:
        s3.upload_fileobj(
            file,                  # 업로드할 파일 객체
            BUCKET_NAME,        # 버킷 이름
            file.filename,         # S3에 저장될 파일 이름
            ExtraArgs={
                'ContentType': file.content_type  # 파일 타입 지정 (예: 'image/jpeg')
            }
        )
        return f"'{file.filename}' 파일 업로드 성공!", 200

    except Exception as e:
        print(e)
        return "업로드 중 오류가 발생했습니다.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)