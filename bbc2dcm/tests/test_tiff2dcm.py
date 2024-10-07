import unittest
from bfd9000_dicom.tiff2dcm import extract_and_convert_data
import logging


class TestTiff2Dicom(unittest.TestCase):

    def test_extract_data_from_filename(self):

        file_path = "~/Downloads/B0013LM18y01m.tif"
        a, b, c, d = extract_and_convert_data(file_path)
        self.assertEqual(a,"B0013")
        self.assertEqual(b,"L")
        self.assertEqual(c,"M")
        self.assertEqual(d,"217M")

