__author__ = 'cai'
import qiniu
import uuid
qiniu_access_key = 'drsiPaX0y46jK0d_GgIoLzBy-YrXGVsUI3zH_ixu'
qiniu_secret_key = '7xlBV9gLYX0OpwZ2Ql6rCGcMroYRVMehXKCzxXVn'
qiniu_bucket_name = 'tour'
qiniu_resource_url = 'http://7xj4kz.com1.z0.glb.clouddn.com'

q = qiniu.Auth(qiniu_access_key, qiniu_secret_key)


class Upload(object):

    def image_upload(self, img_file, image_name=None):
        if not image_name:
            image_name = str(uuid.uuid1())
        mime_type = 'image/jpg'
        token = q.upload_token(qiniu_bucket_name, image_name)
        qiniu.put_data(token, image_name, img_file, mime_type=mime_type, check_crc=True)
        return '%s/%s' % (qiniu_resource_url, image_name)

    def local_image_upload(self, img_path):
        image_name = 'test'
        mime_type = 'image/jpg'
        token = q.upload_token(qiniu_bucket_name, image_name)
        qiniu.put_file(token, image_name, img_path, mime_type=mime_type, check_crc=True)

    def excel_upload(self, excel_file, excel_name=None):
        if not excel_name:
            excel_name = str(uuid.uuid1())
        mime_type = 'application/ms-excel'
        token = q.upload_token(qiniu_bucket_name, excel_name)
        qiniu.put_data(token, excel_name, excel_file, mime_type=mime_type, check_crc=True)
        return '%s/%s' % (qiniu_resource_url, excel_name)

    def zip_upload(self, zip_file, zip_name=None):
        if not zip_name:
            zip_name = str(uuid.uuid1())
        mime_type = 'application/zip'
        token = q.upload_token(qiniu_bucket_name, zip_name)
        qiniu.put_data(token, zip_name, zip_file, mime_type=mime_type, check_crc=True)
        return '%s/%s' % (qiniu_resource_url, zip_name)

my_qiniu = Upload()

