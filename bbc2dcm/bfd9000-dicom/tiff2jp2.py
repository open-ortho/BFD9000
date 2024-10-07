import argparse
import json
from PIL import Image
import glymur
import numpy as np  # Import numpy

def convert_tiff_to_jpeg2000_lossless(input_tiff, output_jp2, dicom_json=None):
    # Open the TIFF file as a 16-bit grayscale image
    with Image.open(input_tiff) as img:
        # Convert to 16-bit grayscale
        img = img.convert('I;16')  # 'I;16' for 16-bit grayscale
        
        # Convert the image to a numpy array
        img_array = np.array(img)
        # Ensure the array is 3-dimensional (single-channel, height, width)
        img_array = img_array[:, :, np.newaxis]  # Add an extra dimension for channel
        
        # Read DICOM JSON if provided
        if dicom_json:
            with open(dicom_json, 'r') as f:
                dicom_tags = json.load(f)
            print(f"Loaded DICOM tags: {dicom_tags}")
            # DICOM tags processing or logging can be done here

        # Convert to JPEG2000 lossless format using glymur
        jp2 = glymur.Jp2k(output_jp2)
        jp2[:] = img_array  # Assign the numpy array

    print(f"Conversion completed: {output_jp2}")



def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Convert a TIFF file to JPEG2000 lossless, with optional DICOM tags from JSON.")
    parser.add_argument('input_tiff', type=str, help="Input TIFF file path")
    parser.add_argument('output_jp2', type=str, help="Output JPEG2000 (JP2) file path")
    parser.add_argument('--dicom_json', type=str, help="Path to DICOM tags JSON file (optional)", default=None)
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Perform the conversion
    convert_tiff_to_jpeg2000_lossless(args.input_tiff, args.output_jp2, args.dicom_json)

if __name__ == "__main__":
    main()
