from pathlib import Path

from PIL import Image, ExifTags
import os
from pillow_heif import register_heif_opener

GPS_TAG = 34853  # GPSInfo tag ID


def get_gps_data(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    # Open the image and get the EXIF data
    with Image.open(image_path) as img:
        exif_data = img.getexif()

        # Check if GPSInfo tag (34853) exists
        if GPS_TAG in exif_data:
            raw_gps_data = exif_data.get_ifd(GPS_TAG)

            gps_info = {
                ExifTags.GPSTAGS.get(tag, tag): value
                for tag, value in raw_gps_data.items()
            }
            return gps_info

    return None  # Return None if no GPS data is found

def convert_to_decimal(degrees, minutes, seconds, direction):
    """Convert DMS (Degrees, Minutes, Seconds) to Decimal."""
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_gps_coordinates(gps_info):
    """Extract GPS latitude and longitude from GPSInfo dictionary."""
    latitude = gps_info.get('GPSLatitude')
    latitude_ref = gps_info.get('GPSLatitudeRef')
    longitude = gps_info.get('GPSLongitude')
    longitude_ref = gps_info.get('GPSLongitudeRef')

    if latitude and latitude_ref and longitude and longitude_ref:
        lat = convert_to_decimal(*latitude, latitude_ref)
        lon = convert_to_decimal(*longitude, longitude_ref)
        return lat, lon
    return None, None


def main():
    print("Running script")
    print("Registering HEIF opener")
    register_heif_opener()
    directory_path = "images/stucco_repair"

    image_dir = Path(directory_path)

    if not image_dir.exists():
        print(f"Directory not found: {directory_path}")
        return

    for image_path in image_dir.glob("*.*"):  # Iterate over all files
        print(f"Processing: {image_path}")
        gps_info = get_gps_data(str(image_path))

        if gps_info:
            lat, lon = extract_gps_coordinates(gps_info)
            if lat is not None and lon is not None:
                print(f"Latitude: {lat}, Longitude: {lon}")
                # generate_qr_code(lat, lon, image_path.stem)
            else:
                print(f"No GPS coordinates found in {image_path.name}.")
        else:
            print(f"No GPS data available in {image_path.name}.")


if __name__ == "__main__":
    main()
