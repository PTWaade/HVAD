import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import random

#### Settings ####

#Type of symbols
symboltype = "IPA"
#symboltype = "geometric"

#Which is the target
target_idx = 6

#How much to zoom the pictures
zoom = 0.4

#Set the paths to the images
prefix_green = "Symbols/" + symboltype + "_" + "green" + "/"
prefix_grey = "Symbols/" + symboltype + "_" + "grey" + "/"


#Make function for getting the image (used by matplotlib)
def getImage(path):
    return OffsetImage(plt.imread(path), zoom=zoom)

#Names of the pictures
paths = [
    '1.png',
    '2.png',
    '3.png',
    '4.png',
    '5.png',
    '6.png',
    '7.png',
    '8.png',
    '9.png',
    '10.png',
    '11.png']

#Create random x and y coordinates
x = random.sample(range(0, 20), 11)
y = random.sample(range(0, 20), 11)

#These are the indeces for each picture
idxs = [0,1,2,3,4,5,6,7,8,9,10]

#Make a figure
fig, ax = plt.subplots()
#Add the points, color them white
ax.scatter(x, y, color = "white") 

#Go through each coordinate, the indices, and the picture names together
for idx, x0, y0, path in zip(idxs, x, y, paths):
    #If the idx is the target
    if idx == target_idx:
        #Create the green image on with the given coordinates
        ab = AnnotationBbox(getImage(prefix_green + path), (x0, y0), frameon=False)
    #Otherwise
    else:
        #Make it grey
        ab = AnnotationBbox(getImage(prefix_grey + path), (x0, y0), frameon=False)
    
    #And add the picture to the plot
    ax.add_artist(ab)


