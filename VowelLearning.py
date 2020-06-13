import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import wave
import time
import parselmouth
import simpleaudio as sa
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageTk
import random
import statistics as stat
import pandas as pd
import os
from shapely.geometry import MultiPoint
from descartes.patch import PolygonPatch
import glob


# class that altenates between displaying recording message and blank space
# Each time it is initiated
class message:
    outputs = ["⦿ Recording", "                     "]
    n = 0
    def __init__(self):
        instr['text'] = self.outputs[self.n]

        if self.n == len(self.outputs)-1:
            message.n = 0
        else:
            message.n = self.n + 1
    # END FUNCTION
# END CLASS

# Class that contains the main functionality of HVAD
#   - Recording and storing sound
#   - Formant analysis
#   - Generating and showing plot (formant space), with user feedback
class schwa:

    ###################
    # Class variables #
    ###################
    path = os.path.dirname(os.path.abspath(__file__))+"/"

    seconds = 1 # number of seconds to record

    device_index = 3 # CLO = 3, MMI = ?

    # Formant data for plotting icons in foprmant space 
    data = pd.read_csv(path + "data/formant_data.csv") # Load data

    f1f3_avgs = []
    f2f3_avgs = []
    f1_avgs = []
    f2_avgs = []

    # Containers for the ratio values of user signal
    F_ratio1 = 0
    F_ratio2 = 0
    
    F1 = 0
    F2 = 0
    F3 = 0


    scale = "freq"

    sex_show = "all"
    
    # Value that controls wether to show error message in plot
    noisy = False


    ###############
    ## FUNCTIONS ##
    ###############

    # Function that records sound for the amount of seconds set above
    # The wav file is stored in the audio folder as sound.wav
    def record(self):
        CHUNK = 2048 # number of data points to read at a time
        RATE = 44100 # Sample rate

        # Initiating PyAudio and start stream (recording)
        p=pyaudio.PyAudio() 
        stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
                    frames_per_buffer=CHUNK, input_device_index=self.device_index) # Remove input_device_index=3 to use computer mic

        frames = []
        # Store data in chunks for self.seconds number of seconds
        for i in range(0, int(RATE / CHUNK * self.seconds)):
            data = stream.read(CHUNK)
            frames.append(data)

        # Stop and close the stream 
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        p.terminate()

        # Store the wav file in the audio folder as sound.wav
        wf = wave.open(self.path + "audio/sound.wav", 'wb')
        wf.setnchannels(1) # mono 
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) # match sample size
        wf.setframerate(RATE) # match frame rate
        wf.writeframes(b''.join(frames)) # put the recorded audio data into the file
        wf.close()
    # END FUNCTION

    # Function that makes formant anlysis
    def formants(self):
        sound = parselmouth.Sound(self.path + "audio/sound.wav") # load the recorded sound
        formants = sound.to_formant_burg() # Extract formants across the whole file

        # Extract the three first formants at 100 time points equally spaced out across the file
        # Starting 0.1 seconds into the file and ending 0.1 seconds before the end of the file
        # The formant values from the 100 time steps are stored in the lists below
        F1_list = []
        F2_list = []
        F3_list = []
        for t in np.linspace(0.1, self.seconds-0.1, num=100):
            F1_list.append(formants.get_value_at_time(1,t))
            F2_list.append(formants.get_value_at_time(2,t))
            F3_list.append(formants.get_value_at_time(3,t))
        
        # Variance analysis - Finding the the vowel at a stable point
        # Looping through formant lists (made above) and analysing a window of time points
        # The variance of the time points in the  window is stored for for each formant in lists
        # Then each time step of these lists are summed together across lists
        # The minimum variance window is the most stable point of the vowel.
        w_size = 5 # window size
        F1_var_list = []
        F2_var_list = []
        #F3_var_list = []

        # Loop though formant lists
        for w in range(len(F1_list)-w_size):

            #Determine window
            F1_window = F1_list[w:w+w_size] 
            F2_window = F2_list[w:w+w_size] 
            #F3_window = F3_list[w:w+w_size]

            # Compute variance - log is used to normalize the values
            F1_var_list.append(
                stat.variance(np.log(F1_window)) / stat.mean(np.log(F1_window))
                )
            F2_var_list.append(
                stat.variance(np.log(F2_window)) / stat.mean(np.log(F2_window))
            )
            #F3_var_list.append(np.log(stat.variance(F3_window)))
        
        # Loop though windows and make variance sums
        # F3 is down weighted a bit, for balance, as it is typically higher
        varSum_list = []
        for i in range(len(F1_var_list)):
            varSum = F1_var_list[i] + F2_var_list[i]
            varSum_list.append(varSum)

        # find the minimum variance window and save its index
        index = varSum_list.index(min(varSum_list))
        
        # The mean formant values of the minimum variance window is the user formants
        F1 = stat.mean(F1_list[index:index+w_size])
        F2 = stat.mean(F2_list[index:index+w_size])
        F3 = stat.mean(F3_list[index:index+w_size])

        # Make formant ratios and store them in the class variables.
        schwa.F1 = F1
        schwa.F2 = F2

        schwa.F_ratio1 = F1/F3
        schwa.F_ratio2 = F2/F3

        print(F1_var_list[index]*1000000)
        print(F2_var_list[index]*1000000)


        # If the variance is two high the signal is two noisy
        # VARIANCE THRESHOLDS ARE SET SEMI RANDOMLY - NEEDS MORE TESTING
        if (F1_var_list[index]*1000000>30)|(F2_var_list[index]*1000000>30):
            schwa.noisy = True
        else:
            schwa.noisy = False
    # END FUNCTION

    # Update function for updating the data before plotting
    def data_update(self):
        
        schwa.data = pd.read_csv(self.path + "data/formant_data.csv") # Load data
        schwa.data = schwa.data[schwa.data.cut==0] 
        schwa.f1f3_avgs = []
        schwa.f2f3_avgs = []
        schwa.f1_avgs = []
        schwa.f2_avgs = []

        if self.sex_show == "female":
            schwa.data = schwa.data[schwa.data.sex=="f"] 
        if self.sex_show == "male":
            schwa.data = schwa.data[schwa.data.sex=="m"]
        vs = [1,2,3,4,5,6,7,10]
        for i in vs:
            sub = schwa.data[schwa.data.vowel == i]
            f1f3 = stat.mean(sub["f1/f3"].tolist())
            f2f3 = stat.mean(sub["f2/f3"].tolist())
            schwa.f1f3_avgs.append(f1f3)
            schwa.f2f3_avgs.append(f2f3)
        
        for i in vs:
            sub = schwa.data[schwa.data.vowel == i]
            f1 = stat.mean(sub["f1"].tolist())
            f2 = stat.mean(sub["f2"].tolist())
            schwa.f1_avgs.append(f1)
            schwa.f2_avgs.append(f2)
 
    #Function for getting the images (used by in the plot function below)   
    def getImage(self, path, zoom):
        return OffsetImage(plt.imread(path), zoom=zoom)

    # Function that generates the right plot and shows it in the interface
    # The reset option is used to remove user stuff while recording (primarily to remove error message)
    def plot(self, reset = False):
        self.data_update()
        # Reset option
        if reset:
            # DO STUFF HERE
            print("---")
        # If not not reset option
        else: 
            # Type of symbols
            if rep.r == "GEO":
                symboltype = "geometric"
            else:
                symboltype = "IPA"

            # Index of target vowel
            target_idx = select_vowel.vowel-1

            # How much to zoom the pictures
            zoom = 0.4

            # Set the paths to the images
            prefix_green = "img/" + symboltype + "_green/"
            prefix_grey = "img/" + symboltype + "_grey/"

            # Names of the pictures
            """
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
            """
            paths = [
                '1.png',
                '2.png',
                '3.png',
                '4.png',
                '5.png',
                '6.png',
                '7.png',
                '10.png']
            # These are the indeces for each picture
            #idxs = [0,1,2,3,4,5,6,7,8,9,10]
            idxs = [0,1,2,3,4,5,6,9,]

            if self.scale == "ratio":
                y = self.f1f3_avgs
                x = self.f2f3_avgs
            else:
                y = self.f1_avgs
                x = self.f2_avgs

            # Make a figure
            fig, ax = plt.subplots()
            # Add the points, color them white
            ax.scatter(x, y, color = "white") 

            # If the class variable noisy is true, just display error message
            if self.noisy:
                schwa.F1 == 0
                ax.text(1800, 730, "Attention: Analysis unreliable", size=10, rotation=0,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round",
                        ec=(1., 0.5, 0.5),
                        fc=(1., 0.8, 0.8),
                        )
                )

            # If the class variable noisy is false, proceed with plotting  
            else:
                # Go through each coordinate, the indices, and the picture names together
                for idx, x0, y0, p in zip(idxs, x, y, paths):
                    # If the idx is the target
                    if idx == target_idx:
                        
                        # Create the green image on with the given coordinates
                        ab = AnnotationBbox(self.getImage(self.path + prefix_green + p, zoom), (x0, y0), frameon=False)
                    # Otherwise
                    else:
                        # Make it grey
                        ab = AnnotationBbox(self.getImage(self.path + prefix_grey + p, zoom), (x0, y0), frameon=False)
                    
                    # And add the picture to the plot
                    ax.add_artist(ab)

                colors = ["#FF5733", "#2E7D32", "#FB8C00", "#1565C0", "#EED918", "#F571C4", "#9575CD", "#1565C0", "#2E7D32", "#AF601A", "#6D4C41"]
        
                if select_vowel.vowel == 0:
                    #for v in [1,2,3,4,5,6,7,8,9,10,11]:
                    for v in [1,2,3,4,5,6,7,10]:
                        v_data = schwa.data[schwa.data.vowel == v]
                        if self.scale == "ratio":
                            destr_f1f3 = v_data["f1/f3"].tolist()
                            destr_f2f3 = v_data["f2/f3"].tolist()
                            #ax.scatter(destr_f1f3, destr_f2f3, color = colors[v-1])
                            
                            if len(destr_f1f3)>2:
                                xy_list = []
                                for i in range(len(destr_f1f3)):
                                    xy = (destr_f1f3[i], destr_f2f3[i])
                                    xy_list.append(xy)
                                points = MultiPoint(xy_list)
                                hull = points.convex_hull
                                patch = PolygonPatch(hull, alpha=0.3, zorder=2, edgecolor=colors[v-1], facecolor=colors[v-1])
                                ax.add_patch(patch)
                        else:    
                            destr_f1 = v_data["f1"].tolist()
                            destr_f2 = v_data["f2"].tolist()
                            #ax.scatter(destr_f2, destr_f1, color = colors[v-1])
                            
                            if len(destr_f1)>2:
                                xy_list = []
                                for i in range(len(destr_f1)):
                                    xy = (destr_f2[i], destr_f1[i])
                                    xy_list.append(xy)

                                points = MultiPoint(xy_list)
                                hull = points.convex_hull
                                patch = PolygonPatch(hull, alpha=0.3, zorder=2, edgecolor=colors[v-1], facecolor=colors[v-1])
                                ax.add_patch(patch)
                else:
                    v = select_vowel.vowel
                    v_data = self.data[self.data.vowel == v]
                    if self.scale == "ratio":
                        destr_f1f3 = v_data["f1/f3"].tolist()
                        destr_f2f3 = v_data["f2/f3"].tolist()
                        #ax.scatter(destr_f2f3, destr_f1f3)
                        if len(destr_f1f3)>2:
                            xy_list = []
                            for i in range(len(destr_f1f3)):
                                xy = (destr_f1f3[i], destr_f2f3[i])
                                xy_list.append(xy)
                            points = MultiPoint(xy_list)
                            hull = points.convex_hull
                            patch = PolygonPatch(hull, alpha=0.3, zorder=2, edgecolor=colors[v-1], facecolor=colors[v-1])
                            ax.add_patch(patch)
                    else:    
                        destr_f1 = v_data["f1"].tolist()
                        destr_f2 = v_data["f2"].tolist()
                        #ax.scatter(destr_f2, destr_f1)
                        if len(destr_f1)>2:
                            xy_list = []
                            for i in range(len(destr_f1)):
                                xy = (destr_f2[i], destr_f1[i])
                                xy_list.append(xy)

                            points = MultiPoint(xy_list)
                            hull = points.convex_hull
                            patch = PolygonPatch(hull, alpha=0.3, zorder=2, edgecolor=colors[v-1], facecolor=colors[v-1])
                            ax.add_patch(patch)
                    

                # The user formant ratios from recording, marked with an X
                if self.F1 != 0:
                    if self.scale == "ratio":
                        y = self.F_ratio1
                        x = self.F_ratio2
                    else:
                        y = self.F1
                        x = self.F2
                    ax.scatter(x, y, s=50, marker = "X", c="black")
            

            # Set axis limits
            # Set axis limits
            if self.scale == "ratio":
                ax.axis([0.02,0.3,0,1]) 
            else:
                if ((self.F1 < 700) & (self.F1 > 150) & (self.F2 < 2900) & (self.F2 > 750)):
                    ax.axis([2900,750,700,150])
                else:
                    ax.axis([3000,400,1000,100])
                if self.F1 == 0:
                    ax.axis([2900,750,700,150])
                if self.noisy:
                    ax.axis([2900,750,700,150])

            # Remove ticks and tick labels
            ax.axes.xaxis.set_visible(False)
            ax.axes.yaxis.set_visible(False)

            # Save the plot in the img folder as plot.png
            fig.savefig(self.path + "img/plot.png")

            # Clear the plot (make ready for new plot)
            fig.clf()

            # Display the plot in the interface
            window.plot = ImageTk.PhotoImage(Image.open(self.path + "img/plot.png"))
            plot_show.configure(image=window.plot)
    # END FUNCTION
