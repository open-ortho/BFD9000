""" DICOM tags for specific types of images.

A good explanation for ImageOrientationPatient
https://dicomiseasy.blogspot.com/2013/06/getting-oriented-using-image-plane.html
"""
from pydicom import Dataset

def LL(ds):
    ds.ImagePositionPatient = ''
    ds.ImageOrientationPatient = ''

def PA(ds):
    ds.ImagePositionPatient = ''
    ds.ImageOrientationPatient = ''