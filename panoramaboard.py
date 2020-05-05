#!/usr/bin/python

# Panorama generator Project

import cv2
import os
import numpy as np
import operator
import random
import PIL.ImageFont
import PIL.ImageDraw
import sys  
from fileinput import filename

# For debugging:
import code

'''Make a row of the given width, from the given files, with the specified gap at the bottom, containing captions where found'''
def makeRow(files, totalWidth, hGapSize, vGapSize, font):
    # Sort the files into position order   
    files.sort(key=getPosition)
    
    # Load the pictures and calculate their width:height ratios
    originals = []
    ratios = []
    ratioTotal = 0.0
    for sourcefile in files:
        if not os.path.isfile(sourcefile):
            print "File " + sourcefile + " does not exist"
            # We'll carry on anyway
            # exit(-1)
        else:
            original = cv2.imread(sourcefile)
            if original is None:
                print "File " + sourcefile + " is not a valid picture"
	            # We'll carry on anyway
	            # exit(-1)
            else:
                # Store the picture
                originals.append(original)
                
                # Calculate its width as a ratio of its height
                ratio = getRatio(original)
                ratios.append(ratio)
                ratioTotal += ratio
    
    numPics = len(originals)
    #print "Read %d pictures for row:" % numPics
    if 0 == numPics:
        print "No pictures read.  Cannot make a row."
        return None
    
    # Calculate the amount of "gap" and therefore the total width of all pictures
    allGapsWidth = (numPics-1) * hGapSize
    allPicsWidth = totalWidth - allGapsWidth

    # Calculate the scaling factor: how much width each unit of ratio gets
    factor = allPicsWidth / ratioTotal
    #print factor

    # Special case: if we have only one image, simply resize it.
    # This avoid several edge-cases relating to rounding errors which are
    # otherwise lost in the "gaps".
    if 1 == numPics:
        newWidth = totalWidth
        newHeight = int( (newWidth / ratios[0]) + 0.5)
        resized = cv2.resize(original, (newWidth, newHeight))
        canvas = np.zeros((newHeight + vGapSize, totalWidth, 3), np.uint8)
        canvas = canvas + 255
        canvas[0:newHeight, 0:newWidth] = resized
        resizeds = [resized]    
        #print "Returning single-image row %d x %d" % (newWidth, newHeight)
    else:
        # Calculate the resulting height from the first picture, so as to ensure that
        # rounding errors don't cause slight variations in height
        # Scale each picture to the correct size
        original = originals[0]
        newWidth = int( (ratios[0] * factor) + 0.5 )
        newHeight = int( (newWidth / ratios[0]) + 0.5)
        #print "newHeight: %d" % newHeight
    
        # Resize each image to the desired size
        resizeds = []    
        for i in range(0, numPics):
            original = originals[i]
            newWidth = int( (ratios[i] * factor) + 0.5)
                        
            new = cv2.resize(original, (newWidth, newHeight))
            resizeds.append(new)
    
    
        # Create a new white canvas of the desired size. with a gap at the bottom
        canvas = np.zeros((newHeight + vGapSize, totalWidth, 3), np.uint8)
        canvas = canvas + 255
        
        # Copy each of the resized pictures into the new canvas
        xpos = 0
        # For all but the last, copy them according to the calculated position
        for i in range(0, numPics-1):
            width = resizeds[i].shape[1]
            canvas[0:newHeight, xpos:xpos+width] = resizeds[i]
            xpos += width + hGapSize
    
        # For the last, we can have small (~1 pixel) errors due to rounding.
        # Calculate the position from the right
        i = numPics-1
        width = resizeds[i].shape[1]
        canvas[0:newHeight, -(1+width):-1] = resizeds[i]
    
    # Generate the captions
    
    # A scratchpad "draw" which is "large enough" to use to measure text sizes
    dummyCanvas = PIL.ImageDraw.Draw(PIL.Image.new("RGB", (1000,1000), "white"))
    
    # Position the caption vertically in the space
    (w, h) = dummyCanvas.textsize("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!,", font)
    h = int(h*1.2)  # For some reason, the text is taller than its reported height
    textTopOffset = -int(h*0.2) # This is a fudge - draw the text a bit higher than 0,0 - don't really understand why

    print "text height %d, vGapSize %d" % (h, vGapSize)
    if h > vGapSize:
        print "Text renders taller than the vertical gap -- aborting"    
        exit(1)

    xOffset = 0
    for i in range(0, numPics):
        # TODO Heed position
        caption, junk, position = getCaptionRowAndPosition(files[i])

        # Create a PIL image of the correct size
        (w, dummyH) = dummyCanvas.textsize(caption, font)
        #print("Text size %d x %d" % (w, dummyH)) 
        pilImage = PIL.Image.new("RGB", (w, h), "white")
        pilDraw = PIL.ImageDraw.Draw(pilImage)
        pilDraw.text((0,textTopOffset), caption, font=font, fill=(0,0,0,255))
        cvImage = np.array(pilImage)
        xpos = max(xOffset + resizeds[i].shape[1] - w, 0)
        xpos = min(xpos, totalWidth - w)
        print("Xpos %d, w %d, h %d, shape %s" % (xpos, w, h, cvImage.shape))
        print("newHeight %d, textTopOffset %d, h %d" % (newHeight, textTopOffset, h))
        print("Canvas size w %d, h %d" % (canvas.shape[1], canvas.shape[0]))
        canvas[newHeight:newHeight+h, xpos:xpos+w] = cvImage
        xOffset += resizeds[i].shape[1] + hGapSize

    return canvas

