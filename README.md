## ImageReconstructionFromHdf

This project reconstructs ultrasound scan data stored in HDF5 format into images for non-destructive testing (NDT), helping detect material inconsistencies or analyze the contents of sealed objects based on each material’s characteristic resonance signature

### Input
A `.hdf5` file containing:
  - Raw sensor data vectors
  - Metadata such as:
    - Speed of sound in the scanned material
    - Sensor configuration (e.g., positions, timestamps)
    - Calibration parameters

### Output
A 2D image file (not sure which format) that visualizes the internal structure of the scanned object.

### Technical 
#### Language and Dependencies
- Python 3.x
- Required libraries (these files will be listed in a `requirements.txt` file in the project directory):
  - `h5py` – read HDF5 files
  - `numpy` – linear algebra and numerical processing
  - `matplotlib` or `Pillow` – for image generation
  - `scipy` – for advanced numerical methods (if needed)
 
#### Installation
```bash
git clone https://github.com/yourusername/ImageReconstructionFromHdf.git
cd ImageReconstructionFromHdf
pip install -r requirements.txt
```
#### Running
```bash
python reconstruct.py path/to/input_file.hdf5
```
### Notes
- The image reconstruction is based on linear algebra techniques applied to the raw data vectors. I may not do anything intelligent here due to scope.
- The project is designed for offline processing—no GUI is included.

### Course Information
This project was proposed as part of the course [Basic Programming Skills in Python](https://github.com/Code-Maven/wis-python-course-2025-03), led by [Gábor Szabó](https://github.com/szabgab) at the [Weizmann Institute of Science](https://www.weizmann.ac.il) in Israel 🇮🇱
