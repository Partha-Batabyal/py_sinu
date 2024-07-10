import pyttsx3 as spk
import speech_recognition as sr
import webbrowser
import pyautogui
import os
import datetime
import time
import threading
import tkinter as tk
from data import data
import pygame
import queue
import pywhatkit as wt

class VoiceAssistant:
    def __init__(self):
        self.output_queue = queue.Queue()
        self.speak_lock = threading.Lock()
        self.assistant_running = False
        self.alarm_frame = None
        self.root = None
        self.output_text = None
        self.alarm_entry = None

    def speak(self, text):
        with self.speak_lock:
            engine = spk.init()
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)
            engine.say(text)
            engine.runAndWait()

    def listen(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.update_output("Listening...")
            r.adjust_for_ambient_noise(source, duration=1.0)
            r.pause_threshold = 1.0
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            r.dynamic_energy_adjustment_damping = 0.15
            r.dynamic_energy_adjustment_ratio = 1.5
            audio = r.listen(source)

        try:
            text = r.recognize_google(audio)
            self.update_output(f"Recognized: {text}")
            return text.lower()
        except sr.UnknownValueError:
            self.update_output("Could not understand audio")
        except sr.RequestError as e:
            self.update_output(f"Error requesting recognition; {e}")
        return ""

    def update_output(self, text):
        self.output_queue.put(text)

    def process_output_queue(self):
        try:
            while True:
                text = self.output_queue.get_nowait()
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, text + "\n")
                self.output_text.config(state=tk.DISABLED)
                self.output_text.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.process_output_queue)

    def play_alarm(self, alarm_time):
        current_time = time.strftime('%H:%M')
        while current_time != alarm_time:
            current_time = time.strftime('%H:%M')
            time.sleep(1)

        self.speak("Time to wake up!")
        alarm_sound = "alarm.mp3"

        if os.path.exists(alarm_sound):
            pygame.init()
            pygame.mixer.init()
            pygame.mixer.music.load(alarm_sound)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            self.speak(f"Alarm sound file '{alarm_sound}' not found.")

    def screen_shot(self):
        self.speak("What should I name the screenshot?")
        while True:
            name = self.listen()
            if name:
                self.speak("Great! I'll take a screenshot with that name.")
                img = pyautogui.screenshot()
                file_name = f"{name}.png"
                img.save(file_name)
                self.speak(f"Screenshot saved as {file_name}.")
                self.update_output(f"Screenshot saved as {file_name}.")
                break
            else:
                self.speak("I didn't catch that. Please try again.")
                self.update_output("I didn't catch that. Please try again.")

    def set_alarm_from_entry(self, event=None):
        alarm_time = self.alarm_entry.get().strip()
        try:
            time.strptime(alarm_time, '%H:%M')
            alarm_thread = threading.Thread(target=self.play_alarm, args=(alarm_time,))
            alarm_thread.start()
            self.speak(f"Alarm set for {alarm_time}")
            self.update_output(f"Alarm set for {alarm_time}")
            self.remove_alarm_frame()
        except ValueError:
            self.speak("Invalid time format. Please enter in HH:MM format.")
            self.update_output("Invalid time format. Please enter in HH:MM format.")

    def display_alarm_frame(self):
        self.speak("Please enter the alarm time in Hour:Minute format.")
        self.alarm_frame = tk.Frame(self.root, bg='gray')
        self.alarm_frame.pack(pady=20)

        alarm_label = tk.Label(self.alarm_frame, text="Enter alarm time (HH:MM):", bg='gray', fg='white', font=('Helvetica', 12))
        alarm_label.grid(row=0, column=0, padx=10)

        self.alarm_entry = tk.Entry(self.alarm_frame, width=15, font=('Helvetica', 12))
        self.alarm_entry.grid(row=0, column=1, padx=10)
        self.alarm_entry.bind('<Return>', self.set_alarm_from_entry)

        alarm_button = tk.Button(self.alarm_frame, text="Set Alarm", command=self.set_alarm_from_entry, bg="blue", fg="white")
        alarm_button.grid(row=0, column=2, padx=10)

        # Focus on the entry field
        self.alarm_entry.focus_set()

    def remove_alarm_frame(self):
        if self.alarm_frame:
            self.alarm_frame.destroy()
            self.alarm_frame = None

    def get_time(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self):
        return datetime.datetime.now().strftime("%d-%m-%Y")

    def search_on_google(self):
        self.speak("What should I search on Google?")
        query = self.listen()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
        else:
            self.speak("I didn't catch that. Please try again.")

    def sleep_mode(self):
        self.speak("Putting the system to sleep in 5 seconds...")
        time.sleep(5)
        os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")

    def shut_down_system(self):
        self.speak("Shutting down in 5 seconds...")
        time.sleep(5)
        os.system("shutdown /s /t 1")

    def play_song(self):
        self.speak("Which song do you want me to play?")
        song = self.listen()
        if song:
            self.speak(f"Playing {song}")
            wt.playonyt(song)
        else:
            self.speak("I didn't catch that. Please try again.")

    def assistant(self):
        self.speak("Hey, user. I am Sinu, say 'Sinu' to activate me")
        while self.assistant_running:
            command = self.listen()
            if "sinu" in command or "seenu" in command:
                self.speak("Hi... I am Sinu... How can I help you?")
                while self.assistant_running:
                    task = self.listen().lower()
                    if "open google" in task:
                        self.speak("Opening Google...")
                        webbrowser.open("https://www.google.com/")
                    elif "song" in task:
                        self.play_song()
                    elif "shut down" in task:
                        self.shut_down_system()
                    elif "sleep" in task:
                        self.sleep_mode()
                    elif "search on google" in task:
                        self.search_on_google()
                    elif "time" in task:
                        self.speak("The time is " + self.get_time())
                    elif "date" in task:
                        self.speak("The date is " + self.get_date())
                    elif task in data["q"]:
                        self.speak(data["q"][task])
                    elif "close this tab" in task:
                        pyautogui.hotkey('ctrl', 'w')
                    elif "open a new tab" in task:
                        pyautogui.hotkey('ctrl', 't')
                    elif "back to the previous tab" in task:
                        pyautogui.hotkey('ctrl', 'tab')
                    elif "recently closed tab" in task:
                        pyautogui.hotkey('ctrl', 'shift', 't')
                    elif "calculator" in task:
                        os.system("start calc")
                    elif "notepad" in task:
                        os.system("start notepad")
                    elif "paint" in task:
                        os.system("start mspaint")
                    elif "word" in task:
                        os.system("start WINWORD")
                    elif "excel" in task:
                        os.system("start EXCEL")
                    elif "powerpoint" in task:
                        os.system("start POWERPNT")
                    elif "set alarm" in task:
                        self.root.after(0, self.display_alarm_frame)
                    elif "close browser" in task:
                        self.speak("Closing browser...")
                        os.system("TASKKILL /F /IM chrome.exe")
                    elif "close edge" in task:
                        self.speak("Closing edge...")
                        os.system("TASKKILL /F /IM msedge.exe")
                    elif "open camera" in task:
                        self.speak("Opening camera...")
                        os.system("start microsoft.windows.camera:")
                    elif "close camera" in task:
                        self.speak("Closing camera...")
                        os.system("TASKKILL /F /IM microsoft.windows.camera:")
                    elif "open command prompt" in task:
                        self.speak("Opening command prompt...")
                        os.system("start cmd")
                    elif "close command prompt" in task:
                        self.speak("Closing command prompt...")
                        os.system("TASKKILL /F /IM cmd.exe")
                    elif "open powershell" in task:
                        self.speak("Opening powershell...")
                        os.system("start powershell")
                    elif "close powershell" in task:
                        self.speak("Closing powershell...")
                        os.system("TASKKILL /F /IM powershell.exe")
                    elif "take screenshot" in task:
                        self.speak("Taking screenshot...")
                        self.screen_shot()
                    elif "volume up" in task:
                        self.speak("Increasing volume...")
                        pyautogui.hotkey('volumeup')
                    elif "volume down" in task:
                        self.speak("Decreasing volume...")
                        pyautogui.hotkey('volumedown')
                    elif "mute" in task:
                        self.speak("Muting volume...")
                        pyautogui.hotkey('volumemute')
                    elif "unmute" in task:
                        self.speak("Unmuting volume...")
                        pyautogui.hotkey('volumemute')
                    elif "my portfolio" in task:
                        webbrowser.open("https://partha-batabyal.github.io/fatty/#nav_Home")
                    elif "exit" in task or not self.assistant_running:
                        break
                    else:
                        self.speak("I'm not sure how to respond to that. Could you please rephrase or ask something else?")
            if not self.assistant_running:
                break

    def start_assistant(self):
        self.assistant_running = True
        threading.Thread(target=self.assistant).start()

    def stop_assistant(self):
        self.assistant_running = False

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Sinu Voice Assistant")
        self.root.configure(bg='gray')

        self.output_text = tk.Text(self.root, height=20, width=60, state=tk.DISABLED, bg='gray', fg='white')
        self.output_text.pack(pady=20)

        button_frame = tk.Frame(self.root, bg='gray')
        button_frame.pack(pady=20)

        button_style = {'font': ('Helvetica', 14), 'width': 15, 'height': 2, 'fg': 'white'}
        start_button = tk.Button(button_frame, text="Start", command=self.start_assistant, **button_style, bg="green")
        start_button.grid(row=0, column=0, padx=20)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_assistant, **button_style, bg="red")
        stop_button.grid(row=0, column=1, padx=20)

        self.root.after(100, self.process_output_queue)
        self.root.mainloop()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.setup_gui()