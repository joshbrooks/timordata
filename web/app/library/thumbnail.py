import logging
import os
import subprocess
from tempfile import NamedTemporaryFile

import ghostscript
import shutil

from unidecode import unidecode
from wand.color import Color
from wand.image import Image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def make_thumbnail_gs(file_path, thumbnail_path, res, page):
    """
    This is significantly faster for pdf files
    :param file_path:
    :param thumbnail_path:
    :param res:
    :param page:
    :return:
    """
 # 1 index for gs
    args = [
        "gs",
        "-dFirstPage=" + str(page + 1),
        "-dLastPage=" + str(page + 1),
        "-dNOPAUSE", "-dSAFER",
        "-sDEVICE=jpeg",
        "-o", thumbnail_path,
        "-c", ".setpdfwrite",
        "-f", file_path,
        "-r" + str(res),

    ]
    subprocess.call(args)
    # ghostscript.Ghostscript(*args)
    return thumbnail_path


def make_thumbnail(file_path, thumbnail_path, res, page):
    # Workaround for "unicodeEncodeError"
    try:
        os.stat(file_path)
    except UnicodeEncodeError:
        file_path = file_path.encode('utf-8')
        os.stat(file_path)
    except OSError:
        return None

    logger.debug('Opening {}'.format(file_path))
    temp_file = None
    if file_path.endswith(b'pdf'):
        temp_file = NamedTemporaryFile()
        # Rip to an image with ghostscript first
        file_path = make_thumbnail_gs(file_path, thumbnail_path=temp_file.name, res=res, page=page)
    try:
        with Image(filename=file_path, format='jpg') as img:
            logger.debug('Opened {}'.format(file_path))
            res = float(res)
            aspect = img.width / img.height
            if aspect > 1:
                w = int(res)
                h = int(img.height * res / img.width)
            else:
                h = int(res)
                w = int(img.width * res / img.height)
            if page in [0, '0', 'cover'] and img.format == 'PDF':
                logger.debug('Clone first page {}'.format(file_path))
                img = img.sequence[0].clone()
                img.format = 'jpg'
                img.background_color = Color('white')
                img.alpha_channel = 'remove'
                img.resize(width=w, height=h)
                logger.debug('Save {} -> {}'.format(file_path, thumbnail_path))

                img.save(filename=thumbnail_path)

            else:
                img = img.sequence[int(page)].clone()
                img.format = 'jpg'
                img.background_color = Color('white')
                img.alpha_channel = 'remove'
                img.resize(width=w, height=h)
                logger.debug('Save {} -> {}'.format(file_path, thumbnail_path))
                img.save(filename=thumbnail_path)
    except Exception as e:
        logger.exception(e.message)

    if temp_file and os.path.exists(temp_file.name):
        temp_file.close()
    # raise AssertionError, 'Should be cool'

    return thumbnail_path


def make_thumbnail_convert(file_path, thumbnail_path, res, page=0, _format='jpg'):
    if isinstance(page, str):
        if page in [0, '0', 'cover']:
            file_path = '{}[0]'.format(file_path, page)
        else:
            file_path = '{}[{}]'.format(file_path, page)

    call = ['convert', file_path, '-resize', '{}'.format(res), '{}:{}'.format(_format, thumbnail_path)]
    print(call)
    subprocess.call(call)
    return thumbnail_path