# END CLASS

# Class that manages selected vowels
class select_vowel:

    # The current selected vowel
    vowel = 0
    # Container for rep folder path
    folder = ""

    # Function that resets all buttons to grey (used when selecting new vowel, before making that green)
    def reset_buttons(self):
        # set the rigth folder path
        if rep.r == "GEO":
            select_vowel.folder = "img/geometric_"
        else:
            select_vowel.folder = "img/IPA_"
        
        # Store all the button images
        window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/1.png"))
        window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/2.png"))
        window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/3.png"))
        window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/4.png"))
        window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/5.png"))
        window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/6.png"))
        window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/7.png"))
        window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/8.png"))
        window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/9.png"))
        window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/10.png"))
        window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "grey/11.png"))

        # Update the buttons in the interface
        v_button1.configure(image=window.v1)
        v_button2.configure(image=window.v2)
        v_button3.configure(image=window.v3)
        v_button4.configure(image=window.v4)
        v_button5.configure(image=window.v5)
        v_button6.configure(image=window.v6)
        v_button7.configure(image=window.v7)
        v_button8.configure(image=window.v8)
        v_button9.configure(image=window.v9)
        v_button10.configure(image=window.v10)
        v_button11.configure(image=window.v11)
    # END FUNCTION

    # The 11 functions each dedicated to a vowel button
    # They rest the buttons to grey, change the selected vowel and make that green
    # Both on the button and in the plot
    def v1(self):
        self.reset_buttons()
        select_vowel.vowel = 1
        window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/1.png"))
        v_button1.configure(image=window.v1)
        schwa().plot()
    def v2(self):
        self.reset_buttons()
        select_vowel.vowel = 2
        window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/2.png"))
        v_button2.configure(image=window.v2)
        schwa().plot()
    def v3(self):
        self.reset_buttons()
        select_vowel.vowel = 3
        window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/3.png"))
        v_button3.configure(image=window.v3)
        schwa().plot()
    def v4(self):
        self.reset_buttons()
        select_vowel.vowel = 4
        window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/4.png"))
        v_button4.configure(image=window.v4)
        schwa().plot()
    def v5(self):
        self.reset_buttons()
        select_vowel.vowel = 5
        window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/5.png"))
        v_button5.configure(image=window.v5)
        schwa().plot()
    def v6(self):
        self.reset_buttons()
        select_vowel.vowel = 6
        window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/6.png"))
        v_button6.configure(image=window.v6)
        schwa().plot()
    def v7(self):
        self.reset_buttons()
        select_vowel.vowel = 7
        window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/7.png"))
        v_button7.configure(image=window.v7)
        schwa().plot()
    def v8(self):
        self.reset_buttons()
        select_vowel.vowel = 8
        window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/8.png"))
        v_button8.configure(image=window.v8)
        schwa().plot()
    def v9(self):
        self.reset_buttons()
        select_vowel.vowel = 9
        window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/9.png"))
        v_button9.configure(image=window.v9)
        schwa().plot()
    def v10(self):
        self.reset_buttons()
        select_vowel.vowel = 10
        window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/10.png"))
        v_button10.configure(image=window.v10)
        schwa().plot()
    def v11(self):
        self.reset_buttons()
        select_vowel.vowel = 11
        window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/11.png"))
        v_button11.configure(image=window.v11)
        schwa().plot()
    
    def reset_vowel(self):
        select_vowel.vowel = 0
        self.reset_buttons()
        schwa().plot()
    # END OF THE 11 FUNCTION