''' Extract the caption, row and position from the filename '''
# The filename is expected to be of the following format:
#   [rr[-pp]] Caption.ext
# where rr is the row number
#       pp is the position (optional)
#       Caption is the caption to be drawn
#       ext is the file extension
def getCaptionRowAndPosition(filepath):
    # Get the filename part, without the extension
    filename, extension = os.path.splitext(os.path.split(filepath)[1])
    
    # If it starts with numbers, we have a row (and position?) section
    row = -1        # No row specified
    position = -1   # No position
    caption = ""
    if filename[0].isdigit():
        # Get the first part, e.g "10-01" or "10"
        row_pos = filename.split()[0]
        
        # The row is the first part, always
        row = int(row_pos.split("-")[0])
        
        # The position is the second part, if it exists
        if len(row_pos.split("-")) > 1:
            position = int(row_pos.split("-")[1])
        
        caption = filename.split(" ", 1)[1]
        #print "Split %s to get %s" % (filename, caption)
    else:
        caption = filename
    
    # Hacks to work around the oversize font:
    # 1. Prepend a space
    caption = " " + caption
    # 2. If the last four characters are NOT digits, append up to 4 digits
    #    Note: we could be cleverer about this and append fewer for smaller letters
    append = " "
    for i in range(-3, 0, 1):
        if not caption[i].isdigit():
            # Append 2 spaces if the non-digit is 3rd from the end,
            # or 3 if it is 3 from the end etc.
            append = " " * (i+5)
    caption = caption + append

    #print "Row %d, position %d, caption %s" % (row, position, caption)
    return caption, row, position

''' Get just the position in the row of a given file '''
def getPosition(filepath):
    caption, row, position = getCaptionRowAndPosition(filepath)
    return position

'''Get the total height of all the given image rows'''
def getTotalHeight(rows):
    totalHeight = 0
    for row in rows:
        totalHeight += row.shape[0]
    return totalHeight

