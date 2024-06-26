import threading
import customtkinter as ctk
from typing import Dict
from utils.utils import remove_ansi_escape_sequences

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class View(ctk.CTk):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.update_time = 1
        self.trim_view = None
        self.audio_settings_view = None
        self.initialize_interface()

    def initialize_interface(self):
        self.title("MP3 YouTube Downloader")
        self.geometry(f"{1200}x{480}")

        # Title
        self.title_label = ctk.CTkLabel(self, text="MP3 YouTube Downloader", font=("Fira Sans", 20, 'bold'))
        self.title_label.pack(pady=10)

        # URL
        self.url_label = ctk.CTkLabel(self, text="YouTube URL", font=("Fira Sans", 12))
        self.url_label.pack(padx=10, anchor='w')

        self.url_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.url_frame.pack(pady=5, padx=10, fill="x")

        self.url_entry = ctk.CTkEntry(self.url_frame, width=400, placeholder_text='Insert URL here')
        self.url_entry.pack(side="left", fill="x", expand=True)

        # Path saved files
        self.path_label = ctk.CTkLabel(self, text="Path of saved files", font=("Fira Sans", 12))
        self.path_label.pack(padx=10, anchor='w')

        self.path_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.path_frame.pack(pady=5, padx=10, fill="x")

        self.path_entry = ctk.CTkEntry(self.path_frame, width=400, placeholder_text=self.controller.default_save_dir)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.configure(state='disabled')

        # Set default path button
        self.default_path_button = ctk.CTkButton(self.path_frame, text="Set as default path", command=self.set_default_path)
        self.default_path_button.pack(side="right", padx=0)

        # Path edit button
        self.select_button = ctk.CTkButton(self.path_frame, text="Edit", command=self.select_directory)
        self.select_button.pack(side="right", padx=5)

        # Settings buttons
        self.settings_button_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.settings_button_frame.pack(pady=10)

        self.file_settings_button = ctk.CTkButton(self.settings_button_frame, text="Audio file settings", command=self.open_audio_file_settings_view)
        self.file_settings_button.pack(side="left")

        # Download and trim buttons
        self.action_button_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.action_button_frame.pack(pady=10)

        self.download_button = ctk.CTkButton(self.action_button_frame, text="Download", height=50, command=self.download)
        self.download_button.pack(side="left")

        self.trim_button = ctk.CTkButton(self.action_button_frame, text="Trim", height=50, command=self.open_trim_view)
        self.trim_button.pack(side="right", padx=20)

        # Download progress
        self.progress_label = ctk.CTkLabel(self, text="Download progress", font=("Fira Sans", 12))
        self.progress_label.pack(padx=10, anchor='w')

        self.progress_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.progress_frame.pack(pady=10, fill="x")

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=1000, height=20)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.progress_bar.set(0)

        self.progress_percentage = ctk.CTkLabel(self.progress_frame, text="0%", font=("Fira Sans", 12))
        self.progress_percentage.pack(side="left", padx=10)

        # Log
        self.progress_log_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.progress_log_frame.pack(pady=10, fill="x")

        self.progress_log = ctk.CTkLabel(self.progress_log_frame, text="", font=("Fira Sans", 12))
        self.progress_log.pack(side="left", fill="y", expand=True)

        # Updating values
        self.update_progress_bar()
        self.update_logs()

    def select_directory(self):
        path = ctk.filedialog.askdirectory(mustexist=True, title="Select directory to save files")
        if path:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, ctk.END)
            self.path_entry.insert(0, path)
            self.controller.save_dir = path
            self.path_entry.configure(state="disabled")
    
    def download(self):
        if not self.controller.state == self.controller.State.DOWNLOADING:
            self.controller.url = self.url_entry.get()
            download_thread = threading.Thread(target=self.controller.download)
            download_thread.start()

    def open_trim_view(self):
        self.previous_trim_settings = self.controller.save_trim_settings()
        self.controller.reset_trim_settings()
        if not self.trim_view:
            def start_trim_view():
                self.trim_view = TrimView(self)
                self.trim_view.mainloop()

            self.after(0, start_trim_view)
    
    def open_audio_file_settings_view(self):
        if not self.audio_settings_view:
            def start_audio_file_settings():
                self.audio_settings_view = AudioFileView(self)
                self.audio_settings_view.mainloop()

            self.after(0, start_audio_file_settings)
        
    def update_progress_bar(self):
        # Note: the state of the program is checked in order to avoid
        # useless computation when not needed
        match self.controller.state:
            case self.controller.State.REQUEST:
                self.progress_percentage.configure(text="0%")
                self.progress_bar.set(0)
            case self.controller.State.DOWNLOADING:
                progress_str = remove_ansi_escape_sequences(self.controller.download_status['progress'])
                self.progress_percentage.configure(text=f"{progress_str}")
                progress = float(progress_str.replace('%', ''))
                self.progress_bar.set(progress / 100)
            case self.controller.State.POSTPROCESSING:
                self.progress_percentage.configure(text="100%")
                self.progress_bar.set(1)
  
        # Update progress bar every n milliseconds
        self.after(self.update_time, self.update_progress_bar)
    
    def update_logs(self):
        match self.controller.state:
            case self.controller.State.REQUEST:
                self.progress_log.configure(text="Requesting information...")
            case self.controller.State.DOWNLOADING:
                self.progress_log.configure(text=f"Downloading... SPEED {self.controller.download_status['speed']} ETA {self.controller.download_status['eta']}")
            case self.controller.State.POSTPROCESSING:
                self.progress_log.configure(text="Postprocessing...")
            case self.controller.State.DONE:
                trim_info = "" if not self.controller.trimmed_download else f",\n{self.controller.trim_filepath}"
                self.progress_log.configure(text=f"Done! File saved at {self.controller.save_path}{trim_info}")
            case self.controller.State.TRIMMED:
                self.progress_log.configure(text=f"File trimmed and saved at {self.controller.trim_filepath}")
            case self.controller.State.SAVE_DIR_CHANGED:
                self.progress_log.configure(text=f"Default save directory changed to {self.controller.default_save_dir}")
            case self.controller.State.ERROR:
                self.progress_log.configure(text=f"An error occured: {self.controller.error_message}")
        
        # Update logs every n milliseconds
        self.after(self.update_time, self.update_logs)
    
    def set_trim_timestamp(self, event, entry, timestamp_config: Dict[str, str]) -> None:
        value = entry.get()
        value = 0 if value == '' else value
        
        try:
            value = float(value) if type(value) == str and '.' in value else int(value)
        except ValueError:
            return
        if value < 0:
            raise ValueError("Value must be a positive number!")
        
        TIMESTAMP_CONVERSION_DICT = {
            'hour': 0,
            'minute': 1,
            'second': 2
        }
        time_point = timestamp_config['point'] # Start or end
        time = TIMESTAMP_CONVERSION_DICT[timestamp_config['time']] # Hour, minute or second

        self.controller.trim_timestamps[time_point][time] = value
    
    def set_default_path(self):
        path = self.path_entry.get()
        if path != '':
            self.controller.set_default_save_dir(path)

