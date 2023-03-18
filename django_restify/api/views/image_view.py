import hashlib
from base64 import b64decode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ..models import Image


def image_save(base64_data, extension):
    # decode the base64 data
    image_data = b64decode(base64_data)
    # calculate the md5 hash of the image data
    image_hash = hashlib.md5(image_data).hexdigest()

    try:
        Image.objects.get(pk=image_hash)
    except Image.DoesNotExist:
        Image.objects.create(h=image_hash, extension=extension, data=image_data)
    return image_hash


def image_delete(image_hash):
    image = Image.objects.get(h=image_hash)
    image.delete()


def image_view(request, image_hash):
    image = get_object_or_404(Image, h=image_hash)
    response = HttpResponse(image.data, content_type=f"image/{image.extension}")
    return response
