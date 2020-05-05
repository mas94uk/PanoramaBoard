#About
A rough-and-ready Python program to lay out a set of panorama photos, each with a caption, on a large canvas, like this:

>![Full page](https://raw.githubusercontent.com/mas94uk/PanoramaBoard/master/example_result_lowres.jpg "Full page")
>![Caption detail](https://raw.githubusercontent.com/mas94uk/PanoramaBoard/master/example_result_detail.jpg "Caption detail")

(I used this to create large wall posters from holiday snaps to fit in Ikea frames.)

The advantage of doing it programatically, rather than laying it out by hand in Gimp (or similar) is that you can experiment with different layouts fairly easily.

Only one resize is performed on each photo, to minimise artefacts from resizing.

Also inluded is a simple script to find panorama photos in a library.

The code is a bit clumsy, probably not very efficient and has some dead experimental code left in.  Feel free to improve upon it!  Runs with Python 2 - sorry.

The example images above use "Scriptina" font ("SCRIPTIN.ttf"), which is readily available on the internet. 

#Requirements (based on Ubuntu 18.04)
 * apt install python-pip     # Because we use `pip` to install Python libraries
 * pip install opencv-python  # for `import cv2`
 * pip install Pillow         # for `import PIL.*`

#Usage
* Place all original photos in a directory
* Name the files according to the pattern `[rr[-pp]] Caption.ext` where
 * rr is the row number
 * pp is the position (optional)
 * Caption is the caption to be drawn
 * ext is the file extension (e.g. jpg)
* Rows are placed in ascending order, as are positions within the rows.  Gaps in the numbering are permitted.
* Run panoramaboard.py with no parameters, to show the required command line parameters
  
#Example
Source files:

    SourceFiles/100 Rye, March 2016.jpg
    SourceFiles/115-3 York, July 2015.jpg
    SourceFiles/115-7 Animal Kingdom, April 2015.jpg`

Command line:

    ./panoramaboard.py ./SourceFiles 475 680 3.35 7.1 300 ./SCRIPTIN.ttf 23 594 841

#Licence
  Licensed under [GPL 3](https://www.gnu.org/licenses/gpl-3.0.en.html).
