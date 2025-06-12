## ImageReconstructionFromHdf

This project reconstructs ultrasound scan data stored in HDF5 format into images for non-destructive testing (NDT), helping detect material inconsistencies or analyze contents of sealed objects, based on typical resonance signatures.

### Input
A `.hdf5` file containing:
  - Raw sensor data vectors
  - Metadata such as:
    - Speed of sound in the scanned material
    - Sensor configuration (e.g., positions, timestamps)
    - Calibration parameters

### Output
A 2D image file (not sure which format) that visualizes the internal structure of the scanned object.

### Language and Dependencies
- Python 3.x
- Required libraries (to be listed in `requirements.txt`):
  - `h5py` – read HDF5 files
  - `numpy` – linear algebra and numerical processing
  - `matplotlib` or `Pillow` – for image generation
  - `scipy` – for advanced numerical methods (if needed)

### Notes
- The image reconstruction is based on linear algebra techniques applied to the raw data vectors. I may not do anything intelligent here due to scope.
- The project is designed for offline processing—no GUI is included.

### Course Information
This project was proposed as part of the course [Basic Programming Skills in Python](https://github.com/Code-Maven/wis-python-course-2025-03), led by [Gábor Szabó](https://github.com/szabgab) at the [Weizmann Institute of Science](https://www.weizmann.ac.il) in Israel 🇮🇱


