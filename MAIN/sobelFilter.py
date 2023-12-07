# -*- coding: utf-8 -*- 
"""
Created on Fri Nov 24 14:03:46 2023

@author: creek
"""
from PIL import Image, ImageEnhance
import numpy as np
imageName = "tylerAndI"
image = "tylerAndI.png" #the name of the image file
grayscale = False
outlined = True

"""
import wx

class MyFrame(wx.Frame):    
    def __init__(self):
        super().__init__(parent=None, title='Hello World')
        panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(panel, pos=(5, 5))
        self.Show()

if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
"""

#dither patterns go here
floyd = [[0, 0, 0],
         [0, 0, (7/16)],
         [(3/16), (5/16),(1/16)]]

wave = [[0, 0, 0],
         [0, 0, (2/12)],
         [(6/16), (3/16), (9/16)]]

atkinson = [[0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, (1/8), (1/8)],
            [0, (1/8), (1/8), (1/8), 0],
            [0, 0, (1/8), 0, 0]]

#sobel settings
threshold = 1000000 # around 175-225 is usually good
edgeColor = (82, 46, 10) #64,255,214 for a nice light teal
img = Image.open(image).convert("RGB")
w,h = img.size
imgGray = img.convert('L')
blur = ImageEnhance.Sharpness(imgGray)
newImg = blur.enhance(0.2)
newImg.show() #the blurred image for sobel filter
img_arr = np.asarray(newImg)

#posterize settings
post_img_array = np.asarray(newImg)
"""
colors = [[53, 212, 188],
          [54, 224, 207],
          [41, 171, 158],
          [29, 122, 113],
          [19, 79, 73],
          [9, 36, 33],
          [0, 0, 0]] #list of colors to posterize to from bright to dark
"""
colors = [[176, 152, 132],
          [128, 100, 69],
          [110, 84, 56],
          [74, 52, 27],
          [48, 25, 6]] #list of colors to posterize to from bright to dark

invert = False
rangeChunk = 255/len(colors)#The size of the range for each color in the list

#dither settings / create the error matrix that is the same size as the image, and fill with zero
ditherMode = "wave" # wave, floyd, or atkinson
errorMatrix = []
errorRow = []
for i in range(0, h):
    for n in range(0, w):
        errorRow.append(0)
    errorMatrix.append(errorRow)
    errorRow = []
    
"""
takes the img array and applies the sobel filter to the given coordinates, it returns the 
expected luminance value at that coord for hte vertical filter
"""
def getPixelValueFromSobelVert(img, xCoord, yCoord):
    
    sobelFilter = [[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]]
    compareSample = [[0, 0, 0],
                     [0, 0, 0],
                     [0, 0, 0]]
    
    countX = 0
    countY = 0
    for i in range(yCoord - 1, yCoord + 2):
        countX = 0
        for n in range(xCoord -1, xCoord +2):
            try:
                compareSample[countY][countX] = int(img.getpixel((i, n)))
            except:
                compareSample[countY][countX] = 0
            countX += 1
        countY += 1
    
    tempSum = 0
    for i in range(0, 3):
        for n in range(0, 3):
            tempSum += compareSample[i][n] * sobelFilter[i][n]
            
    return tempSum           

"""
takes the img array and applies the sobel filter to the given coordinates, it returns the 
expected luminance value at that coord for hte horizontal filter
"""
def getPixelValueFromSobelHoriz(img_arr, xCoord, yCoord):

    sobelFilter = [[1, 2, 1],
                   [0, 0, 0],
                   [-1, -2, -1]]
    compareSample = [[0, 0, 0],
                     [0, 0, 0],
                     [0, 0, 0]]
    
    countX = 0
    countY = 0
    for i in range(yCoord - 1, yCoord + 2):
        countX = 0
        for n in range(xCoord -1, xCoord + 2):
            try:
                compareSample[countY][countX] = int(img.getpixel((i, n)))
            except:
                compareSample[countY][countX] = 0
            countX += 1
        countY += 1
        
    tempSum = 0
    for i in range(0, 3):
        for n in range(0, 3):
            tempSum += (compareSample[i][n] * sobelFilter[i][n])
            
    return tempSum
            


"""
takes the img_arr and some defined coords and decides what the magnitude of the value is
based off of the two sobel filters, this can then be used with our threshold to determine edges
"""
def getPixelMagnitude(img, xCoord, yCoord):
    vertIntensity = getPixelValueFromSobelVert(img, xCoord, yCoord)
    horiIntensity = getPixelValueFromSobelHoriz(img, xCoord, yCoord)
    temp = abs(vertIntensity) + abs(horiIntensity) #faster than getting a square root
    temp = abs(temp)
    #print(temp)
    return temp

def isPixelAnEdge(img, xCoord, yCoord, threshold):
    mag = getPixelMagnitude(img, xCoord, yCoord)
    if mag > threshold:
        return True
    return False

