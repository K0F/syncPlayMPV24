import os
import time
from datetime import datetime, timedelta
from pymediainfo import MediaInfo
import subprocess
from threading import Thread

# Path to directory containing .wav files
AUDIO_DIR = "/home/kof/field"  # <-- Change this to your folder path
MPV_PATH = "mpv"  # Path to mpv executable, must be in your PATH

def extract_encoded_time(file_path):
    """
    Extract the 'encoded_date' from WAV file metadata and return its time (hh:mm:ss).
    """
    media_info = MediaInfo.parse(file_path)
    for track in media_info.tracks:
        if track.track_type == "General" and track.encoded_date:
            try:
                time_str = track.encoded_date.strip()
                parsed_date = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                return parsed_date.time()  # Extract just the time (hh:mm:ss)
            except ValueError as e:
                print(f"Error parsing date in {file_path}: {e}")
    return None

def parse_files(directory):
    """
    Parse WAV files in the directory and extract their encoded timestamps.
    Returns a list of (time, file_path) tuples.
    """
    files_with_times = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".wav"):
            file_path = os.path.join(directory, filename)
            file_time = extract_encoded_time(file_path)
            if file_time:
                files_with_times.append((file_time, file_path))
                print(f"File: {filename} | Encoded Time: {file_time}")
            else:
                print(f"Warning: No 'encoded_date' found for {filename}")
    return files_with_times

def play_at_time(file_path, start_time):
    """
    Waits until the system clock matches the start_time and then plays the file.
    """
    now = datetime.now()
    today_start_time = datetime.combine(now.date(), start_time)  # Align to today

    # If the target time has already passed today, schedule it for tomorrow
    if today_start_time < now:
        today_start_time += timedelta(days=1)

    delay = (today_start_time - now).total_seconds()
    print(f"Waiting {delay:.2f} seconds to play {file_path}...")
    time.sleep(max(0, delay))  # Ensure no negative delays

    print(f"Playing {file_path} at {datetime.now()} (Scheduled: {today_start_time})")
    subprocess.run([MPV_PATH, "--no-video", file_path])

if __name__ == "__main__":
    print("Scanning for WAV files and extracting encoded times...")
    files = parse_files(AUDIO_DIR)

    if not files:
        print("No valid WAV files found. Exiting.")
        exit()

    # Sort files by encoded time
    files.sort(key=lambda x: x[0])

    print("\nPlayback Schedule:")
    for file_time, file_path in files:
        today_start_time = datetime.combine(datetime.now().date(), file_time)
        if today_start_time < datetime.now():
            today_start_time += timedelta(days=1)
        print(f"{today_start_time} - {os.path.basename(file_path)}")

    print("\nScheduling playback...")
    threads = []
    for file_time, file_path in files:
        # Schedule each file to play at its adjusted time for today
        thread = Thread(target=play_at_time, args=(file_path, file_time))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("\nPlayback complete.")
