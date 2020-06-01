import pyaudio
import matplotlib.pyplot as plt
import wave
import parselmouth
import simpleaudio as sa
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageTk
import random


class message:
    outputs = ["           3           ", "2", "1", "GO!", "STOP", "Ready to go"]
    n = 0
    def __init__(self):
        instr['text'] = self.outputs[self.n]

        if self.n == len(self.outputs)-1:
            message.n = 0
        else:
            message.n = self.n + 1

class schwa:

    path = "/Users/Christoffer/Documents/HCI/VowelLearning/"

    def record(self):
        CHUNK = 2048 # number of data points to read at a time
        RATE = 44100
        seconds = 2

        p=pyaudio.PyAudio() 
        stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
                    frames_per_buffer=CHUNK, input_device_index=3 ) 


        frames = []
        # Store data in chunks for 2 seconds
        for i in range(0, int(RATE / CHUNK * seconds)):
            data = stream.read(CHUNK)
            frames.append(data)


        # Stop and close the stream 
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        p.terminate()

        wf = wave.open(self.path + "sound.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    F_ratio1 = 0
    F_ratio2 = 0

    def formants(self):
        sound = parselmouth.Sound(self.path + "sound.wav")
        formants = sound.to_formant_burg()
        F1 = formants.get_value_at_time(1,1)
        F2 = formants.get_value_at_time(2,1)
        F3 = formants.get_value_at_time(3,1)

        schwa.F_ratio1 = F1/F3
        schwa.F_ratio2 = F2/F3
        print(schwa.F_ratio1)
        print(schwa.F_ratio2)
    
    def plot(self):

        target1_F1 = [0.122,0.139,0.142]
        target1_F2 = [0.784,0.794,0.781]
        plt.scatter(target1_F1, target1_F2, s=100, marker="o", c="blue")

        target2_F1 = [0.196, 0.179, 0.179]
        target2_F2 = [0.806, 0.786, 0.807]
        plt.scatter(target2_F1, target2_F2, s=100, marker="o", c="red")

        plt.scatter(self.F_ratio1, self.F_ratio2, s=50, marker = "X", c="black")
        plt.axis([0,0.4,0.1,1])

        plt.xlabel("Formant 1/3 ratio")
        plt.ylabel('Formant 2/3 ratio')
        plt.savefig(self.path + "plot.png")

        plt.clf()

        window.plot = ImageTk.PhotoImage(Image.open(self.path + "plot.png"))
        plot_show.configure(image=window.plot)




def go():
    #Count in 
    message()
    window.after(500, message)
    window.after(1000, message)

    #Recording start
    window.after(1500, message)
    window.after(1510, schwa().record)

    #Recording stop
    window.after(3500, message)
    window.after(3520, schwa().formants)

    #Plot
    window.after(3530, schwa().plot)

    # Return message to normal
    window.after(7000, message)


def playSound():
    wave_obj = sa.WaveObject.from_wave_file(schwa.path + "sound.wav")
    play_obj = wave_obj.play()

def playTarget1():
    targets = ["ae_f1", "ae_f2", "ae_m1"]
    target = random.choice(targets)
    wave_obj = sa.WaveObject.from_wave_file(schwa.path + "target/" + target + ".wav")
    play_obj = wave_obj.play()

def playTarget2():
    targets = ["a_f1", "a_f2", "a_m1"]
    target = random.choice(targets)
    wave_obj = sa.WaveObject.from_wave_file(schwa.path + "target/" + target + ".wav")
    play_obj = wave_obj.play()


window = Tk()
window.title("Vowel Learning")

Label(window, text="#### VOWEL LEARNING EXPERIENCE ####").pack()

Button(window, text="Play your last recorded vowel", width = 30, command=playSound).pack()
Button(window, text="Play a blue vowel", width = 30, command=playTarget1).pack()
Button(window, text="Play a red vowel", width = 30, command=playTarget2).pack()
Button(window, text="Go!", width = 15, command=go).pack() #grid(row=0, column=0)

fontStyle = tkFont.Font(family="Lucida Grande", size=20)
instr = Label(window, text = "Ready to go", font=fontStyle)
#instr.grid(row=1,column=0)
instr.pack()

window.plot = ImageTk.PhotoImage(Image.open(schwa.path + "plot_start.png"))
plot_show = Label(window, image=window.plot)
plot_show.pack()

window.truth = ImageTk.PhotoImage(Image.open(schwa.path + "ground_truth.jpg"))
ground_truth = Label(window, image=window.truth)
ground_truth.pack()


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
