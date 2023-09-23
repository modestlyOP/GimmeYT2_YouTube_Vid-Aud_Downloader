import shlex
import customtkinter
from tkinter import StringVar
from tkinter import filedialog
import pytube.exceptions
import os
from platform import system as os_type
import time
from ffmpeg_progress_yield import FfmpegProgress
from pytube import YouTube, exceptions as pytube_exceptions

# system settings:
customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("green")

# run app:
class YoutubeDownloader(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # app frame:
        self.geometry("720x280")
        self.resizable(width=False, height=False)
        self.title("GimmeYT2 - YouTube Downloader")

        # global storages:
        self.url_var = StringVar()

        # define UI elements:
        ## main parts
        self.lbl_vidTitle = customtkinter.CTkLabel(self, text="Insert a YouTube link")         #initialized text is replaced with vid title after link has been processed
        self.ent_linkInput = customtkinter.CTkEntry(self, width=350, height=40, textvariable=self.url_var)
        self.lbl_progressLabel = customtkinter.CTkLabel(self, text="")          #text is updated after file is downloaded or during that process, if necessary
        ### progressbar and label
        self.lbl_progressPercent = customtkinter.CTkLabel(self, text="0%")
        self.prgbr_progressbar = customtkinter.CTkProgressBar(self, width=400)
        self.prgbr_progressbar.set(0)
        ##download buttons + frame
        self.frm_dlFrame = customtkinter.CTkFrame(self)
        self.btn_dlBtn_vid = customtkinter.CTkButton(self.frm_dlFrame, text="Download .MP4", command=self.startDownload_vid)
        self.btn_dlBtn_aud = customtkinter.CTkButton(self.frm_dlFrame, text="Download .MP3", command=self.startDownload_aud)

        # UI elements placement
        self.lbl_vidTitle.pack(padx=10, pady=10)
        self.ent_linkInput.pack(padx=10, pady=10)
        self.lbl_progressLabel.pack(padx=10, pady=10)
        self.lbl_progressPercent.pack()
        self.prgbr_progressbar.pack(padx=10, pady=10)
        self.frm_dlFrame.pack()
        self.btn_dlBtn_vid.grid(row=0, column=0, padx=10, pady=10)
        self.btn_dlBtn_aud.grid(row=0, column=1, padx=10, pady=10)

    # filesave prompt:
    def promptFilesave(self):
        return filedialog.askdirectory()

    # download function:
    def startDownload_vid(self):
        try:
            storeDirPath = self.promptFilesave()
            if os_type() == 'Windows':
                storeDirPath = storeDirPath.replace("/", "\\")
            self.lbl_progressLabel.configure(text="Downloading...")
            ytlink = self.ent_linkInput.get()
            ytObject = YouTube(ytlink, on_progress_callback=self.on_progress)
            video = ytObject.streams.get_highest_resolution()
            self.lbl_vidTitle.configure(text=f"\"{ytObject.title}\" uploaded by {ytObject.author}")
            self.lbl_progressLabel.configure(text="")
            storeFilePath = os.path.join(storeDirPath, video.default_filename)
            print(storeFilePath)
            if os.path.exists(storeFilePath):
                self.lbl_progressLabel.configure(text="Video file already exists", text_color="yellow")
            else:
                video.download(output_path=storeDirPath)
                self.lbl_progressLabel.configure(text=f"Download Complete\nFile saved to {storeFilePath}", text_color="green")
        except pytube_exceptions.AgeRestrictedError:
            self.lbl_progressLabel.configure(text="Video is age-restricted and cannot be accessed without logging in", text_color="red")
        except (pytube.exceptions.RegexMatchError, pytube.exceptions.VideoUnavailable):
            self.lbl_progressLabel.configure(text="Link invalid or does not contain accessible video", text_color="red")

    def startDownload_aud(self):
        try:
            storeDirPath = self.promptFilesave()
            if os_type() == 'Windows':
                storeDirPath = storeDirPath.replace("/", "\\")
            self.lbl_progressLabel.configure(text="Downloading Source...", text_color="white")
            ytlink = self.ent_linkInput.get()
            ytObject = YouTube(ytlink, on_progress_callback=self.on_progress)
            audio = ytObject.streams.filter(only_audio=True).first()
            self.lbl_vidTitle.configure(text=f"\"{ytObject.title}\" uploaded by {ytObject.author}")
            cleanTitle = os.path.splitext(audio.default_filename.strip())[0]
            path_tempFile_mp4 = os.path.join(storeDirPath, audio.default_filename)
            if os.path.exists(os.path.join(storeDirPath, cleanTitle + ".mp3")):
                self.lbl_progressLabel.configure(text="Audio file already exists", text_color="yellow")
            else:
                audio.download(output_path=storeDirPath, filename=audio.default_filename)
                self.lbl_progressLabel.configure(text="")
                time.sleep(2)
                self.convert_aud2mp3(cleanTitle, storeDirPath, path_tempFile_mp4)
                os.remove(path_tempFile_mp4)
        except pytube_exceptions.AgeRestrictedError:
            self.lbl_progressLabel.configure(text="Video is age-restricted and cannot be accessed without logging in", text_color="red")
        except (pytube.exceptions.RegexMatchError, pytube.exceptions.VideoUnavailable):
            self.lbl_progressLabel.configure(text="Link invalid or does not contain accessible video", text_color="red")

    def convert_aud2mp3(self, name, path_storedir, path_source):
        # reset progressbar and update progress % label
        self.lbl_progressLabel.configure(text="Converting...", text_color="white")
        self.lbl_progressPercent.configure(text="0%")
        self.prgbr_progressbar.set(0)
        # conversion to mp3 from mp4:
        path_outputfile = os.path.join(path_storedir, name.strip() + ".mp3")
        cmd = (
            f'ffmpeg -i "{path_source}" -vn -b:a 192k -y "{path_outputfile}"'
        )
        process = FfmpegProgress(shlex.split(cmd))

        # update progressbar with percent completed
        for progress in process.run_command_with_progress():
            self.lbl_progressPercent.configure(text=f"{progress}%")
            self.lbl_progressPercent.update()
            self.prgbr_progressbar.set(progress / 100)
            print(f"{progress}/100")

        self.lbl_progressLabel.configure(text=f"Conversion Complete\nFile saved to {path_outputfile}", text_color="green")


    def on_progress(self, stream, chunk, bytes_remaining):
        #self.finishedLabel.configure(text="Downloading Source...")
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_complete = bytes_downloaded / total_size * 100
        per = str(int(percentage_complete))
        self.lbl_progressPercent.configure(text=f"{per}%")
        self.lbl_progressPercent.update()
        self.prgbr_progressbar.set(float(percentage_complete) / 100)


if __name__ == "__main__":
    app = YoutubeDownloader()
    app.mainloop()
