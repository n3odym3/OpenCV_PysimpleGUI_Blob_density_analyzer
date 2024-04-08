# What is the purpose of this code ?
 This program has been initially designed to analyze the width and intensity of gel electrophoresis bands or to quantify the autofluorescence intensity of microalgae grown on Agar medium by quantifying tha "lightness" or "darkness" of a group of pixels.

 The software allows to selec a region of interest (ROI) on a picture, within which adaptive binarization is applied to separate the background from the "blob" of interest. The signal from the non-selected background is then subtracted from the average pixel value of the selected blob to compensate as much as possible for local darkening that may be caused by uneven lighting.

 Designed for ease of use, the program operates through a graphical user interface based on PySimpleGUI and is capable of working with many different image formats. Although this software is primarily conceived as a tool to address a specific problem in my laboratory, it can be adapted for any use that requires quantifying how light or dark a region of an image is.

 The software is also capable of converting raw fluorescence data produced by the SpeedZen (JBeamBio) fluorescence camera into uncompressed .PNG files to facilitate the analysis of photosystem II autofluorescence snapshots.

## Dependencies (Python)
 - [Numpy](https://numpy.org/)
 - [Pandas](https://pandas.pydata.org/)
 - [OpenCV](https://opencv.org/)
 - [PySimpleGui](https://www.pysimplegui.org/en/latest/)
 - [Matplotlib](https://matplotlib.org/)
 - [Seaborn](https://seaborn.pydata.org/)
 - [Natsort](https://natsort.readthedocs.io/en/stable/)
 - [Pyperclip](https://pyperclip.readthedocs.io/en/latest/)

**Installation**
```pip install numpy```
```pip install pandas```
```pip install opencv-python```
```pip install pysimplegui```
```pip install matplotlib```
```pip install seaborn```
```pip install natsort```
```pip install pyperclip```
