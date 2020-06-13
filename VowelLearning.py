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

    seconds = 2 # number of seconds to record

    # Formant data for plotting icons in foprmant space 
    data = pd.read_csv(path + "data/formant_data.csv") # Load raw data
    f1f3_avgs = []
    f2f3_avgs = []
    # Looping through vowel numbers and compute mean of ratio values
    # The data is stored in the fxf3_avgs lists
    for i in range(11):
        x = i + 1
        sub = data[data.vowel == x]
        f1f3 = stat.mean(sub["f1/f3"].tolist())
        f2f3 = stat.mean(sub["f2/f3"].tolist())
        f1f3_avgs.append(f1f3)
        f2f3_avgs.append(f2f3)

    # Containers for the ratio values of user signal
    F_ratio1 = 0
    F_ratio2 = 0
    
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
                    frames_per_buffer=CHUNK, input_device_index=2) # Remove input_device_index=3 to use computer mic

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
        w_size = 4 # window size
        F1_var_list = []
        F2_var_list = []
        F3_var_list = []

        # Loop though formant lists
        for w in range(len(F1_list)-w_size):

            #Determine window
            F1_window = F1_list[w:w+w_size] 
            F2_window = F2_list[w:w+w_size] 
            F3_window = F3_list[w:w+w_size]

            # Compute variance - log is used to normalize the values
            F1_var_list.append(np.log(stat.variance(F1_window)))
            F2_var_list.append(np.log(stat.variance(F2_window)))
            F3_var_list.append(np.log(stat.variance(F3_window)))
        
        # Loop though windows and make variance sums
        # F3 is down weighted a bit, for balance, as it is typically higher
        varSum_list = []
        for i in range(len(F1_var_list)):
            varSum = F1_var_list[i] + F2_var_list[i] + F3_var_list[i]*0.8 
            varSum_list.append(varSum)

        # find the minimum variance window and save its index
        index = varSum_list.index(min(varSum_list))
        
        # The mean formant values of the minimum variance window is the user formants
        F1 = stat.mean(F1_list[index:index+w_size])
        F2 = stat.mean(F2_list[index:index+w_size])
        F3 = stat.mean(F3_list[index:index+w_size])

        # Sketchy hack to overcome issue with backvowels
        # The problem is that when F1 and F2 get too close the analysis will interpret them as 1
        # When vowel 9 ("o") is selected if F2 is very high, treat F3 ass F2 and F2 as F1+100
        # NOT SURE IF IT WORKS AS INTENDET!!!
        if (select_vowel.vowel == 9) & (F2 > 1500):
            F3 = F2
            F2 = F1+100

        # Make formant ratios and store them in the class variables.
        schwa.F_ratio1 = F1/F3
        schwa.F_ratio2 = F2/F3

        # If the variance is two high the signal is two noisy
        # VARIANCE THRESHOLDS ARE SET SEMI RANDOMLY - NEEDS MORE TESTING
        if (F1_var_list[index]>7)|(F2_var_list[index]>10)|(F3_var_list[index]>11.5):
            schwa.noisy = True
        else:
            schwa.noisy = False

        """
        # Some testing printing
        print(schwa.F_ratio1)
        print(schwa.F_ratio2)
        print(F3)
        print("------")
        print(F1_var_list[index])
        print(F2_var_list[index])
        print(F3_var_list[index])
        print("------")
        """
    # END FUNCTION

    #Function for getting the images (used by in the plot function below)   
    def getImage(self, path, zoom):
        return OffsetImage(plt.imread(path), zoom=zoom)

    # Function that generates the right plot and shows it in the interface
    # The reset option is used to remove user stuff while recording (primarily to remove error message)
    def plot(self, reset = False):

        # Reset option
        if reset:
            if select_vowel.vowel == 0: # If no target vowel is selected
                if rep.r == "GEO": # if the rep is geometric
                    window.plot = ImageTk.PhotoImage(Image.open(self.path + "img/geometric_plots/grey.png"))
                    plot_show.configure(image=window.plot)
                else: # if the rep is IPA
                    window.plot = ImageTk.PhotoImage(Image.open(self.path + "img/IPA_plots/grey.png"))
                    plot_show.configure(image=window.plot)
            else: # If some target vowel is selected
                v = str(select_vowel.vowel) # Get the selected vowel
                if rep.r == "GEO": # if the rep is geometric
                    window.plot = ImageTk.PhotoImage(Image.open(self.path + "img/geometric_plots/" + v + ".png"))
                    plot_show.configure(image=window.plot)
                else:  # if the rep is IPA
                    window.plot = ImageTk.PhotoImage(Image.open(self.path + "img/IPA_plots/" + v + ".png"))
                    plot_show.configure(image=window.plot)
        
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
            zoom = 0.3

            # Set the paths to the images
            prefix_green = "img/" + symboltype + "_green/"
            prefix_grey = "img/" + symboltype + "_grey/"

            # Names of the pictures
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

            # These are the indeces for each picture
            idxs = [0,1,2,3,4,5,6,7,8,9,10]

            # Make a figure
            fig, ax = plt.subplots()
            # Add the points, color them white
            ax.scatter(self.f1f3_avgs, self.f2f3_avgs, color = "white") 

            # If the class variable noisy is true, just display error message
            if self.noisy:
                ax.text(0.155, 0.58, "Sorry, the vowel could not be calculated. \nPlease try again.", size=20, rotation=5,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round",
                        ec=(1., 0.5, 0.5),
                        fc=(1., 0.8, 0.8),
                        )
                )

            # If the class variable noisy is false, proceed with plotting  
            else:
                # Go through each coordinate, the indices, and the picture names together
                for idx, x0, y0, p in zip(idxs, self.f1f3_avgs, self.f2f3_avgs, paths):
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

                 #Target vowels from previous demo (for reference. should be removed in the final version)   
                target1_F1 = [0.122,0.139,0.142]
                target1_F2 = [0.784,0.794,0.781]
                ax.scatter(target1_F1, target1_F2, s=100, marker="o", c="blue")
                target2_F1 = [0.196, 0.179, 0.179]
                target2_F2 = [0.806, 0.786, 0.807]
                ax.scatter(target2_F1, target2_F2, s=100, marker="o", c="red")

                # The user formant ratios form recording, marked with an X
                ax.scatter(self.F_ratio1, self.F_ratio2, s=50, marker = "X", c="black")
            
            # Set axis limits
            ax.axis([0.09,0.22,0.3,0.9])

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

    # Function that changes the target vowel in the plot
    def change_plot(self):
        v = str(self.vowel)
        if rep.r == "GEO":
            window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_plots/" + v + ".png"))
            plot_show.configure(image=window.plot)
        else:
            window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/IPA_plots/" + v + ".png"))
            plot_show.configure(image=window.plot)
    # END FUNCTION

    # The 11 functions each dedicated to a vowel button
    # They rest the buttons to grey, change the selected vowel and make that green
    # Both on the button and in the plot
    def v1(self):
        self.reset_buttons()
        select_vowel.vowel = 1
        window.v1 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/1.png"))
        v_button1.configure(image=window.v1)
        self.change_plot()
    def v2(self):
        self.reset_buttons()
        select_vowel.vowel = 2
        window.v2 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/2.png"))
        v_button2.configure(image=window.v2)
        self.change_plot()
    def v3(self):
        self.reset_buttons()
        select_vowel.vowel = 3
        window.v3 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/3.png"))
        v_button3.configure(image=window.v3)
        self.change_plot()
    def v4(self):
        self.reset_buttons()
        select_vowel.vowel = 4
        window.v4 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/4.png"))
        v_button4.configure(image=window.v4)
        self.change_plot()
    def v5(self):
        self.reset_buttons()
        select_vowel.vowel = 5
        window.v5 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/5.png"))
        v_button5.configure(image=window.v5)
        self.change_plot()
    def v6(self):
        self.reset_buttons()
        select_vowel.vowel = 6
        window.v6 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/6.png"))
        v_button6.configure(image=window.v6)
        self.change_plot()
    def v7(self):
        self.reset_buttons()
        select_vowel.vowel = 7
        window.v7 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/7.png"))
        v_button7.configure(image=window.v7)
        self.change_plot()
    def v8(self):
        self.reset_buttons()
        select_vowel.vowel = 8
        window.v8 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/8.png"))
        v_button8.configure(image=window.v8)
        self.change_plot()
    def v9(self):
        self.reset_buttons()
        select_vowel.vowel = 9
        window.v9 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/9.png"))
        v_button9.configure(image=window.v9)
        self.change_plot()
    def v10(self):
        self.reset_buttons()
        select_vowel.vowel = 10
        window.v10 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/10.png"))
        v_button10.configure(image=window.v10)
        self.change_plot()
    def v11(self):
        self.reset_buttons()
        select_vowel.vowel = 11
        window.v11 = ImageTk.PhotoImage(Image.open(schwa.path + self.folder + "green/11.png"))
        v_button11.configure(image=window.v11)
        self.change_plot()
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
        if select_vowel.vowel == 0:
            if rep.r == "GEO":
                window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_plots/grey.png"))
                plot_show.configure(image=window.plot)
            else:
                window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/IPA_plots/grey.png"))
                plot_show.configure(image=window.plot)
        else:
            v = str(select_vowel.vowel)
            if rep.r == "GEO":
                window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_plots/" + v + ".png"))
                plot_show.configure(image=window.plot)
            else:
                window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/IPA_plots/" + v + ".png"))
                plot_show.configure(image=window.plot)
    # END FUNCTION
