import pytest
from hamcrest import *
from unittest.mock import Mock, call
from pan_images import *
from os import path

class TestImage:
    def test_from_json_returns_an_image_with_an_id_and_a_file_name(self):
        assert_that(Image.from_json_attributes({ "id": "52292", "attributes": { "Filename": [ "PP  Zonder nummer verso 91.tif" ] } }),
            equal_to(Image("52292", "PP  Zonder nummer verso 91.tif")))

    def test_jpeg_name_replaces_the_extension_to_jpeg(self):
        assert_that(Image("52292", "PP Zonder nummer verso 91.tif").jpeg_name, equal_to("PP Zonder nummer verso 91.jpg"))

class TestImageBatch:
    def test_size_is_the_size_of_the_list_of_images(self):
        assert_that(ImageBatch(total_size=300, from_index=1, images=[]).size, equal_to(0))
        assert_that(ImageBatch(total_size=300, from_index=1, images=[Image("123", "1231")]).size, equal_to(1))

    def test_concatenate_batch_results_in_concatenation_sum_of_2_batches(self):
        assert_that(ImageBatch(total_size=2, from_index=1, images=[Image("1", "file1")]).concatenate(ImageBatch(total_size=2, from_index=2, images=[Image("2", "file2")])), equal_to(
            ImageBatch(total_size=2, from_index=1, images=[Image("1", "file1"),Image("2", "file2")])
        ))

    def test_next_index_is_current_index_plus_size(self):
        assert_that(ImageBatch(total_size=300, from_index=23, images=[Image("0", "file0"), Image("1", "file0")]).next_index, equal_to(25))

    def test_all_from_returns_all_images_from_image_repository(self):
        repository=Mock(ImagesRepository)
        repository.get_images.side_effect = [
            ImageBatch(total_size=3, from_index=0, images=[Image("1", "file1"),Image("2", "file2")]),
            ImageBatch(total_size=3, from_index=2, images=[Image("3", "file2")]),
            ImageBatch(total_size=3, from_index=3, images=[]),
            ]
        assert_that(ImageBatch.all_from(repository, 2), equal_to(
            ImageBatch(total_size=3, from_index=0, images=[Image("1", "file1"),Image("2", "file2"), Image("3", "file2")])))

    def test_all_from_calls_all_batches_in_sequence(self):
        repository=Mock(ImagesRepository)
        repository.get_images.side_effect = [
            ImageBatch(total_size=3, from_index=0, images=[Image("1", "file1"),Image("2", "file2")]),
            ImageBatch(total_size=3, from_index=2, images=[Image("3", "file2")]),
            ImageBatch(total_size=3, from_index=3, images=[]),
            ]
        ImageBatch.all_from(repository, 2)
        assert_that(repository.get_images.call_args_list, equal_to([call(0,2), call(2,2), call(3,2)]))

class TestImageRepository:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.mock_connection = Mock(requests)
        self.repository = ImagesRepository(self.mock_connection)
        
    def test_get_images_returns_a_batch_of_images(self):
        self.mock_connection.get.return_value = StubResponse(ok=True, text="""{"totalNumberOfAssets":1930,"assets":[{"id":"328260","attributes":{"Filename":["PP 1255.tif"]}}]}""")
        image_batch = self.repository.get_images(1,1)
        assert_that(image_batch, equal_to(ImageBatch(total_size=1930, from_index=1, images=[Image.from_json_attributes({"id":"328260","attributes":{"Filename":["PP 1255.tif"]} })])))

    def test_get_images_gets_the_images_from_tyler(self):
        self.mock_connection.get.return_value = StubResponse(ok=True, text="""{"totalNumberOfAssets":1930,"assets":[{"id":"328260","attributes":{"Filename":["PP 1255.tif"]}}]}""")
        self.repository.get_images(23,51)
        self.mock_connection.get.assert_called_once_with("http://beeld.teylersmuseum.nl:8085/panpoeticon/api/v1/asset", params={"query":str({"fields":["Filename"],"startingIndex":23,"pageSize":51,"sortOptions":{"field":"Filename","order":"asc"}})})

class TestImageDownloader:
    def xtest_download_downloads_the_image_to_a_file(self):
        downloader = ImageDownloader(download_dir='data')
        downloader.download(Image("52292","Bla bla.tif"))
        assert_that(path.exists('data/Bla bla.jpg')) 

