# Image Location Report

Sometimes you need to know where some stuff is, and a PDF is an easy deliverable to communicate that. 

This script turns a directory full of files into a 
PDF report with the image, and 2 QR codes, one for apple maps and one for Google Maps to communicate where the photo was taken


# Use
* clone repo
* `poetry install`
* create a folder named `images/`
* move a folder full of images into `images`
* change the value of the variable `project_name="test"` to match the name of the folder
* run the file

## Future features
* highlighting elements with the [pillow `ImageDraw` functionality](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
* Using an AI API to create a description of the image like [replicate](https://replicate.com/methexis-inc/img2prompt/api/learn-more)
* Caching/storing metadata information somewhere.
    * At least a database running in a container with a volume setup. Possibly using [Docker test-containers](https://testcontainers.com)?