'''Join several rows vertically to make a page'''
def joinRows(rows, targetHeight):
    # Calculate the total height of all the rows
    totalHeight = getTotalHeight(rows)
        
    # Calculate how much height we need to add to make the height equal the target
    remainingPadding = targetHeight - totalHeight
    print "Total padding: %d pixels over %d rows" % (remainingPadding, len(rows))
    if remainingPadding < 0:
        print "Rows are taller than the target: will not pad, and picture will be too tall!"
        remainingPadding = 0
    
    # Get the width - they should all be the same
    width = rows[0].shape[1]
    
    # Create blank white  canvas
    canvasHeight = max(targetHeight, totalHeight)
    canvas = np.zeros((canvasHeight, width, 3), np.uint8)
    canvas = canvas + 255
    
    # Place each row in turn
    ypos = 0
    remainingGaps = len(rows) - 1
    for row in rows:
        # Place the row itself
        height = row.shape[0]
        canvas[ypos:ypos+height, 0:width] = row
        ypos += height
        
        # Add any padding
        if remainingGaps > 0:
            padding = remainingPadding / remainingGaps
            ypos += padding
            remainingPadding -= padding
            remainingGaps -= 1
         
    return canvas

def getRatio(picture):
    w = picture.shape[1]
    h = picture.shape[0]
    ratio = 1.0 * w/h
    return ratio

'''Centre the given image on a page of the specified size (in pixels)'''
def centreOnPage(picture, width, height):
    # Create the page, all white
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas = canvas + 255
    
    # Calculate the offsets
    pictureW = picture.shape[1]
    leftOffset = (width - pictureW)/2
    
    pictureH = picture.shape[0]
    topOffset = (height - pictureH)/2
    
    # Position the picture on the page
    canvas[topOffset:topOffset+pictureH, leftOffset:leftOffset+pictureW] = picture
    return canvas

