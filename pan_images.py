#!/usr/bin/env python
import json
from posixpath import basename
import requests
from os import path, stat
from pathlib import Path
from dataclasses import dataclass
from typing import *

@dataclass
class Image:
    id: str
    filename: str
    @staticmethod
    def from_json_attributes(json_def):
        return Image(id=json_def["id"], filename=json_def["attributes"]["Filename"][0])
        
    @property
    def jpeg_name(self):
        return str(Path(self.filename).with_suffix('.jpg'))

@dataclass
class StubResponse:
    ok: bool
    text: str


@dataclass
class ImageBatch:
    total_size: int
    from_index: int
    images: List[Image]

    @staticmethod
    def all_from(repository, batch_size):
        batch = repository.get_images(0, batch_size)
        next_batch = batch
        while True:
            next_batch = repository.get_images(next_batch.next_index, batch_size)
            if next_batch.is_empty:
                return batch
            batch = batch.concatenate(next_batch)

    @property
    def next_index(self):
        return self.from_index + self.size

    @property
    def is_empty(self):
        return self.size == 0

    @property
    def size(self):
        return len(self.images)

    def concatenate(self, other_batch):
        return ImageBatch(total_size=self.total_size, from_index=self.from_index, images=self.images+other_batch.images)

class ImagesRepository:
    def __init__(self, connection=requests):
        self.connnection = connection

    def get_images(self, from_index, size):
        response = self.connnection.get("http://beeld.teylersmuseum.nl:8085/panpoeticon/api/v1/asset", params={'query':str({"fields":["Filename"],"startingIndex":from_index,"pageSize":size,"sortOptions":{"field":"Filename","order":"asc"}})})
        json_body = json.loads(response.text)
        return ImageBatch(total_size=json_body["totalNumberOfAssets"], from_index=from_index, images=[Image.from_json_attributes(asset) for asset in json_body["assets"]])

class ImageDownloader:
    def __init__(self, download_dir):
        self.download_dir = download_dir
    
    def download(self, image):
        response = requests.get('http://beeld.teylersmuseum.nl:8085/panpoeticon/api/v1/asset/{}/_derivative'.format(image.id), params={"imageOptions":str({"outputFileFormat":"JPEG","compressionQuality":95,"colorMode":"RGB"})})
        with open(self.download_path(image), "wb+") as f:
            f.write(response.content)

    def download_path(self, image):
        return path.join(self.download_dir, image.jpeg_name)



if __name__ == '__main__':
    downloader = ImageDownloader('data')
    print('Getting image batch')
    image_batch = ImageBatch.all_from(ImagesRepository(), 200)
    print('Image batch size is: {}'.format(image_batch.size))
    for (i, image) in enumerate(image_batch.images):
        if not path.exists(downloader.download_path(image)):
            print("Downloading image {}: {}".format(i+1, image))
            downloader.download(image)
        else:
            print("Downloading image {}: {}\t\texists. skipping...".format(i+1, image))
            
