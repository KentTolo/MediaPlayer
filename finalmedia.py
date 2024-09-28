import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Progressbar
import customtkinter as ctk
from mutagen.mp3 import MP3
import threading
import pygame
import time
import os
import cv2  # Import OpenCV for video playback
from tkinter import messagebox
from tkinter import ttk

# Initialize pygame for audio playback
pygame.mixer.init()

# Store the current position of the music
current_position = 0
paused = False
selected_folder_path = ""  # store the selected folder path

# Function to update the progress bar for audio
def update_progress():
    global current_position
    while True:
        if pygame.mixer.music.get_busy() and not paused:
            current_position = pygame.mixer.music.get_pos() / 1000
            pbar["value"] = current_position
            
            # Check if the current song has reached its maximum duration
            if current_position >= pbar["maximum"]:
                stop_music()  # Stop music playback
                pbar["value"] = 0  # Reset the progress bar
            
            window.update()
        time.sleep(0.1)

# Create a thread to update the progress bar
pt = threading.Thread(target=update_progress)
pt.daemon = True
pt.start()

# Function to select a folder containing music files
def select_music_folder():
    global selected_folder_path
    selected_folder_path = filedialog.askdirectory()
    if selected_folder_path:
        lbox.delete(0, tk.END)  # Clear the listbox
        for filename in os.listdir(selected_folder_path):
            if filename.endswith(".mp3"):
                lbox.insert(tk.END, filename)  # Insert filenames into the listbox

# Function to play the selected music
def play_music():
    global paused
    if paused:
        pygame.mixer.music.unpause()  # Unpause music if it was paused
        paused = False
    else:
        play_selected_song()  # Play the selected song from the listbox

# Function to play the selected song from the listbox
def play_selected_song():
    global current_position, paused
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        selected_song = lbox.get(current_index)
        full_path = os.path.join(selected_folder_path, selected_song)
        pygame.mixer.music.load(full_path)  # Load the selected song
        pygame.mixer.music.play(start=current_position)  # Play the song from the current position
        paused = False

        # Get song duration and update progress bar
        audio = MP3(full_path)
        song_duration = audio.info.length
        pbar["maximum"] = song_duration

# Function to pause the current music
def pause_music():
    global paused
    pygame.mixer.music.pause()  # Pause the music
    paused = True

# Function to stop the current music
def stop_music():
    global paused
    pygame.mixer.music.stop()  # Stop music playback
    paused = False

# Function to play the previous song in the playlist
def previous_song():
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        if current_index > 0:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index - 1)
            play_selected_song()

# Function to play the next song in the playlist
def next_song():
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        if current_index < lbox.size() - 1:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index + 1)
            play_selected_song()

# Function to upload and play video using OpenCV
def upload_video():
    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
    if video_path:
        play_video(video_path)

# Function to play video with OpenCV
def play_video(video_path):
    cap = cv2.VideoCapture(video_path)
    
    # Check if the video was opened successfully
    if not cap.isOpened():
        messagebox.showerror("Error", "Unable to open video file.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Convert frame to RGB (OpenCV uses BGR by default)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Display video frame in a window
            cv2.imshow('Video Playback', frame_rgb)

            # Close window when 'q' is pressed
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

# Create the main window
window = tk.Tk()
window.title("High-End Multimedia Player")
window.geometry("800x600")

# Create a label for the media player
l_music_player = tk.Label(window, text="High-End Multimedia Player", font=("TkDefaultFont", 30, "bold"))
l_music_player.pack(pady=10)

# Create a button to select the music folder
btn_select_folder = ctk.CTkButton(window, text="Select Music Folder", command=select_music_folder, font=("TkDefaultFont", 18))
btn_select_folder.pack(pady=10)

# Create a listbox to display available songs
lbox = tk.Listbox(window, width=50, font=("TkDefaultFont", 16))
lbox.pack(pady=10)

# Create a frame to hold control buttons for audio
btn_frame = tk.Frame(window)
btn_frame.pack(pady=20)

# Create buttons for controlling audio
btn_previous = ctk.CTkButton(btn_frame, text="<", command=previous_song, width=50, font=("TkDefaultFont", 18))
btn_previous.pack(side=tk.LEFT, padx=5)

btn_play = ctk.CTkButton(btn_frame, text="Play", command=play_music, width=50, font=("TkDefaultFont", 18))
btn_play.pack(side=tk.LEFT, padx=5)

btn_pause = ctk.CTkButton(btn_frame, text="Pause", command=pause_music, width=50, font=("TkDefaultFont", 18))
btn_pause.pack(side=tk.LEFT, padx=5)

btn_next = ctk.CTkButton(btn_frame, text=">", command=next_song, width=50, font=("TkDefaultFont", 18))
btn_next.pack(side=tk.LEFT, padx=5)

# Create a progress bar for the current song's progress
pbar = Progressbar(window, length=300, mode="determinate")
pbar.pack(pady=10)

# Button to upload and play video
btn_upload_video = ctk.CTkButton(window, text="Upload Video", command=upload_video, font=("TkDefaultFont", 18))
btn_upload_video.pack(pady=20)

window.mainloop()