# END CLASS

# Function dedicated to the "GO!" button
# It initiates the seequence of events and in the rigth order and the rigth timing
def go():

    rec_time = 1000*schwa.seconds # convert to miliseconds

    # Reset plot
    schwa().plot(reset=True)

    # Start recording
    message() # Show recording message
    window.after(10, schwa().record) # wait 10 miliseconds and start recording

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
        targets = ["f2"]
        target = random.choice(targets)
        vowel = str(select_vowel.vowel)
        wave_obj = sa.WaveObject.from_wave_file(schwa.path + "audio/target/" + vowel+"/"+target + ".wav")
        play_obj = wave_obj.play()









######################################################################################
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_!InterFACE!_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
###_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_##
######################################################################################

# Initiate interface window
window = Tk()

# The title of the window
window.title("HVAD - Vowel Learning Tool")

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
v_button4.grid(row=12, column=2)
v_button5.grid(row=13, column=2)
v_button6.grid(row=14, column=2)
v_button7.grid(row=12, column=3)
v_button8.grid(row=13, column=3)
v_button9.grid(row=14, column=3)
v_button10.grid(row=12, column=4)
v_button11.grid(row=13, column=4)

# Go button
goStyle = tkFont.Font(family="Lucida Grande", size=15) # Styling of the text
Button(window, text="Go!", font=goStyle, width = 15, height=2, command=go).grid(row=16, column=1, columnspan=4)