class TrimView(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.transient(parent)
        self.initialize_interface()
        self.grab_set()

    def initialize_interface(self) -> None:
        self.title("Trim")
        self.geometry(f"{600}x{400}")

        self.label = ctk.CTkLabel(self, text="Trim")
        self.label.pack(pady=10)

        # Set filepath
        self.filepath_label = ctk.CTkLabel(self, text="File path", font=("Fira Sans", 12))
        self.filepath_label.pack(pady=5, padx=10, anchor='w')

        self.path_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.path_frame.pack(pady=10, padx=10, fill="x")

        self.path_entry = ctk.CTkEntry(self.path_frame, width=400, placeholder_text="File to be trimmed")
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.configure(state='disabled')

        self.select_button = ctk.CTkButton(self.path_frame, text="Select", command=self.select_file)
        self.select_button.pack(side="right", padx=5)

        # Trim settings
        self.label = ctk.CTkLabel(self, text="Trim file", font=("Fira Sans", 12))
        self.label.pack(pady=5, padx=10, anchor='w')

        self.trim_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.trim_frame.pack(pady=10)

        # Start time
        hour, minute,second = self.parent.controller.trim_timestamps['start']

        self.start_hour_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=hour if hour != 0 else "hh", justify="center")
        self.start_hour_entry.pack(padx=5, side="left")
        self.start_hour_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_hour_entry, timestamp_config={'point': 'start', 'time': 'hour'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.start_minute_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=minute if minute != 0 else "mm", justify="center")
        self.start_minute_entry.pack(padx=5, side="left")
        self.start_minute_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_minute_entry, timestamp_config={'point': 'start', 'time': 'minute'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.start_second_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=second if second != 0 else "ss", justify="center")
        self.start_second_entry.pack(padx=5, side="left")
        self.start_second_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_second_entry, timestamp_config={'point': 'start', 'time': 'second'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text="-", font=("Fira Sans", 12))
        self.separator_label.pack(padx=10, side="left")

        # End time
        hour, minute,second = self.parent.controller.trim_timestamps['end']

        self.end_hour_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=hour if hour != 0 else "hh", justify="center")
        self.end_hour_entry.pack(padx=5, side="left")
        self.end_hour_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_hour_entry, timestamp_config={'point': 'end', 'time': 'hour'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.end_minute_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=minute if minute != 0 else "mm", justify="center")
        self.end_minute_entry.pack(padx=5, side="left")
        self.end_minute_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_minute_entry, timestamp_config={'point': 'end', 'time': 'minute'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.end_second_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=second if second != 0 else "ss", justify="center")
        self.end_second_entry.pack(padx=5, side="left")
        self.end_second_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_second_entry, timestamp_config={'point': 'end', 'time': 'second'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        # Buttons
        self.bottom_buttons = ctk.CTkFrame(self, fg_color='transparent')
        self.bottom_buttons.pack(pady=15, fill="x", side="bottom")
        
        self.close_button = ctk.CTkButton(self.bottom_buttons, text="Trim", height=50, width=100, command=self.trim)
        self.close_button.pack(padx=10)
        
        self.close_button = ctk.CTkButton(self.bottom_buttons, text="Back", command=self.on_exit)
        self.close_button.pack(pady=15, side="bottom")

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        self.parent.controller.load_trim_settings(self.parent.previous_trim_settings)
        self.parent.trim_view = None
        self.destroy()
    
    def select_file(self):
        filepath = ctk.filedialog.askopenfilename(title="Select file to be trimmed")
        if filepath:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, ctk.END)
            self.path_entry.insert(0, filepath)
            self.path_entry.configure(state="disabled")
        # Avoids the window to hide behind every open window
        self.lift()
    
    def trim(self):
        if self.parent.controller.trim_timestamps_not_set:
            self.parent.controller.error_message = "Trim timestamps not set!"
            self.parent.controller.state = self.parent.controller.State.ERROR
            raise ValueError(self.parent.controller.error_message)
        if self.parent.controller.should_trim:
            self.parent.controller.trim_audio_file(self.path_entry.get())