# END CLASS

# Class that manages the representation (Geometric/IPA)
class rep:

    # The current representation
    r = "GEO"

    # Function dedicated to the "Change representation" button
    # It changes the r value in this class and all the buttons and the plot accordingly
    def change_rep(self):

        # Change the r value to the other rep
        if self.r == "GEO":
            rep.r = "IPA"
        else: 
            rep.r = "GEO"

        # Set the path prefix according to the rep
        if self.r == "GEO":
            folder = "img/geometric_"
        else:
            folder = "img/IPA_"

        # Make all buttons grey
        window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/1.png"))
        window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/2.png"))
        window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/3.png"))
        window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/4.png"))
        window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/5.png"))
        window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/6.png"))
        window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/7.png"))
        window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/8.png"))
        window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/9.png"))
        window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/10.png"))
        window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "grey/11.png"))
        
        # Make the target vowel green
        if select_vowel.vowel == 1:
            window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/1.png"))
        if select_vowel.vowel == 2:
            window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/2.png"))
        if select_vowel.vowel == 3:
            window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/3.png"))
        if select_vowel.vowel == 4:
            window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/4.png"))
        if select_vowel.vowel == 5:
            window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/5.png"))
        if select_vowel.vowel == 6:
            window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/6.png"))
        if select_vowel.vowel == 7:
            window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/7.png"))
        if select_vowel.vowel == 8:
            window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/8.png"))
        if select_vowel.vowel == 9:
            window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/9.png"))
        if select_vowel.vowel == 10:
            window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/10.png"))
        if select_vowel.vowel == 11:
            window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + folder + "green/11.png"))
        
        # Update the buttons in the interface
        v_button1.configure(image=window.v1)
        v_button2.configure(image=window.v2)
        v_button3.configure(image=window.v3)
        v_button4.configure(image=window.v4)
        v_button5.configure(image=window.v5)
        v_button6.configure(image=window.v6)
        v_button7.configure(image=window.v7)
        v_button8.configure(image=window.v8)
        v_button9.configure(image=window.v9)
        v_button10.configure(image=window.v10)
        v_button11.configure(image=window.v11)

        # Update the plot in the interface
        schwa().plot()

    # END FUNCTION
