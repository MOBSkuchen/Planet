from main import launch
from Saturn import SPOTIFY_ENABLED, SPOTIFY, DISABLE_PLAYBACK
import multiprocessing as mp
import subprocess as sbp
import sys

DISABLE_LAVALINK_OUTPUT = len(sys.argv) > 1 and sys.argv.pop(1).lower() in ["-dl", "--disable-lavalink"]
OVERWRITE_LAVALINK_APP_YML = len(sys.argv) > 1 and sys.argv.pop(1).lower() in ["-ol", "--overwrite-lavalink"]
LAVALINK_FILE_CONTENT = None


def start_lavalink(out):
    try:
        out = -1 if out else sys.stdout
        proc = sbp.Popen("java -jar Lavalink.jar", shell=True, stdout=out)
    except KeyboardInterrupt:
        proc.kill()


def overwrite_lavalink(filename="application.yml"):
    global LAVALINK_FILE_CONTENT
    if not SPOTIFY_ENABLED: return
    with open(filename, "r") as file:
        content = file.read()
        LAVALINK_FILE_CONTENT = content
        content = content.replace("$spotify/client-id", SPOTIFY["client-id"])
        content = content.replace("$spotify/client-secret", SPOTIFY["client-secret"])
        content = content.replace("$spotify/enable", "true" if SPOTIFY_ENABLED else "false")
    with open(filename, "w") as file:
        file.write(content)


def revert_lavalink(filename="application.yml"):
    if LAVALINK_FILE_CONTENT is None: return
    with open(filename, "w") as file:
        file.write(LAVALINK_FILE_CONTENT)


def main():
    try:
        lavalink_proc = mp.Process(target=start_lavalink, args=[DISABLE_LAVALINK_OUTPUT])
        launch_proc = mp.Process(target=launch)
        print("Processes ready!")
        if (not DISABLE_PLAYBACK) and OVERWRITE_LAVALINK_APP_YML:
            overwrite_lavalink()
        if not DISABLE_PLAYBACK:
            lavalink_proc.start()
            print("Lavalink started...", "[ENABLED OUTPUT]" if not DISABLE_LAVALINK_OUTPUT else "[DISABLED OUTPUT]", "[OVERWROTE LAVALINK application.yml]" if OVERWRITE_LAVALINK_APP_YML else "")
        launch_proc.start()
        print("Launched Planet")
        print("===============")
        while True: pass
    except KeyboardInterrupt:
        print("Shutting down...")
        if not DISABLE_PLAYBACK:
            print("Terminating Lavalink")
            lavalink_proc.terminate()
            print("Done")
        print("Terminating Planet")
        launch_proc.terminate()
        print("Done")
        if (not DISABLE_PLAYBACK) and OVERWRITE_LAVALINK_APP_YML and LAVALINK_FILE_CONTENT is not None:
            print("Reverting application.yml")
            revert_lavalink()
            print("Done")


if __name__ == '__main__':
    mp.freeze_support()
    main()
