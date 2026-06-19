import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from threading import Thread
import cv2
import os
from pathlib import Path
import imageio
import imageio_ffmpeg
import time

class SlowMoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SlowMo Pro - Video Slow Motion Maker")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main Frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎬 SlowMo Pro", font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(main_frame, text="Video Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(file_frame, text="Select Video File:").pack(anchor=tk.W, pady=5)
        
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(path_frame, text="Browse", command=self.browse, width=10).pack(side=tk.RIGHT)
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Speed Factor
        speed_frame = ttk.Frame(settings_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="Slow Motion Speed:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.speed_var = tk.StringVar(value="4")
        speed_spinbox = ttk.Spinbox(speed_frame, from_=2, to=10, textvariable=self.speed_var, width=10)
        speed_spinbox.pack(side=tk.LEFT)
        
        ttk.Label(speed_frame, text="x (1 = normal, higher = slower)").pack(side=tk.LEFT, padx=10)
        
        # Output Format
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, values=["mp4", "avi", "mov"], width=10)
        format_combo.pack(side=tk.LEFT)
        
        # Progress & Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=('Arial', 10))
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Log Area
        self.log = scrolledtext.ScrolledText(status_frame, height=8, font=('Consolas', 9))
        self.log.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="🚀 Start Processing", command=self.start_thread, width=20)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Exit", command=root.quit, width=10).pack(side=tk.RIGHT, padx=5)
        
        # Footer
        footer_label = ttk.Label(main_frame, text="Made with ❤️ | FFmpeg included", font=('Arial', 8))
        footer_label.pack(pady=5)

    def browse(self):
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.log_message(f"Selected: {os.path.basename(path)}")

    def clear_log(self):
        self.log.delete(1.0, tk.END)

    def log_message(self, message):
        self.log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log.see(tk.END)
        self.root.update()

    def start_thread(self):
        if not self.path_entry.get():
            messagebox.showerror("Error", "Please select a video file first!")
            return
        
        self.process_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.progress_var.set(0)
        self.status_label.config(text="Processing started...")
        self.log_message("=" * 50)
        self.log_message("Processing started!")
        
        Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            input_path = self.path_entry.get()
            speed_factor = int(self.speed_var.get())
            output_format = self.format_var.get()
            
            # Generate output path
            input_file = Path(input_path)
            output_file = input_file.parent / f"{input_file.stem}_slowmo.{output_format}"
            output_path = str(output_file)
            
            self.log_message(f"Input: {input_path}")
            self.log_message(f"Output: {output_path}")
            self.log_message(f"Speed Factor: {speed_factor}x")
            self.log_message(f"Format: {output_format}")
            
            # Open video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self.log_message(f"Video Info: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
            
            # Setup video writer
            if output_format == "mp4":
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            elif output_format == "avi":
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
            elif output_format == "mov":
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            else:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            out = cv2.VideoWriter(output_path, fourcc, fps / 2, (width, height))
            
            # Process frames
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Write frame multiple times for slow motion
                for _ in range(speed_factor):
                    out.write(frame)
                
                frame_count += 1
                
                # Update progress
                progress = (frame_count / total_frames) * 100
                self.progress_var.set(progress)
                self.status_label.config(text=f"Processing: {frame_count}/{total_frames} frames")
                
                if frame_count % 10 == 0:
                    self.log_message(f"Processed {frame_count}/{total_frames} frames")
            
            # Release resources
            cap.release()
            out.release()
            
            self.progress_var.set(100)
            self.status_label.config(text="✅ Processing complete!")
            self.log_message(f"✅ Success! Video saved as: {os.path.basename(output_path)}")
            self.log_message(f"Location: {output_path}")
            self.log_message("=" * 50)
            
            # Show completion message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Video processed successfully!\n\nSaved as: {os.path.basename(output_path)}"
            ))
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.log_message(error_msg)
            self.status_label.config(text="❌ Error occurred")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL, text="🚀 Start Processing"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SlowMoApp(root)
    root.mainloop()
