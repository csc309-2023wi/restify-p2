import hashlib
from base64 import b64decode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from io import BytesIO
from PIL import Image as PIL_Image

from ..models import Image


def image_save(base64_data, extension):
    # decode the base64 data
    image_data = b64decode(base64_data)
    # calculate the md5 hash of the image data
    image_hash = hashlib.md5(image_data).hexdigest()

    image_obj = None
    try:
        image_obj = Image.objects.get(pk=image_hash)
    except Image.DoesNotExist:
        image_obj = Image.objects.create(
            h=image_hash, extension=extension, data=image_data
        )
    return image_obj


def image_view(request, image_hash):
    image = get_object_or_404(Image, h=image_hash)
    image_data = image.data

    # get query parameters
    width = request.GET.get("width")
    height = request.GET.get("height")
    requested_ext = request.GET.get("ext")

    # validate query parameters
    if width and height:
        return HttpResponse("Cannot specify both width and height", status=400)

    # open image with Pillow
    pil_image = None
    if width or height or (requested_ext and image.extension != requested_ext.lower()):
        try:
            pil_image = PIL_Image.open(BytesIO(image_data))
        except Exception as e:
            return HttpResponse(str(e), status=400)

    # resize image if necessary
    if width or height:
        try:
            if width:
                width = int(width)
                height = int((float(pil_image.size[1]) / pil_image.size[0]) * width)
            else:
                height = int(height)
                width = int((float(pil_image.size[0]) / pil_image.size[1]) * height)
            pil_image = pil_image.resize((width, height), PIL_Image.ANTIALIAS)
        except Exception as e:
            return HttpResponse(str(e), status=400)

    # save modified image if necessary
    outfile_ext = requested_ext.lower() if requested_ext else image.extension
    if pil_image:
        output_buffer = BytesIO()
        pil_format = PIL_Image.EXTENSION.get(
            "." + outfile_ext
        ) or PIL_Image.registered_extensions().get("." + outfile_ext)
        pil_image.save(output_buffer, format=pil_format)
        image_data = output_buffer.getvalue()

    content_type = f"image/{outfile_ext}"

    # create and return response
    response = HttpResponse(image_data, content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{image_hash}.{outfile_ext}"'
    return response
