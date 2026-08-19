import os
import base64


def encode_logo(request):
    image_path = os.path.join(os.path.dirname(__file__), 'Report_Logo.png')
    logo = ""
    with open(image_path, 'rb') as image_file:
        # Read the binary data of the image
        image_binary = image_file.read()

        # Encode the binary data to base64
        image_base64 = base64.b64encode(image_binary).decode('utf-8')
        return {'report_logo': image_base64}


def encode_signature(request):
    image_path = os.path.join(os.path.dirname(__file__), 'official_report_signature.png')
    with open(image_path, 'rb') as image_file:
        # Read the binary data of the image
        image_binary = image_file.read()

        # Encode the binary data to base64
        image_base64 = base64.b64encode(image_binary).decode('utf-8')
        return {'signature': image_base64}