# -*- coding: utf-8 -*-

# Copyright 2014-2018 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from http://www.imagebam.com/"""

from .common import Extractor, Message
from .. import text


class ImagebamExtractor(Extractor):
    """Base class for imagebam extractors"""
    category = "imagebam"
    root = "http://www.imagebam.com"

    def get_image_data(self, page_url, data):
        """Fill 'data' and return image URL"""
        page = self.request(page_url).text
        image_url = text.extract(page, 'property="og:image" content="', '"')[0]
        data["extension"] = image_url.rpartition(".")[2]
        data["image_key"] = page_url.rpartition("/")[2]
        data["image_id"] = data["image_key"][6:]
        return image_url


class ImagebamGalleryExtractor(ImagebamExtractor):
    """Extractor for image galleries from imagebam.com"""
    subcategory = "gallery"
    directory_fmt = ["{category}", "{title} - {gallery_key}"]
    filename_fmt = "{num:>03}-{image_key}.{extension}"
    archive_fmt = "{gallery_key}_{image_key}"
    pattern = [r"(?:https?://)?(?:www\.)?imagebam\.com/gallery/([0-9a-z]+)"]
    test = [
        ("http://www.imagebam.com/gallery/adz2y0f9574bjpmonaismyrhtjgvey4o", {
            "url": "fb01925129a1ff1941762eaa3a2783a66de6847f",
            "keyword": "9e25b8827474ac93c54855e798d60aa3cbecbd7a",
            "content": "596e6bfa157f2c7169805d50075c2986549973a8",
        }),
        ("http://www.imagebam.com/gallery/gsl8teckymt4vbvx1stjkyk37j70va2c", {
            "url": "7d54178cecddfd46025cc9759f5b675fbb8f65af",
            "keyword": "7d7db9664061132be50aa0d98e9602e98eb581ce",
        }),
    ]

    def __init__(self, match):
        ImagebamExtractor.__init__(self)
        self.gallery_key = match.group(1)

    def items(self):
        url = "{}/gallery/{}".format(self.root, self.gallery_key)
        page = text.extract(
            self.request(url).text, "<fieldset>", "</fieldset>")[0]

        data = self.get_metadata(page)
        imgs = self.get_image_pages(page)
        data["count"] = len(imgs)
        data["gallery_key"] = self.gallery_key

        yield Message.Version, 1
        yield Message.Directory, data
        for data["num"], page_url in enumerate(imgs, 1):
            image_url = self.get_image_data(page_url, data)
            yield Message.Url, image_url, data

    @staticmethod
    def get_metadata(page):
        """Return gallery metadata"""
        return text.extract_all(page, (
            ("title"      , "'> ", " <span "),
            (None         , "'>", "</span>"),
            ("description", ":#FCFCFC;'>", "</div>"),
        ))[0]

    @staticmethod
    def get_image_pages(page):
        """Return a list of all image pages"""
        return list(text.extract_iter(page, "<a href='", "'"))


class ImagebamImageExtractor(ImagebamExtractor):
    """Extractor for single images from imagebam.com"""
    subcategory = "image"
    filename_fmt = "{image_key}.{extension}"
    archive_fmt = "{image_key}"
    pattern = [r"(?:https?://)?(?:\w+\.)?imagebam\.com"
               r"/(?:image/|(?:[0-9a-f]{2}/){3})([0-9a-f]+)"]
    test = [
        ("http://www.imagebam.com/image/94d56c502511890", {
            "url": "b384893c35a01a09c58018db71ddc4cf2480be95",
            "keyword": "4263d4840007524129792b8587a562b5d20c2687",
            "content": "0c8768055e4e20e7c7259608b67799171b691140",
        }),
        ("http://images3.imagebam.com/1d/8c/44/94d56c502511890.png", None),
    ]

    def __init__(self, match):
        ImagebamExtractor.__init__(self)
        self.image_key = match.group(1)

    def items(self):
        page_url = "{}/image/{}".format(self.root, self.image_key)
        data = {}
        image_url = self.get_image_data(page_url, data)
        yield Message.Version, 1
        yield Message.Directory, data
        yield Message.Url, image_url, data