# Recording message
fontStyle = tkFont.Font(family="Lucida Grande", size=30) # Styling of the text
instr = Label(window, text = " ", font=fontStyle, fg="#ff0000") # Just empty space at the start
instr.grid(row=18, column=1, columnspan=4) # Place in grid

# Change representation button
Button(window, text="Change representation", width = 30, command=rep().change_rep).grid(row=19, column=1, columnspan=4)

# Display plot in grid
window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "img/geometric_plots/grey.png"))
plot_show = Label(window, image=window.plot)
plot_show.grid(row=1, column=0, rowspan=40)

# Show the interface
window.mainloop()





"""
ae_f1 = 342, 2189, 2792
342/2792 = 0.122
2189/2792 = 0.784

ae_f2 = 430, 2441, 3075
430/3075 = 0.139
2441/3075 = 0.794

ae_m1 = 373, 2047, 2622
373/2622 = 0.142
2047/2622 = 0.781

ae_m2 = 387, 2118, 2538
387/2538 = 0.152
2118/2538 = 0.835


a_f1 = 514, 2120, 2629
514/2629= 0.196
2120/2629 = 0.806

a_f2 = 547, 2396,  3048
547/3048 = 0.179
2396/3048 = 0.786

a_m1 = 423, 1905, 2360
423/2360 = 0.179
1905/2360 = 0.807

a_m2 = 434, 2184, 2782
434/2782 = 0.156
2184/2782 = 0.785
"""
