import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pandas as pd
import statistics as stat

path = os.path.dirname(os.path.abspath(__file__))+"/" 

data = pd.read_csv(path + "data/formant_data.csv")
pd.head(data)
f1f3_avgs = []
f2f3_avgs = []
for i in range(11):
    x = i + 1
    sub = data[data.vowel == x]
    f1f3 = stat.mean(sub["f1/f3"].tolist())
    f2f3 = stat.mean(sub["f2/f3"].tolist())
    f1f3_avgs.append(f1f3)
    f2f3_avgs.append(f2f3)



#### Settings ####

#Type of symbols
symboltype = "IPA"
#symboltype = "geometric"

#Which is the target
#target_idx = 1

#How much to zoom the pictures
zoom = 0.3

#Set the paths to the images
prefix_green = "img/" + symboltype + "_green/"
prefix_grey = "img/" + symboltype + "_grey/"


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

#These are the indeces for each picture
idxs = [0,1,2,3,4,5,6,7,8,9,10,100]

for v in idxs:
    target_idx = v 
    #Make a figure
    fig, ax = plt.subplots()
    #Add the points, color them white
    ax.scatter(f1f3_avgs, f2f3_avgs, color = "white") 

    #Go through each coordinate, the indices, and the picture names together
    for idx, x0, y0, p in zip(idxs, f1f3_avgs, f2f3_avgs, paths):
        #If the idx is the target
        if idx == target_idx:
            #Create the green image on with the given coordinates
            ab = AnnotationBbox(getImage(path + prefix_green + p), (x0, y0), frameon=False)
        #Otherwise
        else:
            #Make it grey
            ab = AnnotationBbox(getImage(path + prefix_grey + p), (x0, y0), frameon=False)
        
        #And add the picture to the plot
        ax.add_artist(ab)

    ax.axis([0.09,0.22,0.3,0.9])
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)

    fig.savefig(path + "img/" + symboltype + "_plots/" + str(target_idx+1))
    fig.clf()

