import sys

from main import launch
import multiprocessing as mp
import subprocess as sbp
import sys

DISABLE_LAVALINK_OUTPUT = len(sys.argv) > 1 and sys.argv[1] in ["-dl", "--disable-lavalink"]


def start_lavalink():
    try:
        proc = sbp.Popen("java -jar Lavalink.jar", shell=True, stdout=sbp.PIPE if DISABLE_LAVALINK_OUTPUT else sys.stdout)
    except KeyboardInterrupt:
        proc.kill()


def main():
    try:
        lavalink_proc = mp.Process(target=start_lavalink)
        launch_proc = mp.Process(target=launch)
        print("Processes ready!")
        lavalink_proc.start()
        print("Lavalink started...", "[ENABLED INPUT]" if not DISABLE_LAVALINK_OUTPUT else "[DISABLED OUTPUT]")
        launch_proc.start()
        print("Launched Planet")
        print("===============")
        while True: pass
    except KeyboardInterrupt:
        print("Shutting down...")
        print("Terminating Lavalink")
        lavalink_proc.terminate()
        print("Done")
        print("Terminating Planet")
        launch_proc.terminate()
        print("Done")


if __name__ == '__main__':
    mp.freeze_support()
    main()