def makePage(sourcedir, image_w_mm, image_h_mm, h_gap_mm, v_gap_mm, dpi, fontfile, fontsize, page_w_mm, page_h_mm):
    print "Making image %dx%dmm from %s, gaps %fx%f, at %d DPI, font %s size %d on page %dx%dmm" % (image_w_mm, image_h_mm, sourcedir, h_gap_mm, v_gap_mm, dpi, fontfile, fontsize, page_w_mm, page_h_mm)

    # Inner frame is ~49x68cm
    # FRAME_W = 475.0
    # FRAME_H = 680.0

    # Calculate pixel sizes from page size and DPI
    pixelsPerMm = float(dpi) / 25.4
    image_width_px = int(image_w_mm * pixelsPerMm)
    # h_gap_pix = image_width_px / 143
    # v_gap_pix = image_width_px / 67
    h_gap_pix = int(h_gap_mm * pixelsPerMm)
    v_gap_pix = int(v_gap_mm * pixelsPerMm)
    #fontsize = image_width_px / 240 #175 #220
    print "h gap %f, v gap %f" % (h_gap_pix, v_gap_pix)
    #exit(-1)
        
    font = PIL.ImageFont.truetype(fontfile, fontsize)
    
    # Get a list of the files in the source directory
    sourceFiles = [os.path.join(sourcedir, f) for f in os.listdir(sourcedir) if os.path.isfile(os.path.join(sourcedir, f))]
    print "Found %d files" % len(sourceFiles)
    
    # Get their width:height ratios - stored as a dictionary (filename:ratio)
    imageRatios = {}
    print "Getting file aspect ratios..."
    for imageFile in sourceFiles:
        sys.stdout.write(".")   # Progress indicator
        image = cv2.imread(imageFile)
        # code.interact(local=locals())
        if image is None:
            print "Problem loading %s" % imageFile
            exit(-1)
        else:
            ratio = getRatio(image)
            if None == ratio:
                print "Problem getting ratio for %s" % imageFile
            else:
                imageRatios[imageFile] = ratio 
    
    print "\nGot ratios for %d files" % len(imageRatios)
    
    # Get a sorted list of files and ratios
    # Each item is a list containing the filename and the ratio, in that order
    sortedImages = sorted(imageRatios.items(), key=operator.itemgetter(1))
    
    # Create the rows
    rows = []
    
    # Option 1: take the smallest, largest, smallest
    if False:
        while len(sortedImages) > 0:
            print "There are %d pictures left" % len(sortedImages)
            # Get the smallest item, then the largest, then the smallest
            files = []
            item = sortedImages[0]  # A tuple containing the filename and the ratio
            files.append(item[0])   # Add the filename
            sortedImages.remove(item)
            
            if len(sortedImages) > 0:
                item = sortedImages[-1]
                files.append(item[0]) 
                sortedImages.remove(item)
        
            if len(sortedImages) > 0:
                item = sortedImages[0]
                files.append(item[0]) 
                sortedImages.remove(item)
        
            # Make these 3 items into a row
            row = makeRow(files, image_width_px, h_gap_pix, v_gap_pix, font)
            if None != row:
                rows.append(row)
    
    # Option 2: Random first, selected second, third etc
    #           Alternate rows fat/thin
    if False:
    #     RATIO_LOW = 5
    #     RATIO_MED =# Filename 8
    #     RATIO_HIGH = 16
        RATIO_LOW = 8
        RATIO_MED = 12
        RATIO_HIGH = 24
        
        # Generate 10 pictures
        numPics = 0;
        while numPics < 10:
            print("Starting picture %d" % numPics)
            rows = []
            abandon = False
            sortedImagesCopy = sortedImages[:]
            rowEven = True
            while len(sortedImagesCopy) > 0 and not abandon:
                rowEven = not rowEven
                if rowEven:
                    minRatio = RATIO_LOW
                    maxRatio = RATIO_MED
                else:
                    minRatio = RATIO_MED
                    maxRatio = RATIO_HIGH
                files = []
                item = random.choice(sortedImagesCopy)
                #print "Randomly chose %s" % item[0]
                sortedImagesCopy.remove(item)
                files.append(item[0])
                ratio = item[1]
                
                # Pick the widest available image giving us a ratio of not more than MAX_RATIO
                bestRatio = ratio
                while len(sortedImagesCopy) > 0:
                    bestItem = None
                    for candidate in sortedImagesCopy:
                        candiateRatio = candidate[1]
                        newRatio = ratio + candiateRatio
                        if newRatio > bestRatio and newRatio < maxRatio:
                            bestItem = candidate
                            bestRatio = newRatio
                            
                    if None == bestItem:
                        break
                    else:
                        #print "Best extra image: %s (ratio: %f)" % (bestItem[0], bestRatio)
                        files.append(bestItem[0])
                        sortedImagesCopy.remove(bestItem)
                        ratio = bestRatio
        
                # If we've got to here and don't have a large-enough ratio, abandon the picture
                if ratio < minRatio:
                    abandon = True
                    print("Abandoning picture %d" % numPics)
                    
                # Make this item (or these items) into a row
                row = makeRow(files, image_width_px, h_gap_pix, v_gap_pix, font)
                if None != row:
                    rows.append(row)
    
            if not abandon:
                # We have a workable picture.
                filename = "output%d.png" % numPics 
                print("Writing %s" % filename)
                # Build the page
                page = joinRows(rows)
                # Calculate the height (if width is == frame width)
                collageRatio = 1.0 * page.shape[1] / page.shape[0]
                collageHeight = image_w_mm / collageRatio
                print("Collage size: %d x %d (frame %d x %d)" % (image_w_mm, collageHeight, image_w_mm, image_h_mm) )
                cv2.imwrite(filename, page)
                numPics = numPics + 1
    
    # Option 3 (test): One picture per row
    if False:
        for item in sortedImages:
            print("---")
            print(item)
            print(item[0])
            files = [ item[0] ]
            row = makeRow(files, image_width_px, h_gap_pix, v_gap_pix, font)
            if None != row:
                rows.append(row)
    
    # Option 4: Prescribed rows
    #           Set the content of each row according to the filename - 1_, 2_ etc.
    if True:
        # Split the images into rows
        rowImages = {}
        #for item in sortedImages:
        for item in imageRatios:
            dummy, rowNum, junk = getCaptionRowAndPosition(item)
            
            # Put the filename into the right row in the dictionary
            if not rowImages.has_key(rowNum):
                rowImages[rowNum] = []
            #rowImages[rowNum].append(item[0])
            rowImages[rowNum].append(item)
        sortedRowImages = sorted(rowImages.iteritems())
        print "Sorted images into %d rows" % len(rowImages)
            
        print "Generating rows..."        
        rows = []
        for thisRowImages in sortedRowImages:
            print "Generating next row"
            row = makeRow(thisRowImages[1], image_width_px, h_gap_pix, v_gap_pix, font)
    
            if row is not None:
                rows.append(row)
        print "%d rows generated" % len(rows)
    
    # Calculate the total height
    totalHeight = getTotalHeight(rows)
    print "Total size of all rows: %d x %d - average row height %d pixels" % (image_width_px, totalHeight, totalHeight/len(rows))
    
    # Show some stats about how this fits into one or two frames
    frameRatio = image_w_mm / image_h_mm
    targetHeight = int(image_width_px / frameRatio)
    print "Target is %d x %d (one frame) or %d x %d (two frames)" % (image_width_px, targetHeight, image_width_px, 2*targetHeight)
    
    # Create the final page by joining all the rows
    print "Joining rows..."
    if 0 == len(rows):
        print "No rows generated.   Cannot generate a page."
    else:
        page = joinRows(rows, targetHeight)

        # Set the picture in the centre of a larger page, for printing
        pageWidthPixels = int(page_w_mm * pixelsPerMm)
        pageHeightPixels = int(page_h_mm * pixelsPerMm)
        
        print "Centring on page of %d x %d pixels" % (pageWidthPixels, pageHeightPixels)
        pageWithBorder = centreOnPage(page, pageWidthPixels, pageHeightPixels)
        
        # Output the result
        outputFilename = sourcedir.replace("/", "_").replace(".", "_") + "_output.png"
    #     cv2.startWindowThread()
    #     cv2.namedWindow("Result")
    #     cv2.imshow("Result", page)
        print "Writing output file %s" % outputFilename
        cv2.imwrite(outputFilename, pageWithBorder)
        #cv2.imwrite(outputFilename, page)
        print "Done\n\n"

