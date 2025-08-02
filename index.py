import os
from flask import Flask, request, redirect
from flask_restx import Api, Resource, Namespace, reqparse, fields
from werkzeug.datastructures import FileStorage
import boto3

# 예시를 위해 Config 값을 여기에 정의합니다.
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 중요: 실제 AWS S3 버킷 이름으로 변경해야 합니다.
BUCKET_NAME = 'your-s3-bucket-name'

app = Flask(__name__)
api = Api(app, version='1.0', title='File Upload API',
          description='사용자, 그룹, 인증 파일 업로드를 위한 API',
          doc='/api-docs/')
s3 = boto3.client('s3', region_name='ap-northeast-2')

upload_ns = Namespace('uploads', description='파일 업로드 관련 API')
download_ns = Namespace('downloads', description='파일 다운로드 관련 API')
api.add_namespace(upload_ns)
api.add_namespace(download_ns)


# --- Helper 함수 ---
def allowed_file(filename):
    """파일 확장자 검사 함수"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file_on_s3(file, filename):
    """S3에 파일을 업로드하는 함수"""
    s3.upload_fileobj(
        file,
        BUCKET_NAME,
        filename,
        ExtraArgs={
            'ContentType': file.content_type
        }
    )

file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument('image', location='files', type=FileStorage, required=True, help='업로드할 이미지 파일')

user_profile_parser = file_upload_parser.copy()
user_profile_parser.add_argument('userId', type=str, required=True, help='사용자 고유 ID', location='form')
user_profile_parser.add_argument('userSns', type=str, required=True, help='사용자 SNS 종류', location='form')

group_profile_parser = file_upload_parser.copy()
group_profile_parser.add_argument('groupId', type=str, required=True, help='그룹 고유 ID', location='form')

punish_feed_parser = file_upload_parser.copy()
punish_feed_parser.add_argument('userId', type=str, required=True, help='사용자 고유 ID', location='form')
punish_feed_parser.add_argument('userSns', type=str, required=True, help='사용자 SNS 종류', location='form')
punish_feed_parser.add_argument('groupId', type=str, required=True, help='그룹 고유 ID', location='form')
punish_feed_parser.add_argument('punishId', type=str, required=True, help='인증(벌칙) 고유 ID', location='form')

@upload_ns.route('/user-profile')
class UploadUserProfile(Resource):
    @upload_ns.expect(user_profile_parser)
    @upload_ns.response(201, '성공적으로 업로드되었습니다.')
    @upload_ns.response(400, '잘못된 요청입니다.')
    @upload_ns.response(500, '서버 오류가 발생했습니다.')
    def post(self):
        """사용자 프로필 이미지를 업로드합니다."""
        args = user_profile_parser.parse_args()
        user_id = args['userId']
        user_sns = args['userSns']
        image_file = args['image']

        if not image_file or not allowed_file(image_file.filename):
            return {'message': '파일이 잘못되었습니다.'}, 400

        filename = f"{user_id}_{user_sns}_userProfile"
        try:
            upload_file_on_s3(image_file, filename)
        except Exception as e:
            return {'message': f'업로드 중 오류가 발생했습니다: {str(e)}'}, 500

        return {'message': '성공적으로 업로드되었습니다.', 'filename': filename}, 201


@upload_ns.route('/group-profile')
class UploadGroupProfile(Resource):
    @upload_ns.expect(group_profile_parser)
    @upload_ns.response(201, '성공적으로 업로드되었습니다.')
    @upload_ns.response(400, '잘못된 요청입니다.')
    @upload_ns.response(500, '서버 오류가 발생했습니다.')
    def post(self):
        """그룹 프로필 이미지를 업로드합니다."""
        args = group_profile_parser.parse_args()
        gid = args['groupId']
        image_file = args['image']

        if not image_file or not allowed_file(image_file.filename):
            return {'message': '파일이 잘못되었습니다.'}, 400

        filename = f"{gid}_groupProfile"
        try:
            upload_file_on_s3(image_file, filename)
        except Exception as e:
            return {'message': f'업로드 중 오류가 발생했습니다: {str(e)}'}, 500

        return {'message': '성공적으로 업로드되었습니다.', 'filename': filename}, 201


@upload_ns.route('/punish-feed')
class UploadPunishFeed(Resource):
    @upload_ns.expect(punish_feed_parser)
    @upload_ns.response(201, '성공적으로 업로드되었습니다.')
    @upload_ns.response(400, '잘못된 요청입니다.')
    @upload_ns.response(500, '서버 오류가 발생했습니다.')
    def post(self):
        """인증(벌칙) 피드 이미지를 업로드합니다."""
        args = punish_feed_parser.parse_args()
        user_id = args['userId']
        user_sns = args['userSns']
        gid = args['groupId']
        punish_id = args['punishId']
        image_file = args['image']

        if not image_file or not allowed_file(image_file.filename):
            return {'message': '파일이 잘못되었습니다.'}, 400

        filename = f"{user_id}_{user_sns}_{gid}_{punish_id}_punish"
        try:
            upload_file_on_s3(image_file, filename)
        except Exception as e:
            return {'message': f'업로드 중 오류가 발생했습니다: {str(e)}'}, 500

        return {'message': '성공적으로 업로드되었습니다.', 'filename': filename}, 201


download_model = download_ns.model("이미지 요청을 위한 모델", {
    'reason': fields.String(description='요청 이유: userProfile, groupProfile, punish 셋중 하나'),
    'userId': fields.String(description="유저의 id, reason이 userProfile, punish일 때만 필요"),
    'userSns': fields.String(description="유저가 가입한 sns, reason이 userProfile, punish일 때만 필요"),
    'gid': fields.String(description="그룹 id, reason이 groupProfile, punish일 때만 필요"),
    'punish_id': fields.String(description="벌칙 id, reason이 userProfile, punish일 때만 필요")
})

@download_ns.route('/image')
class GetUrl(Resource):
    @download_ns.expect(download_model)
    @download_ns.response(200, 'URL이 성공적으로 생성되었습니다.')
    @download_ns.response(404, '파일을 찾을 수 없습니다.')
    @download_ns.response(500, '서버 오류가 발생했습니다.')
    def get(self):
        args = download_model.parse_args()
        filename_key = args['filename']

        try:
            # URL은 3600초(1시간) 동안 유효합니다.
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': filename_key},
                ExpiresIn=3600
            )
            return url, 200

        except Exception as e:
            # Boto3의 ClientError를 더 구체적으로 처리할 수 있습니다.
            # from botocore.exceptions import ClientError
            # if isinstance(e, ClientError) and e.response['Error']['Code'] == 'NoSuchKey':
            #     return {'message': '파일을 찾을 수 없습니다.'}, 404

            print(e)
            return {'message': '다운로드 URL 생성 중 오류가 발생했습니다.'}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)