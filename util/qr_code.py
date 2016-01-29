import qrcode



def create_qrcode(URL, file_path):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=1)
    qr.add_data(URL)
    qr.make(fit=True)
    img = qr.make_image()
    img.save(file_path)

create_qrcode('http://192.168.1.123:8000/leave/sick_leave_img_upload_page/46', '/Users/cai/cai/a.png')








