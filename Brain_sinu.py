import pyttsx3 as spk
import speech_recognition as sr
import webbrowser
import pyautogui
import os
import datetime
import time
import threading
import tkinter as tk
import pygame
import requests
import pywhatkit as wt
from data import data
import sys

from hugchat import hugchat
import queue
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

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
            engine = spk.init('sapi5')
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)
            engine.setProperty('rate', 174)
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

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

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

    def chatBot(self, query):
        try:
            self.speak("it takes some time to respond,please wait...")
            json=self.resource_path("cookie.json")
            chatbot = hugchat.ChatBot(cookie_path=json)
            id = chatbot.new_conversation()
            chatbot.change_conversation(id)
            response = chatbot.chat(query)
            self.update_output(f"Chatbot: \n {response}")
            self.speak(response)
            return response
        except Exception as e:
            self.update_output(f"Error in chatbot: {str(e)}")
            return "Sorry, I encountered an error while processing your request."

    def play_alarm(self, alarm_time):
        current_time = datetime.datetime.now().strftime('%H:%M')
        while current_time != alarm_time:
            current_time = datetime.datetime.now().strftime('%H:%M')
            time.sleep(1)

        self.speak("Time to wake up!")
        alarm_sound = self.resource_path("alarm.mp3")


        if os.path.exists(alarm_sound):
            pygame.mixer.init()
            pygame.mixer.music.load(alarm_sound)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            self.update_output("Alarm sound file not found.")

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
            # Validate the time format
            alarm_datetime = datetime.datetime.strptime(alarm_time, '%H:%M')

            # Get current time
            current_time = datetime.datetime.now()

            # Set the alarm for today or tomorrow if the time has already passed
            alarm_datetime = alarm_datetime.replace(year=current_time.year, month=current_time.month, day=current_time.day)
            if alarm_datetime <= current_time:
                alarm_datetime += datetime.timedelta(days=1)

            # Calculate the time difference
            time_diff = alarm_datetime - current_time

            # Start the alarm thread
            threading.Thread(target=self.play_alarm, args=(alarm_datetime.strftime('%H:%M'),)).start()

            # Provide feedback
            self.speak(f"Alarm set for {alarm_datetime.strftime('%I:%M %p')} ({time_diff.seconds // 3600} hours and {(time_diff.seconds // 60) % 60} minutes from now)")
            self.update_output(f"Alarm set for {alarm_datetime.strftime('%I:%M %p')} ({time_diff.seconds // 3600} hours and {(time_diff.seconds // 60) % 60} minutes from now)")

            # Close the alarm frame
            self.remove_alarm_frame()
        except ValueError:
            self.speak("Invalid time format. Please enter the time in HH:MM format.")
            self.update_output("Invalid time format. Please enter the time in HH:MM format.")
        except Exception as e:
            self.speak("An error occurred while setting the alarm. Please try again.")
            self.update_output(f"Error setting alarm: {str(e)}")

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

    def fetch_weather(self, city_name):
        api_key = "ec4fd8be6f99939122dabbb131fb837f"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}"

        try:
            response = requests.get(url)
            data = response.json()
            temp = data['main']['temp']
            temp_c = temp - 273.15
            self.speak(f"The temperature in {city_name} is {temp_c:.1f} degrees Celsius.")
        except Exception as e:
            self.speak(f"Sorry, I couldn't fetch the weather for {city_name}. Please try again.")
            self.update_output(f"Error fetching weather: {str(e)}")

    def assistant(self):
        self.speak("Hey, user. I am Sinu, say 'Sinu' to activate me")
        while self.assistant_running:
            command = self.listen().lower()
            if "sinu" in command or "seenu" in command or "chinu" in command:
                self.speak("Hi... I am Sinu... How can I help you?")
                while self.assistant_running:
                    task = self.listen().lower()
                    if "open google" in task:
                        self.speak("Opening Google...")
                        webbrowser.open("https://www.google.com/")
                    elif "song" in task:
                        self.speak("Which song do you want me to play?")
                        song = self.listen().lower()
                        if song:
                            self.speak(f"Playing {song}")
                            wt.playonyt(song)
                    if "gpt" in task:
                        self.speak("What should I search on ChatGPT?")
                        query = self.listen().lower()
                        if query:
                            url = f"https://chat.openai.com/?q={query}"
                            webbrowser.open(url)
                        else:
                            self.speak("I didn't catch that. Please try again.")
                    elif "shut down" in task:
                        self.speak("Shutting down in 5 seconds...")
                        time.sleep(5)
                        os.system("shutdown /s /t 1")
                    elif "sleep" in task:
                        self.speak("Putting the system to sleep in 5 seconds...")
                        time.sleep(5)
                        os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")
                    elif "search on google" in task:
                        self.search_on_google()
                    elif "time" in task:
                        self.speak("The time is " + self.get_time())
                    elif "date" in task:
                        self.speak("The date is " + self.get_date())
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
                    elif "open the notepad" in task or "open notepad" in task:
                        self.speak("Opening notepad")
                        os.system("start notepad")
                        self.speak("plz click on the notepad window")
                        time.sleep(3)  # Wait for Notepad to open


                        self.speak("What should I write in notepad?")
                        while True:
                            data_notepad = self.listen().lower()
                            if "stop" in data_notepad:
                                self.speak("Stopping notepad interaction")
                                break
                            if data_notepad:
                                pyautogui.typewrite(data_notepad)
                                pyautogui.press('space')



                    elif "close notepad" in task:
                        os.system("TASKKILL /F /IM notepad.exe")
                    elif "saved data" in task:
                        self.speak("data saved")
                        self.update_output("data saved")



                        os.system("start notepad")
                    elif "paint" in task:
                        os.system("start mspaint")
                    elif "word" in task:
                        os.system("start WINWORD")
                    elif "excel" in task:
                        os.system("start EXCEL")
                    elif "powerpoint" in task:
                        os.system("start POWERPNT")
                    elif task in data["q"]:
                        self.speak(data["q"][task])
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
                        os.system("TASKKILL /F /IM WindowsCamera.exe")
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
                    elif "volume up" in task or "volumeup" in task or  "increase" in task:
                        self.speak("Increasing volume...")
                        pyautogui.press('volumeup')
                    elif "volume down" in task or "volumedown" in task or "decrease" in task:
                        self.speak("Decreasing volume...")
                        pyautogui.press('volumedown')
                    elif "mute" in task or "unmute" in task:
                        self.speak("Toggling mute...")
                        pyautogui.press('volumemute')
                    elif "switch window" in task or "switch" in task or "screen" in task:
                        self.speak("Switching window...")
                        pyautogui.hotkey('alt', 'tab')
                    elif "minimize" in task or "minimise" in task:
                        self.speak("minimizing the window...")
                        pyautogui.hotkey('win', 'd')
                    elif "maximize" in task or "maximise" in task:
                        self.speak("maximizing the window...")
                        pyautogui.hotkey('win', 'd')
                    elif "scroll down" in task or "scrolldown" in task:
                        pyautogui.press('pagedown')
                    elif "scroll up" in task or "scrollup" in task:
                        pyautogui.press('pageup')
                    elif "weather" in task:
                        self.speak("What city do you want to know the weather of?")
                        city = self.listen().lower()
                        if city:
                            city_name = city.split()[-1]
                            threading.Thread(target=self.fetch_weather, args=(city_name,)).start()
                        else:
                            self.speak("I didn't catch the city name. Please try again.")
                    elif "my portfolio" in task:
                        webbrowser.open("https://partha-batabyal.github.io/fatty/#nav_Home")
                    elif "chat" in task or "chatbot" in task:
                        self.speak("chatbot is activated...")
                        while True:
                            query = self.listen().lower()
                            if "stop" in query or "exit" in query or "quit" in query or "bye" in query or "close" in query:
                                break
                            elif query:
                                self.chatBot(query)

                    elif "sleep" in task or not self.assistant_running or "quit" in task or "stop" in task or "exit" in task or "bye" in task or "close" in task:
                        break
                    else:
                        self.speak("sorry, this fiture is not available,please give me anather one")
            if not self.assistant_running:
                break

    def start_assistant(self):
        self.assistant_running = True
        threading.Thread(target=self.assistant).start()

    def stop_assistant(self):
        self.assistant_running = False
        self.remove_alarm_frame()
        self.speak("Stopping the assistant. Goodbye!")
        self.update_output("Stopping the assistant. Goodbye!")
        self.root.destroy()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Sinu Voice Assistant")

        sinuImg = self.resource_path('sinu.png')
        self.root.iconphoto(True, tk.PhotoImage(file=sinuImg))

        self.root.maxsize(800, 720)
        self.root.minsize(700, 720)
        self.root.protocol("WM_DELETE_WINDOW", self.stop_assistant)
        self.root.configure(bg='gray')

        self.output_text = tk.Text(self.root, height=20, width=60, state=tk.DISABLED, bg='gray', fg='white', font=('Helvetica', 12), padx=10, pady=10)
        self.output_text.pack(pady=20, padx=30)

        button_frame = tk.Frame(self.root, bg='gray')
        button_frame.pack(pady=20)

        button_style = {'font': ('Helvetica', 14), 'width': 15, 'height': 2, 'fg': 'white'}
        start_button = tk.Button(button_frame, text="Start", command=self.start_assistant, **button_style, bg="green", cursor="hand2", activebackground="green")
        start_button.grid(row=0, column=0, padx=20)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_assistant, **button_style, bg="red", cursor="hand2", activebackground="red")
        stop_button.grid(row=0, column=1, padx=20)

        self.root.after(100, self.process_output_queue)
        self.root.mainloop()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.setup_gui()