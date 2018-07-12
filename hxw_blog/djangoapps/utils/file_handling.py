import datetime
import io
import random
from PIL import Image

from django.core.files.uploadedfile import InMemoryUploadedFile


def get_thumbnail(orig, width=180, height=180):
    """get the thumbnail of orig
    @return: InMemoryUploadedFile which can be assigned to ImageField
    """

    now = datetime.datetime.now()
    filename = now.strftime("%Y%m%d%M%H%S{0}{1}".format(random.randint(1, 999999), '.jpg'))
    quality = 95

    try:
        thumb = Image.open(orig).convert('RGB')
        size = (width, height)
        thumb.thumbnail(size, Image.ANTIALIAS)
        thumb_io = io.BytesIO()
        thumb.save(thumb_io, format="JPEG", quality=quality)
        thumb_file = InMemoryUploadedFile(thumb_io, None, filename, 'image/jpeg',
                                          None, None)
        return thumb_file
    except Exception as e:
        return None
