import pytube
import yt_dlp
import os
import cv2
from sklearn.cluster import KMeans
import numpy as np
import urllib.request
from Saturn import get_bucket
from discord import FFmpegPCMAudio
from urllib.request import urlopen


ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
os.environ["FFMPEG_EXE"] = "C:/Driver/ffmpeg/ffmpeg.exe"
FFMPEG = os.environ.get("FFMPEG_EXE")
music_files_bucket = get_bucket("storage/music")
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

def wrap(url):
    return FFmpegPCMAudio(urlopen(url), pipe=True, executable=FFMPEG)


class Goblin:
    def __init__(self, pytube_obj: pytube.YouTube):
        self.yt_obj = pytube_obj
        self.title = self.yt_obj.title
        self.thumbnail = self.yt_obj.thumbnail_url
        self.author = self.yt_obj.author
        self.seconds = self.yt_obj.length
        self.url = self.yt_obj.watch_url
        self.filename = 'vid_' + self.yt_obj.video_id + ".mp3"
        self.filename = music_files_bucket.alloc_file(self.filename)  # Pretend like file exists
        try:
            self.color = self.get_color()
        except:
            self.color = 0x000000

    def get_color(self):
        filename = self.filename + "_picture.jpg"
        music_files_bucket.alloc_file(filename)
        if not music_files_bucket.exists(os.path.basename(filename)):
            urllib.request.urlretrieve(self.thumbnail, filename)
        try:
            img = cv2.imread(filename)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except cv2.error:
            return 0x000000
        reshape = img.reshape((img.shape[0] * img.shape[1], 3))
        cluster = KMeans(n_clusters=5).fit(reshape)
        centroids = cluster.cluster_centers_
        labels = np.arange(0, len(np.unique(cluster.labels_)) + 1)
        hist, _ = np.histogram(cluster.labels_, bins=labels)
        hist = hist.astype("float")
        hist /= hist.sum()
        colors = sorted([(percent, color) for (percent, color) in zip(hist, centroids)])
        color = int("0x" + '%02x%02x%02x' % tuple(int(c) for c in colors[len(colors) - 1][1]), base=16)
        dc_color = color
        return dc_color

    @staticmethod
    def search(query: str):
        s = pytube.Search(query)
        try:
            cr = s.completion_suggestions
        except:
            cr = []
        return s.results, cr

    @staticmethod
    def from_query(query: str, selector: int = 0):
        r, _ = Goblin.search(query)
        return Goblin(r[selector])

    @staticmethod
    def from_url(url: str):
        return Goblin(pytube.YouTube(url))

    async def get(self):
        data = ytdl.extract_info(self.url, download=False)
        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]
        url = data["url"]
        return wrap(url)

    # Fallback
    async def download(self):
        if os.path.exists(self.filename):
            return wrap(self.filename)
        video_info = yt_dlp.YoutubeDL().extract_info(
            url=self.url, download=False
        )
        options = {
            'format': 'bestaudio/best',
            'keepvideo': False,
            'outtmpl': self.filename,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_info['webpage_url']])

        return wrap(self.filename)
