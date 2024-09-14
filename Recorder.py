import sounddevice as sd
import numpy as np
import wave
import os
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from scipy.fftpack import fft
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# Audio Recorder Class
class AudioRecorder:
    def __init__(self, folder_path="recordings"):
        self.fs = 44100  # Sampling rate
        self.recording = False
        self.paused = False
        self.frames = []
        self.stream = None
        self.folder_path = 'E:/Projects/Python_Audio_Recorder/Recordings'  # Placeholder for storing recording
        self.start_time = None
        self.paused_duration = 0  # To track the total pause duration
        self.pause_start_time = None

        # Ensure recordings folder exists
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            self.start_time = time.time()  # Start timer for duration
            self.paused_duration = 0  # Reset paused duration
            self.stream = sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.fs)
            self.stream.start()
            print("Recording started...")

    def audio_callback(self, indata, frames, time, status):
        if self.recording and not self.paused:
            self.frames.append(indata.copy())

    def pause_recording(self):
        if self.recording:
            if self.paused:
                # Resuming recording
                self.paused = False
                if self.pause_start_time:
                    self.paused_duration += time.time() - self.pause_start_time
                print("Recording resumed.")
            else:
                # Pausing recording
                self.paused = True
                self.pause_start_time = time.time()  # Mark the time when paused
                print("Recording paused.")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.stream.stop()
            self.stream.close()
            print("Recording stopped.")

    def reset_recording(self):
        if self.recording:
            self.stop_recording()
            self.frames = []
            print("Recording reset.")

    def get_duration(self):
        if self.start_time:
            if self.paused:
                return self.pause_start_time - self.start_time - self.paused_duration
            else:
                return time.time() - self.start_time - self.paused_duration
        return 0

    def save_recording(self, filename):
        if not self.frames:
            messagebox.showwarning("Warning", "No recording to save!")
            return

        data = np.concatenate(self.frames, axis=0)
        scaled_data = np.int16(data / np.max(np.abs(data)) * 32767)

        filepath = os.path.join(self.folder_path, filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.fs)
            wf.writeframes(scaled_data.tobytes())

        messagebox.showinfo("Info", f"Recording saved as {filepath}")

    def delete_recording(self):
        self.frames = []
        messagebox.showinfo("Info", "Recording deleted.")


# GUI for the Audio Recorder
class RecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder")
        self.recorder = AudioRecorder()

        # Main Layout
        self.setup_layout()

        # Frequency Meter Setup
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        # List all recordings on startup
        self.refresh_recordings()

        # Update timer for recording duration
        self.update_duration()

    def setup_layout(self):
        # Title
        title = tk.Label(self.root, text="Python Audio Recorder", font=("Arial", 20))
        title.pack(pady=10)

        # Buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.record_btn = tk.Button(control_frame, text="Record", command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = tk.Button(control_frame, text="Pause", command=self.pause_recording)
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.stop_btn = tk.Button(control_frame, text="Stop", command=self.stop_recording)
        self.stop_btn.grid(row=0, column=2, padx=5)

        self.save_btn = tk.Button(control_frame, text="Save", command=self.save_recording)
        self.save_btn.grid(row=0, column=3, padx=5)

        self.reset_btn = tk.Button(control_frame, text="Reset", command=self.reset_recording)
        self.reset_btn.grid(row=0, column=4, padx=5)

        # Timer and Status Label
        self.status_label = tk.Label(self.root, text="Status: Idle | Duration: 0 s", font=("Arial", 14))
        self.status_label.pack(pady=10)

        # Recordings List
        self.recordings_list = tk.Listbox(self.root, height=10)
        self.recordings_list.pack(pady=10)

        # Play and Delete Buttons
        list_control_frame = tk.Frame(self.root)
        list_control_frame.pack(pady=5)

        self.play_btn = tk.Button(list_control_frame, text="Play", command=self.play_recording)
        self.play_btn.grid(row=0, column=0, padx=5)

        self.delete_selected_btn = tk.Button(list_control_frame, text="Delete", command=self.delete_selected_recording)
        self.delete_selected_btn.grid(row=0, column=1, padx=5)

    def start_recording(self):
        if not self.recorder.recording:
            threading.Thread(target=self.recorder.start_recording).start()
            self.update_frequency_meter()

    def pause_recording(self):
        self.recorder.pause_recording()

    def stop_recording(self):
        self.recorder.stop_recording()

    def reset_recording(self):
        self.recorder.reset_recording()
        self.status_label.config(text="Status: Reset | Duration: 0 s")

    def save_recording(self):
        if not self.recorder.frames:
            messagebox.showwarning("Warning", "No recording to save!")
            return

        filename = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")], initialdir=self.recorder.folder_path)
        if filename:
            self.recorder.save_recording(os.path.basename(filename))
            self.refresh_recordings()

    def refresh_recordings(self):
        # Clear list
        self.recordings_list.delete(0, tk.END)

        # List all saved recordings
        recordings = os.listdir(self.recorder.folder_path)
        for rec in recordings:
            if rec.endswith(".wav"):
                self.recordings_list.insert(tk.END, rec)

    def play_recording(self):
        selected = self.recordings_list.get(tk.ACTIVE)
        if selected:
            filepath = os.path.join(self.recorder.folder_path, selected)
            os.system(f"start {filepath}")

    def delete_selected_recording(self):
        selected = self.recordings_list.get(tk.ACTIVE)
        if selected:
            filepath = os.path.join(self.recorder.folder_path, selected)
            os.remove(filepath)
            self.refresh_recordings()
            messagebox.showinfo("Info", f"{selected} deleted.")

    def update_frequency_meter(self):
        if self.recorder.recording and not self.recorder.paused:
            data = np.concatenate(self.recorder.frames, axis=0) if self.recorder.frames else np.zeros(1024)
            fft_data = fft(data)
            self.ax.clear()
            self.ax.plot(np.abs(fft_data[:len(fft_data)//2]))
            self.canvas.draw()

        if self.recorder.recording:
            self.root.after(100, self.update_frequency_meter)

    def update_duration(self):
        if self.recorder.recording:
            duration = int(self.recorder.get_duration())
            status = "Paused" if self.recorder.paused else "Recording"
            self.status_label.config(text=f"Status: {status} | Duration: {duration} s")
        else:
            self.status_label.config(text="Status: Idle | Duration: 0 s")

        self.root.after(1000, self.update_duration)


# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = RecorderApp(root)
    root.mainloop()
