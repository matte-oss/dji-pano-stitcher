# DJI Panoramic Stitcher

A tool for automatically stitching, resizing, and enhancing panoramic images shot with DJI drones.  
Combines Hugin's panorama tools, ImageMagick, SkyFill, and ExifTool for a seamless equirectangular workflow.

## Features

- **Automatic panorama stitching** using Hugin CLI tools
- **Sky filling for panoramas** using SkyFill
- **EXIF metadata injection** for proper panorama display and upload on Google Maps/Photos
- **Cross-platform support**: Windows & Linux
- **Automatic tool download (SkyFill, ExifTool)** if missing

## Prerequisites

- [Python 3.7+](https://www.python.org/)
- Images captured by DJI drone (in a folder, they should be 26)
- [Hugin](http://hugin.sourceforge.net/) installed (CLI tools in PATH or default locations)
- [ImageMagick](https://imagemagick.org/) installed (magick in PATH)
- On Linux: `exiftool` installed via package manager

## Usage

```sh
python pano.py <images-folder> [--debug-skip]
```

- `<images-folder>`: Path to folder of DJI images
- `--debug-skip`: Skips stitching/resizing steps if temp files already exist

## Workflow

1. **Detects required tools**: Hugin CLI, ImageMagick, SkyFill, ExifTool
2. **Downloads SkyFill & ExifTool** automatically if missing
3. **Stitches panoramas** using Hugin tools
4. **Resizes output** to equirectangular format
5. **Fills sky** with SkyFill
6. **Injects EXIF metadata** for panorama viewers

## Output

- Final panorama saved in `output/<your-images-folder>_pano.jpg`

## Example

```sh
python pano.py dji-images
```
Final file will be in `output/dji-images_pano.jpg`

## License

MIT License

## Credits

- [Hugin](http://hugin.sourceforge.net/)
- [SkyFill](https://stuvelfoto.nl/)
- [ImageMagick](https://imagemagick.org/)
- [ExifTool](https://exiftool.org/)
