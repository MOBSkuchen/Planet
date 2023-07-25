import pytube
import yt_dlp
import os
import cv2
from pytube import YouTube, Search, exceptions
from sklearn.cluster import KMeans
import numpy as np
import urllib.request
from Saturn.storage import get_bucket


music_files_bucket = get_bucket("storage/music")


class Goblin:
    def __init__(self, pytube_obj: pytube.YouTube):
        self.yt_obj = pytube_obj
        self.url = self.yt_obj.url
        self.filename = 'vid_' + self.yt_obj.video_id
        music_files_bucket.alloc_file(self.filename)
        self.color = self.get_color()

    def get_color(self):
        filename = self.filename + "_picture.jpg"
        music_files_bucket.alloc_file(filename)
        if not os.path.exists(filename):
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
        return s.results, s.completion_suggestions

    @staticmethod
    def from_query(query: str, selector: int = 0):
        r, _ = Goblin.search(query)
        return Goblin(r[0])

    @staticmethod
    def from_url(url: str):
        return Goblin(pytube.YouTube(url))
