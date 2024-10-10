import os
import json
import pydicom
import argparse
import datetime
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage
from PIL import Image
import numpy as np
import logging

from bfd9000_dicom.dicom_tags import dpi_to_dicom_spacing, build_file_meta, add_common_bolton_brush_tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def extract_and_convert_data(file_path):
    file_name = os.path.basename(file_path)
    # Extract data from file name
    patient_id = file_name[0:5]
    image_type = file_name[5]
    patient_sex = file_name[6]
    patient_age = file_name[7:13]  # Assume format is 'AAyBBm'

    # Parse age from format 'AAyBBm' (e.g., '23y02m') to total months 'nnnM'
    years = int(patient_age[:2])
    months = int(patient_age[3:5])
    total_months = years * 12 + months

    # Format total months as zero-padded string 'nnnM'
    formatted_age = f"{total_months:03}M"  # Zero-padded to 3 digits
    logger.debug(f"Patient Age: [{formatted_age}]")
    logger.debug(f"PatientId: [{patient_id}]")
    logger.debug(f"Image Type: [{image_type}]")
    logger.debug(f"PatientSex: [{patient_sex}]")

    return patient_id, image_type, patient_sex, formatted_age


def convert_tiff_to_dicom(tiff_path, dicom_path, dicom_json=None):
    # Open the TIFF file using Pillow
    with Image.open(tiff_path) as img:
        # Convert image to grayscale if it isn't already
        img = img.convert('I')

        # Extract DPI information
        dpi_horizontal, dpi_vertical = img.info['dpi']

        # Load the image into a numpy array and ensure it's in 16-bit
        # Explicitly setting dtype to uint16
        img_array = np.array(img, dtype=np.uint16)

        # Check the array dimensions and flatten if necessary
        if len(img_array.shape) > 2:
            # Take the first channel if multi-dimensional
            img_array = img_array[:, :, 0]

        # Check maximum pixel value to infer bit depth
        max_pixel_value = img_array.max()
        if max_pixel_value > 4095:
            bits_allocated = 16
        else:
            bits_allocated = 12  # Assumes 12-bit data if max value is 4095 or less

        logger.warning(f"max_pixel_value: {max_pixel_value}, allocating {
                       bits_allocated} bits.")

        bits_stored = bits_allocated
        high_bit = bits_stored - 1

    # Create and populate DICOM dataset with image data and metadata
    if dicom_json:
        ds = load_dataset_from_file(dicom_json)
    else:
        ds = build_dicom_without_image(tiff_path)
    ds.Rows, ds.Columns = img_array.shape[0], img_array.shape[1]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.BitsStored = bits_stored
    ds.BitsAllocated = bits_allocated
    ds.HighBit = high_bit
    ds.PixelData = img_array.tobytes()

    (ds.NominalScannedPixelSpacing, ds.PixelAspectRatio) = dpi_to_dicom_spacing(
        dpi_horizontal, dpi_vertical)
    ds.PixelSpacing = ds.NominalScannedPixelSpacing
    ds.PixelSpacingCalibrationType = "GEOMETRY"

    add_common_bolton_brush_tags(ds)

    # Save the DICOM file
    ds.save_as(dicom_path, write_like_original=False)
    print(f"Saved DICOM file at {dicom_path}")


def load_dataset_from_file(json_file_path) -> Dataset:
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)
    ds = Dataset.from_json(json_data)
    ds.file_meta = build_file_meta()
    return ds

def build_dicom_without_image(file_path) -> Dataset:
    # Create the DICOM Dataset
    # Create File Meta Information
    ds = Dataset()
    ds.file_meta = build_file_meta()
    ds.PatientID, image_type, ds.PatientSex, ds.PatientAge = extract_and_convert_data(
        file_path)
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    ds.SOPClassUID = SecondaryCaptureImageStorage

    ds.StudyID = '1'

    ds.SeriesNumber = '1'
    ds.InstanceNumber = '1'
    ds.ImageComments = 'Converted from TIFF'

    # Additional DICOM attributes to address missing elements
    ds.AccessionNumber = ''  # Use the actual accession number

    # Conditional elements (only necessary under certain conditions)
    # These should be set based on the actual image and its metadata, and may be omitted if not applicable.
    ds.ImageLaterality = 'U'
    ds.PatientOrientation = 'AF'
    return ds


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Convert a TIFF file to DICOM, with optional DICOM tags from JSON.")
    parser.add_argument('input_tiff', type=str, help="Input TIFF file path")
    parser.add_argument('output_dcm', type=str, help="Output DICOM file path")
    parser.add_argument('--dicom_json', type=str,
                        help="Path to DICOM tags JSON file (optional)", default=None)

    # Parse the arguments
    args = parser.parse_args()

    # Perform the conversion
    convert_tiff_to_dicom(args.input_tiff, args.output_dcm, args.dicom_json)


if __name__ == "__main__":
    main()

# Example usage
