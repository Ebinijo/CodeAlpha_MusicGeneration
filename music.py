import tkinter as tk
from tkinter import messagebox, scrolledtext
import numpy as np
import os
import threading

# Try importing required libraries
try:
    from music21 import stream, note, chord, tempo, instrument
    from music21 import environment
    MUSIC21_OK = True
except ImportError:
    MUSIC21_OK = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TF_OK = True
except ImportError:
    TF_OK = False

# ── Simple Music Generator (No Training Required) ──────────
def generate_simple_music(style="classical", length=32):
    """Generate music without requiring pre-trained model"""
    
    # Note patterns for different styles
    patterns = {
        "classical": ["C4","E4","G4","C5","E5","G5","E5","C5",
                     "D4","F4","A4","D5","F5","A5","F5","D5",
                     "E4","G4","B4","E5","G5","B5","G5","E5",
                     "F4","A4","C5","F5","A5","C6","A5","F5"],
        "jazz":      ["C4","Eb4","G4","Bb4","C5","Bb4","G4","Eb4",
                     "F4","Ab4","C5","Eb5","F5","Eb5","C5","Ab4",
                     "G4","Bb4","D5","F5","G5","F5","D5","Bb4",
                     "A4","C5","E5","G5","A5","G5","E5","C5"],
        "pop":       ["C4","C4","G4","G4","A4","A4","G4","G4",
                     "F4","F4","E4","E4","D4","D4","C4","C4",
                     "G4","G4","F4","F4","E4","E4","D4","D4",
                     "G4","G4","F4","F4","E4","E4","D4","D4"],
        "random":    None
    }
    
    note_names = ["C","D","E","F","G","A","B","C#","D#","F#","G#","A#"]
    octaves = [3, 4, 4, 4, 5]
    
    s = stream.Score()
    part = stream.Part()
    part.insert(0, instrument.Piano())
    t = tempo.MetronomeMark(number=120)
    part.insert(0, t)
    
    if style == "random" or patterns[style] is None:
        selected = [f"{np.random.choice(note_names)}{np.random.choice(octaves)}"
                   for _ in range(length)]
    else:
        selected = patterns[style][:length]
    
    durations = [0.5, 0.5, 1.0, 1.0, 0.25, 0.25]
    
    for n in selected:
        try:
            new_note = note.Note(n)
            new_note.duration.quarterLength = np.random.choice(durations)
            part.append(new_note)
        except:
            new_note = note.Note("C4")
            new_note.duration.quarterLength = 0.5
            part.append(new_note)
    
    s.append(part)
    return s

# ── UI App ─────────────────────────────────────────────────
class MusicGenApp:
    def __init__(self, root):
        root.title("🎵 CodeAlpha Music Generator")
        root.geometry("600x580")
        root.configure(bg="#1e1e2e")
        root.resizable(False, False)

        # Title
        tk.Label(root, text="🎵 AI Music Generator",
                 font=("Helvetica", 20, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(pady=15)

        tk.Label(root, text="Generate music sequences using AI patterns",
                 font=("Helvetica", 10),
                 bg="#1e1e2e", fg="#6c7086").pack()

        # Style selection
        style_frame = tk.Frame(root, bg="#1e1e2e")
        style_frame.pack(pady=15)

        tk.Label(style_frame, text="Select Music Style:",
                 bg="#1e1e2e", fg="#a6adc8",
                 font=("Helvetica", 12)).grid(row=0, column=0, padx=10)

        self.style_var = tk.StringVar(value="classical")
        styles = ["classical", "jazz", "pop", "random"]
        self.style_menu = tk.OptionMenu(style_frame, self.style_var, *styles)
        self.style_menu.config(bg="#313244", fg="#cdd6f4",
                               font=("Helvetica", 11),
                               activebackground="#45475a",
                               relief="flat", width=12)
        self.style_menu.grid(row=0, column=1, padx=10)

        # Length selection
        len_frame = tk.Frame(root, bg="#1e1e2e")
        len_frame.pack(pady=5)

        tk.Label(len_frame, text="Note Length:",
                 bg="#1e1e2e", fg="#a6adc8",
                 font=("Helvetica", 12)).grid(row=0, column=0, padx=10)

        self.length_var = tk.IntVar(value=32)
        tk.Scale(len_frame, from_=8, to=64,
                 orient="horizontal", variable=self.length_var,
                 bg="#1e1e2e", fg="#cdd6f4",
                 highlightthickness=0, length=200,
                 troughcolor="#313244").grid(row=0, column=1)

        # Generate button
        tk.Button(root, text="🎵 Generate Music",
                  command=self.generate,
                  bg="#89b4fa", fg="#1e1e2e",
                  font=("Helvetica", 13, "bold"),
                  padx=30, pady=8, relief="flat").pack(pady=20)

        # Output area
        tk.Label(root, text="Generated Note Sequence:",
                 bg="#1e1e2e", fg="#a6adc8",
                 font=("Helvetica", 11)).pack()

        self.output = scrolledtext.ScrolledText(
            root, height=10, width=65,
            bg="#313244", fg="#a6e3a1",
            font=("Courier", 10),
            relief="flat", state="disabled"
        )
        self.output.pack(padx=15, pady=8)

        # Save button
        tk.Button(root, text="💾 Save as MIDI",
                  command=self.save_midi,
                  bg="#a6e3a1", fg="#1e1e2e",
                  font=("Helvetica", 11, "bold"),
                  padx=20, pady=6, relief="flat").pack(pady=5)

        # Status
        self.status = tk.Label(root, text="Ready to generate!",
                                bg="#1e1e2e", fg="#6c7086",
                                font=("Helvetica", 9))
        self.status.pack()

        self.current_score = None

    def generate(self):
        if not MUSIC21_OK:
            messagebox.showerror("Error", "music21 not installed!\nRun: pip install music21")
            return

        style = self.style_var.get()
        length = self.length_var.get()
        self.status.config(text="🎵 Generating...")

        def run():
            try:
                score = generate_simple_music(style, length)
                self.current_score = score

                # Get note names
                notes_list = []
                for element in score.flatten().notes:
                    if isinstance(element, note.Note):
                        notes_list.append(element.nameWithOctave)
                    elif isinstance(element, chord.Chord):
                        notes_list.append(".".join(n.nameWithOctave for n in element.notes))

                display = " → ".join(notes_list)

                self.output.config(state="normal")
                self.output.delete("1.0", "end")
                self.output.insert("end", f"Style: {style.upper()}\n")
                self.output.insert("end", f"Notes: {length}\n\n")
                self.output.insert("end", display)
                self.output.config(state="disabled")
                self.status.config(text=f"✅ Generated {len(notes_list)} notes!")
            except Exception as e:
                self.status.config(text=f"❌ Error: {e}")

        threading.Thread(target=run, daemon=True).start()

    def save_midi(self):
        if not self.current_score:
            messagebox.showwarning("No Music", "Please generate music first!")
            return
        try:
            filename = f"generated_{self.style_var.get()}.mid"
            self.current_score.write("midi", fp=filename)
            self.status.config(text=f"💾 Saved as {filename}!")
            messagebox.showinfo("Saved!", f"MIDI file saved as:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save:\n{e}")

# ── Run ────────────────────────────────────────────────────
root = tk.Tk()
app = MusicGenApp(root)
root.mainloop()