# END CLASS

# Function dedicated to the "GO!" button
# It initiates the seequence of events and in the rigth order and the rigth timing
def go():

    rec_time = int(1000*schwa.seconds) # convert to miliseconds

    # Reset plot
    schwa().plot(reset=True)

    # Start recording
    message() # Show recording message
    window.after(10, schwa().record) # Record

    #Recording stop (after recording time)
    window.after(rec_time, message)
    window.after(rec_time+20, schwa().formants) # wait 20 miliseconds and do formant analysis

    #Plot
    window.after(rec_time+40, schwa().plot) # Wait 20 miliseconds more before doing plot
    # The extra 20 miliseconds wait time is so that the computer can finish the previous job
    # Before starting the next one (which depend on the results from the previous)
    # Maybe this needs to be adjusted on slower computers?
# END FUNCTION

# Function that plays back the sound recorded from the user
def playSound():
    wave_obj = sa.WaveObject.from_wave_file(schwa.path + "audio/sound.wav")
    play_obj = wave_obj.play()

# Function that plays back the prerecorded sounds of the target vowel
def playTarget():
    if select_vowel.vowel != 0:
        vowel = str(select_vowel.vowel)
        targets = glob.glob(schwa.path + "audio/target/" + vowel + "/*.wav")
        target = random.choice(targets)
        wave_obj = sa.WaveObject.from_wave_file(target)
        play_obj = wave_obj.play()

