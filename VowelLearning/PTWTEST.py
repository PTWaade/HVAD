import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import random



#### Settings ####

symboltype = "IPA"
#symboltype = "geometric"

target_idx = 6

prefix_green = "Symbols/" + symboltype + "_" + "green" + "/"
prefix_grey = "Symbols/" + symboltype + "_" + "grey" + "/"



def getImage(path):
    return OffsetImage(plt.imread(path), zoom=0.4)

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

x = random.sample(range(0, 20), 11)
y = random.sample(range(0, 20), 11)

idxs = [0,1,2,3,4,5,6,7,8,9,10]

fig, ax = plt.subplots()
ax.scatter(x, y, color = "white") 

for idx, x0, y0, path in zip(idxs, x, y, paths):
    if idx == target_idx:
        ab = AnnotationBbox(getImage(prefix_green + path), (x0, y0), frameon=False)
    else:
        ab = AnnotationBbox(getImage(prefix_grey + path), (x0, y0), frameon=False)
    
    ax.add_artist(ab)