"""
adjusts the img so that it matches the dither pattern and readjusts surrounding pixels
"""
def ditherError(img, xCoord, yCoord, color):  
    
    #dither patterns are defined at the top
    
    boundMin = 0 # 1 for 5*5
    boundMax = 1 # 2 for 5*5
    
    if (ditherMode == "floyd"):
        matrixToBeUsed = floyd
    elif (ditherMode == "wave"):
        matrixToBeUsed = wave
    elif (ditherMode == "atkinson"):
        matrixToBeUsed = atkinson
        boundMin = 2
        boundMax = 2
    else:
        matrixToBeUsed = floyd
        
    #print(matrixToBeUsed)
    
    matrixToBeUsed = wave #use this to dynamically adjust the filter settings later
    intendedColor = post_img_array[xCoord][yCoord]
    postColor = (0.2126 * color[0]) + (0.7152 * color[1]) + (0.0722 * color[2])
    dif = intendedColor - postColor
    if xCoord > boundMin and xCoord < h - boundMax: # within bounds
        if yCoord > boundMin and yCoord < w - boundMax:
            errorMatrix[xCoord][yCoord] += dif
            if boundMin != 1: # 3x3 matrix
                errorMatrix[xCoord+1][yCoord] += matrixToBeUsed[1][2] * dif
                errorMatrix[xCoord-1][yCoord+1] += matrixToBeUsed[2][0] * dif
                errorMatrix[xCoord][yCoord+1] += matrixToBeUsed[2][1] * dif
                errorMatrix[xCoord+1][yCoord+1] += matrixToBeUsed[2][2] * dif 
            if boundMin == 1: # 5x5 matrix
                #middle row
                errorMatrix[xCoord][yCoord-2] += matrixToBeUsed[2][0] * dif
                errorMatrix[xCoord][yCoord-1] += matrixToBeUsed[2][1] * dif
                errorMatrix[xCoord][yCoord+1] += matrixToBeUsed[2][3] * dif
                errorMatrix[xCoord][yCoord+2] += matrixToBeUsed[2][4] * dif
                #second to bottom
                errorMatrix[xCoord+1][yCoord-2] += matrixToBeUsed[3][0] * dif
                errorMatrix[xCoord+1][yCoord-1] += matrixToBeUsed[3][1] * dif
                errorMatrix[xCoord+1][yCoord] += matrixToBeUsed[3][2] * dif
                errorMatrix[xCoord+1][yCoord+1] += matrixToBeUsed[3][3] * dif
                errorMatrix[xCoord+1][yCoord+2] += matrixToBeUsed[3][4] * dif
                #bottom
                errorMatrix[xCoord+2][yCoord-2] += matrixToBeUsed[4][0] * dif
                errorMatrix[xCoord+2][yCoord-1] += matrixToBeUsed[4][1] * dif
                errorMatrix[xCoord+2][yCoord] += matrixToBeUsed[4][2] * dif
                errorMatrix[xCoord+2][yCoord+1] += matrixToBeUsed[4][3] * dif
                errorMatrix[xCoord+2][yCoord+2] += matrixToBeUsed[4][4] * dif
    return
        

def getPostVal(post_img_array, xCoord, yCoord):
    colorToPost = post_img_array[xCoord][yCoord] #the brightness of the color
    colorToPost += errorMatrix[xCoord][yCoord]
    if colorToPost > 255:
        colorToPost = 255
    elif colorToPost < 0:
        colorToPost = 0
    color = (int(colorToPost/rangeChunk)) - 1 #floor divide to get the color
    if invert:
        color = colors[color]
    else:
        if colorToPost < rangeChunk:
            color = colors[-1]
        else:
            color = colors[-(color + 1)]
    ditherError(post_img_array, xCoord, yCoord, color) #adjust the errorMatrix
    #print(color)
    #dither here
    return (color[0], color[1], color[2])

def main():
    postReturn = Image.open(image).convert("RGB")
    print(w, h)
    print("calculating Posterization and Dither...")
    for i in range(0, h):
        for n in range(0, w):
            postReturn.putpixel((n, i), getPostVal(post_img_array, i, n))
        #print ( str(i) + " out of " + str(h)  + " rows done")
        
    print("Posterization and Dither: Done")
    postReturn.show()
    
    #imgGray = postReturn.convert('L')
    if (outlined):
        print("calculatingSobel...")
        for i in range(1, h-1):
            for n in range(1, w-1):
                isEdge = isPixelAnEdge(newImg, i, n, threshold)
                if isEdge:
                    postReturn.putpixel((n, i), edgeColor)
            print ( str(i) + " out of " + str(h)  + " rows done")    
                    
        print("Sobel: Done")
        if (grayscale):
            postReturn = postReturn.convert('L')
        postReturn.show()
    
    #save the file
    filename = "dithered_" + imageName
    path = "output/" + filename + ".png"
    finalReturn = postReturn.resize((20 * w, 20 * h)) #only use this if using low res image
    finalReturn.save(path)
            
main()
