import os
import cv2
import wavelink
from discord import Embed, User, Member
from sklearn.cluster import KMeans
import numpy as np
import urllib.request
from Saturn import get_bucket, get_server_translation, time_format, get_user, random_id

ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"
ICON_URLS = {
    "spotify": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png",
    "youtube": "https://yt3.googleusercontent.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s900-c-k-c0x00ffffff-no-rj"
}
music_files_bucket = get_bucket("storage/music")
DEFAULT_COLOR = 0x000000


def get_icon_url(requester):
    if isinstance(requester, Member):
        return ANON_AVATAR if not requester.avatar else requester.avatar.url
    return ICON_URLS[requester.lower()]


def get_color(thumbnail):
    # This function is under maintenance and may be removed in future versions.
    if thumbnail is None: return DEFAULT_COLOR
    filename = random_id() + ".jpg"
    real_filename = music_files_bucket.alloc_file(filename)
    urllib.request.urlretrieve(thumbnail, real_filename)
    try:
        img = cv2.imread(real_filename)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except cv2.error:
        print(f"ERROR [by CV2] : After operations imread, cvtColor | Returning {DEFAULT_COLOR}")
        return DEFAULT_COLOR
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
    music_files_bucket.Fdel(filename)
    return dc_color


def get_embed(player: wavelink.Player, track: wavelink.Playable, recommended):
    thumbnail = track.artwork
    title = track.title
    guild = player.guild
    author = track.author
    milliseconds = track.length
    if recommended:
        requester = track.source
        requester[0].upper()
        requester_name = requester
    else:
        requester = get_user(track.extras.requested_by, guild)
        requester_name = requester.name
    requester_icon_url = get_icon_url(requester)

    embed = Embed(color=DEFAULT_COLOR)
    embed.add_field(name=f"{get_server_translation(guild, 'now_playing')}{title}",
                    value=f"{get_server_translation(guild, 'by')}{author}\n{get_server_translation(guild, 'playing_for')}{time_format(milliseconds)}",
                    inline=False)
    if track.album.name is not None:
        embed.add_field(name="Album", value=track.album.name)
    if thumbnail is not None: embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=f"{get_server_translation(guild, 'requested_by')}{requester_name}",
                     icon_url=requester_icon_url)

    return embed