def scale_ratio():
    schwa.scale = "ratio"
    schwa().plot()
def scale_freq():
    schwa.scale = "freq"
    schwa().plot()

def sex_change_f():
    schwa.sex_show = "female"
    instr["text"] = "  Sex set to female  "
    schwa().plot()
def sex_change_m():
    schwa.sex_show = "male"
    instr["text"] = "   Sex set to male  "
    schwa().plot()
def sex_change_all():
    schwa.sex_show = "all"
    instr["text"] = "   Sex set to all  "
    schwa().plot()


######################################################################################
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_!InterFACE!_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
######################################################################################

# Initiate interface window
window = Tk()

# The title of the window
window.title("HVAD - Help with Vowel Acquisition for Danish")

# Get logo and display in grid
window.logo = ImageTk.PhotoImage(Image.open(schwa.path + "img/HVADlogo.png"))
logo = Label(window, image=window.logo)
logo.grid(row=0,column=0, columnspan=2)

# The playback buttons
Button(window, text="Play your last recorded vowel", width = 30, command=playSound).grid(row=10, column=1, columnspan=4)
Button(window, text="Play target vowel", width = 30, command=playTarget).grid(row=11, column=1, columnspan=4)

# The images of the vowel buttons
window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/1.png"))
window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/2.png"))
window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/3.png"))
window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/4.png"))
window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/5.png"))
window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/6.png"))
window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/7.png"))
window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/8.png"))
window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/9.png"))
window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/10.png"))
window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_grey/11.png"))

