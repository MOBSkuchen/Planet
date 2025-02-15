import cv2
import wavelink
from discord import Embed
import numpy as np
import urllib.request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from Saturn import get_bucket, get_server_translation, time_format, get_user, random_id, get_icon_url, SPOTIFY, SPOTIFY_ENABLED, AUDIO_SRC_PREF, Logger

logger = Logger("Goblin", dumpfile="goblin.log")
music_files_bucket = get_bucket("storage/music")
DEFAULT_COLOR = 0x000000

if SPOTIFY_ENABLED:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY["client-id"],
                                                               client_secret=SPOTIFY["client-secret"]))
    logger.log("Created spotify client")
else:
    sp = None


def get_color(thumbnail: str | None):
    """
    Gets the dominant color of an image
    :param thumbnail:
    Image URL (may be none)
    :return:
    The dominant color of the image (HEX),
    returns DEFAULT_COLOR if <thumbnail> is None
    """
    if thumbnail is None:
        logger.log(f"Thumbnail is None, returning DEFAULT_COLOR ({DEFAULT_COLOR})")
        return DEFAULT_COLOR
    filename = random_id() + ".jpg"
    real_filename = music_files_bucket.alloc_file(filename)
    urllib.request.urlretrieve(thumbnail, real_filename)
    image = cv2.imread(real_filename)
    pixels = image.reshape((-1, 3))
    pixels = np.float32(pixels)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, center = cv2.kmeans(pixels, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    dominant_color = center[np.argmax(np.unique(labels, return_counts=True)[1])]
    dominant_color = list(dominant_color)
    dominant_color = int("0x" + '%02x%02x%02x' % tuple(int(c) for c in dominant_color), base=16)
    music_files_bucket.file_delete(filename)
    logger.log(f"Returned dominant color: {dominant_color}")
    return dominant_color


def get_embed(player: wavelink.Player, track: wavelink.Playable, recommended: bool):
    """
    Gets the embed for music playback
    :param player:
    The current player
    :param track:
    The track that is now played
    :param recommended:
    Whether this track was recommended by the playback API or requested by a user
    :return:
    Return the full embed of this track
    """
    thumbnail = track.artwork
    title = track.title
    guild = player.guild
    author = track.author
    milliseconds = track.length
    if recommended:
        requester = track.source
        requester[0].upper()
        requester_name = requester.capitalize()
        logger.log("Preparing recommended track")
    else:
        requester = get_user(track.extras.requested_by, guild)
        requester_name = requester.name
        logger.log("Preparing requested track")
    requester_icon_url = get_icon_url(requester)

    embed = Embed(color=get_color(thumbnail))
    embed.add_field(name=f"{get_server_translation(guild, 'now_playing', title=title)}",
                    value=f"{get_server_translation(guild, 'by', by=author)}\n{get_server_translation(guild, 'playing_for', duration=time_format(milliseconds))}",
                    inline=False)
    if track.album.name is not None:
        embed.add_field(name="Album", value=track.album.name)
    if thumbnail is not None: embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=get_server_translation(guild, 'requested_by', by=requester_name),
                     icon_url=requester_icon_url)
    logger.log("Returned track")
    return embed


async def _search_ytm(query: str) -> wavelink.Search:
    logger.log("Returning YouTube Music track")
    return await wavelink.Playable.search(query)


async def _search_spotify(query: str):
    track_url = sp.search(q=query, limit=1)["tracks"]["items"][0]["external_urls"]["spotify"]
    playable = await wavelink.Playable.search(track_url)
    logger.log(f"Returning spotify track: {track_url}")
    return playable


async def multi_source_search(query: str, audio_source: str):
    audio_source = audio_source.lower()
    logger.log(f"Search query for: {query} ({audio_source})")
    if SPOTIFY_ENABLED and (audio_source == 'spotify'):
        return await _search_spotify(query)
    elif audio_source == 'youtube':
        return await _search_ytm(query)
    else:
        return await multi_source_search(query, AUDIO_SRC_PREF)