# Entry Point

# Read the parameters from the command line
if len(sys.argv) != 11:
	executable = sys.argv[0]
	print "Usage:\n %s ImageSourceDir InnerFrameWidth(mm) InnerFrameHeight(mm) HorizontalGap(mm) MinVerticalGap(mm) DPI FontFile FontSize OuterFrameWidth(mm) OuterFrameHeight(mm)" % executable
	exit(-1)
sourceDir = sys.argv[1]
innerFrameWidth = float(sys.argv[2])
innerFrameHeight = float(sys.argv[3])
horizGap = float(sys.argv[4])
vertGap = float(sys.argv[5])
dpi = int(sys.argv[6])
fontFile = sys.argv[7]
fontSize = int(sys.argv[8])
outerFrameWidth = float(sys.argv[9])
outerFrameHeight = float(sys.argv[10])

# Make the page
makePage(sourceDir, innerFrameWidth, innerFrameHeight, horizGap, vertGap, dpi, fontFile, fontSize, outerFrameWidth, outerFrameHeight)
#makePage("/home/mark/Development/PanoramaBoard/SourceFiles_Test", 300, "SCRIPTIN.ttf")
#makePage("/home/mark/Scratch/Panoramas/2_oriented")
#makePage("/home/mark/Development/PanoramaBoard/SourceFiles_Page1", 300, "SCRIPTIN.ttf")
#makePage("/home/mark/Scratch/Panoramas/SourceFiles_Page2", 300)