# The vowel bottons 
v_button1 = Button(window, command=select_vowel().v1, image=window.v1)
v_button2 = Button(window, command=select_vowel().v2, image=window.v2)
v_button3 = Button(window, command=select_vowel().v3, image=window.v3)
v_button4 = Button(window, command=select_vowel().v4, image=window.v4)
v_button5 = Button(window, command=select_vowel().v5, image=window.v5)
v_button6 = Button(window, command=select_vowel().v6, image=window.v6)
v_button7 = Button(window, command=select_vowel().v7, image=window.v7)
v_button8 = Button(window, command=select_vowel().v8, image=window.v8)
v_button9 = Button(window, command=select_vowel().v9, image=window.v9)
v_button10 = Button(window, command=select_vowel().v10, image=window.v10)
v_button11 = Button(window, command=select_vowel().v11, image=window.v11)

# Place the vowel buttons in grid
v_button1.grid(row=12, column=1)
v_button2.grid(row=13, column=1)
v_button3.grid(row=14, column=1)
v_button4.grid(row=15, column=1)
v_button5.grid(row=12, column=2)
v_button6.grid(row=13, column=2)
v_button7.grid(row=14, column=2)
#v_button8.grid(row=13, column=3)
#v_button9.grid(row=14, column=3)
v_button10.grid(row=15, column=2)
#v_button11.grid(row=13, column=4)

# Go button
goStyle = tkFont.Font(family="Lucida Grande", size=15) # Styling of the text
Button(window, text="Go!", font=goStyle, width = 15, height=2, command=go).grid(row=16, column=1, columnspan=4)

# Recording message
fontStyle = tkFont.Font(family="Lucida Grande", size=30) # Styling of the text
instr = Label(window, text = " ", font=fontStyle, fg="#ff0000") # Just empty space at the start
instr.grid(row=18, column=1, columnspan=4) # Place in grid

# Change representation button
Button(window, text="Change representation", width = 30, command=rep().change_rep).grid(row=19, column=1, columnspan=4)

#scale buttons
#Button(window, text="Ratio", width = 15, command=scale_ratio).grid(row=21, column=1, columnspan=2)
#Button(window, text="Freq", width = 15, command=scale_freq).grid(row=21, column=3, columnspan=2)

# Sex change buttons
Button(window, text="Female", width = 8, command=sex_change_f).grid(row=22, column=1, columnspan=1)
Button(window, text="Male", width = 8, command=sex_change_m).grid(row=22, column=2, columnspan=1)
Button(window, text="All", width = 8, command=sex_change_all).grid(row=22, column=3, columnspan=1)

#reset
Button(window, text="Reset", width = 8, command=select_vowel().reset_vowel).grid(row=22, column=4, columnspan=1)

# Display plot in grid
window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_plots/grey.png"))
plot_show = Label(window, image=window.plot)
plot_show.grid(row=1, column=0, rowspan=40)



schwa().plot()
# Show the interface
window.mainloop()




