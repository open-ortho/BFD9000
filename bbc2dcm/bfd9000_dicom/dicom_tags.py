""" DICOM tags for specific types of images.

A good explanation for ImageOrientationPatient
https://dicomiseasy.blogspot.com/2013/06/getting-oriented-using-image-plane.html
"""
from pydicom import Dataset

def LL(ds:Dataset):
    ds.ImagePositionPatient = ''
    ds.ImageOrientationPatient = ''

def PA(ds:Dataset):
    ds.ImagePositionPatient = ''
    ds.ImageOrientationPatient = ''

def expected_tags():
    """ The set of expected tags to come in from JSON.
    
    These depend on the image, 
    
    """

    ds = Dataset()
    ds.DateOfSecondaryCapture = ''
    ds.TimeOfSecondaryCapture = ''

def dpi_to_dicom_spacing(dpi_horizontal, dpi_vertical=None):
    """
    Convert DPI to DICOM's NominalScannedPixelSpacing and PixelAspectRatio.
    
    Parameters:
    dpi_horizontal (float): The DPI for the horizontal dimension.
    dpi_vertical (float, optional): The DPI for the vertical dimension. If not provided,
        it is assumed that vertical DPI is the same as horizontal DPI.
    
    Returns:
    tuple: Returns two tuples:
        - NominalScannedPixelSpacing: Tuple of two floats (spacingX, spacingY) in mm.
        - PixelAspectRatio: Tuple of two integers (aspectX, aspectY) or None if pixels are square.
    """
    mm_per_inch = 25.4  # 1 inch is 25.4 millimeters

    if dpi_vertical is None:
        dpi_vertical = dpi_horizontal

    # Calculate pixels per millimeter
    ppmm_horizontal = dpi_horizontal / mm_per_inch
    ppmm_vertical = dpi_vertical / mm_per_inch

    # Calculate NominalScannedPixelSpacing in mm
    spacing_horizontal = 1 / ppmm_horizontal
    spacing_vertical = 1 / ppmm_vertical

    # Calculate PixelAspectRatio using original dpi values to avoid rounding errors
    if dpi_horizontal == dpi_vertical:
        pixel_aspect_ratio = (1,1)
    else:
        # Reduce aspect ratio to simplest form
        from math import gcd
        gcd_ratio = gcd(int(dpi_vertical), int(dpi_horizontal))
        pixel_aspect_ratio = (int(dpi_vertical / gcd_ratio), int(dpi_horizontal / gcd_ratio))

    return ((spacing_horizontal, spacing_vertical), pixel_aspect_ratio)
