import boto3
from flask import Flask, request, redirect

s3 = boto3.client('s3')
# 설정
S3_BUCKET_NAME = 'ttack-dae'

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
            S3_BUCKET_NAME,        # 버킷 이름
            file.filename,         # S3에 저장될 파일 이름
            ExtraArgs={
                'ContentType': file.content_type  # 파일 타입 지정 (예: 'image/jpeg')
            }
        )
        return f"'{file.filename}' 파일 업로드 성공!", 200

    except Exception as e:
        print(e)
        return "업로드 중 오류가 발생했습니다.", 500

@app.route('/', methods=['GET'])
def send_file():
    try:
        # Presigned URL 생성
        # URL은 3600초(1시간) 동안 유효합니다.
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': 'img.png'},
            ExpiresIn=3600
        )

        # 생성된 URL로 사용자 브라우저를 리디렉션
        return redirect(url)

    except Exception as e:
        # 파일이 존재하지 않거나 다른 S3 오류 처리
        if e.response['Error']['Code'] == 'NoSuchKey':
            return "파일을 찾을 수 없습니다.", 404
        else:
            print(e)
            return "다운로드 중 오류가 발생했습니다.", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)