class AudioFileView(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.transient(parent)
        self.initialize_interface()
    
    def initialize_interface(self) -> None:
        self.title("Audio settings")
        self.geometry(f"{400}x{250}")

        # Window title
        self.label = ctk.CTkLabel(self, text="Audio file settings", font=("Fira Sans", 12, "bold"))
        self.label.pack(pady=10)

        # File name
        self.label = ctk.CTkLabel(self, text="Custom file name", font=("Fira Sans", 12))
        self.label.pack(pady=5, padx=10, anchor='w')

        self.file_name_entry = ctk.CTkEntry(self, width=400, placeholder_text="Insert custom file name here" if self.parent.controller.custom_filename == "" else self.parent.controller.custom_filename)
        self.file_name_entry.pack(anchor="w", padx=10, fill="x")
        self.file_name_entry.bind("<KeyRelease>", self.set_file_name)

        # Trim settings
        self.label = ctk.CTkLabel(self, text="Trim file", font=("Fira Sans", 12))
        self.label.pack(pady=5, padx=10, anchor='w')

        self.trim_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.trim_frame.pack(pady=10)

        # Start time
        hour, minute,second = self.parent.controller.trim_timestamps['start']

        self.start_hour_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=hour if hour != 0 else "hh", justify="center")
        self.start_hour_entry.pack(side="left", padx=5)
        self.start_hour_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_hour_entry, timestamp_config={'point': 'start', 'time': 'hour'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.start_minute_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=minute if minute != 0 else "mm", justify="center")
        self.start_minute_entry.pack(side="left", padx=5)
        self.start_minute_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_minute_entry, timestamp_config={'point': 'start', 'time': 'minute'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.start_second_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=second if second != 0 else "ss", justify="center")
        self.start_second_entry.pack(side="left", padx=5)
        self.start_second_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.start_second_entry, timestamp_config={'point': 'start', 'time': 'second'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text="-", font=("Fira Sans", 12))
        self.separator_label.pack(side="left", padx=10)

        # End time
        hour, minute,second = self.parent.controller.trim_timestamps['end']
        
        self.end_hour_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=hour if hour != 0 else "hh", justify="center")
        self.end_hour_entry.pack(side="left", padx=5)
        self.end_hour_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_hour_entry, timestamp_config={'point': 'end', 'time': 'hour'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.end_minute_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=minute if minute != 0 else "mm", justify="center")
        self.end_minute_entry.pack(side="left", padx=5)
        self.end_minute_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_minute_entry, timestamp_config={'point': 'end', 'time': 'minute'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        self.separator_label = ctk.CTkLabel(self.trim_frame, text=":", font=("Fira Sans", 12))
        self.separator_label.pack(side="left")

        self.end_second_entry = ctk.CTkEntry(self.trim_frame, width=45, placeholder_text=second if second != 0 else "ss", justify="center")
        self.end_second_entry.pack(side="left", padx=5)
        self.end_second_entry.bind("<KeyRelease>", 
                                   lambda event, value=self.end_second_entry, timestamp_config={'point': 'end', 'time': 'second'}: 
                                   self.parent.set_trim_timestamp(event, value, timestamp_config))

        # Back button
        self.back_button = ctk.CTkButton(self, text="Back", command=self.on_exit)
        self.back_button.pack(pady=15, side="bottom")

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        self.parent.audio_settings_view = None
        self.destroy()

    def set_file_name(self, event) -> None:
        self.parent.controller.custom_filename = self.file_name_entry.get()
        