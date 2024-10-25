import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List

import qrcode
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from tqdm import tqdm

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
    if direction in ["S", "W"]:
        decimal = -decimal
    return decimal


def extract_gps_coordinates(gps_info):
    """Extract GPS latitude and longitude from GPSInfo dictionary."""
    latitude = gps_info.get("GPSLatitude")
    latitude_ref = gps_info.get("GPSLatitudeRef")
    longitude = gps_info.get("GPSLongitude")
    longitude_ref = gps_info.get("GPSLongitudeRef")

    if latitude and latitude_ref and longitude and longitude_ref:
        lat = convert_to_decimal(*latitude, latitude_ref)
        lon = convert_to_decimal(*longitude, longitude_ref)
        return lat, lon
    return None, None


def generate_qr_codes(lat: float, lon: float, filename: str, output_dir: str):
    """Generate and save a QR code that opens Google Maps."""

    def generate_qr(provider, image_name, url):
        qr = qrcode.make(url)
        output_file = f"{output_dir}/{image_name}_{provider}_location_qr.png"
        qr.save(output_file)
        return output_file

    google_output_file = generate_qr(
        "google", filename, f"https://www.google.com/maps?q={lat},{lon}"
    )
    apple_output_file = generate_qr(
        "apple", filename, f"https://maps.apple.com/?q={lat},{lon}"
    )

    return google_output_file, apple_output_file


@dataclass
class ImageMetadata:
    name: str
    path: str
    gps_info: Optional[Dict] = field(default_factory=dict)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_qr_code_path: Optional[str] = None
    apple_qr_code_path: Optional[str] = None


def generate_pdf(images_metadata: List[ImageMetadata], output_file="output.pdf"):
    """Create a PDF with each page containing the original image and QR codes."""
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    for metadata in tqdm(images_metadata, desc="Adding images to the PDF", unit="image"):
        # Add the filename at the top of the page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, height - 50, f"File: {metadata.name}")

        # Draw the original image (large version)
        original_img = ImageReader(metadata.path)
        c.drawImage(
            original_img,
            30,
            height / 2,
            width - 60,
            height / 2 - 80,
            preserveAspectRatio=True,
        )

        # Draw the Google Maps QR code (small version)
        c.drawString(60, 175, "Google Maps")
        google_qr = ImageReader(metadata.google_qr_code_path)
        c.drawImage(google_qr, 50, 50, 120, 120, preserveAspectRatio=True)

        # Draw the Apple Maps QR code (small version)
        c.drawString(215, 175, "Apple Maps")
        apple_qr = ImageReader(metadata.apple_qr_code_path)
        c.drawImage(apple_qr, 200, 50, 120, 120, preserveAspectRatio=True)

        # Move to the next page
        c.showPage()

    # Save the PDF
    c.save()
    print(f"PDF saved as '{output_file}'.")


def main():
    print("Running script")

    project_name = "test"
    directory_path = f"images/{project_name}"
    output_path = f"output/{project_name}"

    # Ensure the input and output directory exists
    image_dir = Path(directory_path)

    if not image_dir.exists():
        print(f"Directory not found: {directory_path}")
        return
    output_dir = Path(output_path)
    output_dir.mkdir(exist_ok=True)

    # pillow plugin for .HEIC files
    register_heif_opener()
    image_metadata = {}
    valid_extensions = {".jpg", ".HEIC", ".png", ".jpeg"}
    images = [f for f in image_dir.glob("*") if f.suffix in valid_extensions]
    for image_path in tqdm(
        images, desc="Processing images", unit="image"
    ):  # Iterate over all files
        image_metadata[image_path.stem] = ImageMetadata(
            name=image_path.stem, path=image_path
        )

        gps_info = get_gps_data(str(image_path))
        image_metadata[image_path.stem].gps_info = gps_info

        if gps_info:
            lat, lon = extract_gps_coordinates(gps_info)
            image_metadata[image_path.stem].latitude = lat
            image_metadata[image_path.stem].longitude = lon
            if lat is not None and lon is not None:
                google_qr, apple_qr = generate_qr_codes(
                    lat, lon, image_path.stem, output_dir=output_path
                )
                image_metadata[image_path.stem].google_qr_code_path = google_qr
                image_metadata[image_path.stem].apple_qr_code_path = apple_qr
    filtered_data = [
        meta for meta in image_metadata.values() if meta.google_qr_code_path is not None
    ]
    if filtered_data:
        generate_pdf(filtered_data, output_file=f"{project_name}.pdf")


if __name__ == "__main__":
    main()
