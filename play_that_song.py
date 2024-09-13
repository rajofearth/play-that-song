import os
import sys
import pygame
import curses
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import time
import random
import pathlib

class MP3Player:
    def __init__(self, mp3_files):
        self.mp3_files = mp3_files
        self.current_file_index = 0
        self.playing = False
        self.paused = False
        self.current_position = 0
        pygame.mixer.init()
        self.load_current_file()
        self.repeat_mode = 0  # 0: no repeat, 1: repeat one, 2: repeat all
        self.volume = 0.5
        self.shuffle = False
        pygame.mixer.music.set_volume(self.volume)

    def load_current_file(self):
        pygame.mixer.music.load(self.mp3_files[self.current_file_index])
        self.audio = MP3(self.mp3_files[self.current_file_index])
        self.duration = self.audio.info.length

    def play(self):
        if self.paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.play(start=self.current_position)
        self.playing = True
        self.paused = False

    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.current_position = 0

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True

    def unpause(self):
        pygame.mixer.music.unpause()
        self.paused = False

    def set_volume(self, volume):
        self.volume = max(0, min(1, volume))
        pygame.mixer.music.set_volume(self.volume)

    def seek(self, position):
        self.current_position = max(0, min(self.duration, position))
        if self.playing:
            pygame.mixer.music.play(start=self.current_position)

    def get_current_position(self):
        if self.playing:
            return pygame.mixer.music.get_pos() / 1000 + self.current_position
        return self.current_position

    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle

    def next_track(self):
        if self.shuffle:
            self.current_file_index = random.randint(0, len(self.mp3_files) - 1)
        else:
            self.current_file_index = (self.current_file_index + 1) % len(self.mp3_files)
        self.load_current_file()
        self.current_position = 0
        self.play()

    def previous_track(self):
        if self.shuffle:
            self.current_file_index = random.randint(0, len(self.mp3_files) - 1)
        else:
            self.current_file_index = (self.current_file_index - 1) % len(self.mp3_files)
        self.load_current_file()
        self.current_position = 0
        self.play()

    def set_music_folder(self, folder_path):
        expanded_path = os.path.expanduser(folder_path)
        if os.path.isdir(expanded_path):
            self.mp3_files = [os.path.join(expanded_path, f) for f in os.listdir(expanded_path) if f.lower().endswith('.mp3')]
            if not self.mp3_files:
                return False
            self.current_file_index = 0
            self.load_current_file()
            return True
        return False

def get_mp3_metadata(mp3_file):
    try:
        audio = ID3(mp3_file)
        title = str(audio.get('TIT2', ['Unknown Title'])[0])
        artist = str(audio.get('TPE1', ['Unknown Artist'])[0])
        album = str(audio.get('TALB', ['Unknown Album'])[0])
        return title, artist, album
    except Exception as e:
        print(f"Error reading MP3 metadata: {e}")
        return 'Unknown Title', 'Unknown Artist', 'Unknown Album'

def format_time(seconds):
    return time.strftime('%M:%S', time.gmtime(seconds))

def draw_progress_bar(stdscr, current, total, width, y, x):
    bar_width = width - 15  # Reserve space for time stamps
    filled_width = int(bar_width * (current / total))
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    current_str = format_time(current)
    total_str = format_time(total)
    stdscr.addstr(y, x, f"{current_str} {bar} {total_str}")

def draw_volume_bar(stdscr, volume, width, y, x):
    bar_width = min(20, width - 20)  # Limit bar width
    filled_width = int(bar_width * volume)
    bar = '█' * filled_width + '▒' * (bar_width - filled_width)
    vol_percent = int(volume * 100)
    stdscr.addstr(y, x, f"Volume: [{bar}] {vol_percent}%")

def draw_bordered_text(stdscr, text, y, x, width):
    stdscr.addstr(y, x, '╔' + '═' * (width - 2) + '╗')
    stdscr.addstr(y + 1, x, f'║{text.center(width - 2)}║')
    stdscr.addstr(y + 2, x, '╚' + '═' * (width - 2) + '╝')

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    # Set up color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)

    # Default music directory
    music_dir = r"C:\Users\ITFACT\Music\Liked"
    mp3_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.lower().endswith('.mp3')]

    if not mp3_files:
        stdscr.addstr(0, 0, f"No MP3 files found in {music_dir}")
        stdscr.getch()
        return

    player = MP3Player(mp3_files)
    playlist = [os.path.basename(f) for f in mp3_files]

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.bkgd(' ', curses.color_pair(1))

        current_file = mp3_files[player.current_file_index]
        title, artist, album = get_mp3_metadata(current_file)

        # Now Playing
        draw_bordered_text(stdscr, "Now Playing", 0, 0, width)
        stdscr.addstr(4, 2, f"♫ {title[:width-4]}")
        stdscr.addstr(5, 4, f"by {artist[:width-6]}")
        stdscr.addstr(6, 4, f"Album: {album[:width-11]}")

        # Playlist
        playlist_start = 9
        draw_bordered_text(stdscr, "Playlist", playlist_start, 0, width)
        visible_playlist = playlist[player.current_file_index:] + playlist[:player.current_file_index]
        for i, track in enumerate(visible_playlist):
            if playlist_start + i + 3 < height - 10:
                if i == 0:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(playlist_start + i + 3, 2, f"> {track[:width-4]}")
                    stdscr.attroff(curses.color_pair(2))
                else:
                    stdscr.addstr(playlist_start + i + 3, 2, f"  {track[:width-4]}")

        # Status
        status = "▶ Playing" if player.playing and not player.paused else "⏸ Paused" if player.paused else "⏹ Stopped"
        repeat_status = ["🔁 Off", "🔂 One", "🔁 All"][player.repeat_mode]
        shuffle_status = "🔀 On" if player.shuffle else "🔀 Off"
        status_line = f"{status} | Repeat: {repeat_status} | Shuffle: {shuffle_status}"
        draw_bordered_text(stdscr, status_line, height - 9, 0, width)

        # Progress bar
        current_pos = player.get_current_position()
        draw_progress_bar(stdscr, current_pos, player.duration, width, height - 6, 0)

        # Volume bar
        draw_volume_bar(stdscr, player.volume, width, height - 4, 0)

        # Controls adjusted for better fit
        controls = [
            "P: Play/Pause", "S: Stop", "R: Repeat", "H: Shuffle",
            "N: Next", "B: Previous", "←/→: Seek", "↑/↓: Volume", "F: Folder", "Q: Quit"
        ]
        max_controls = min(len(controls), width // 10)  # Adjust this based on how wide each control text is
        visible_controls = controls[:max_controls]

        for i, control in enumerate(visible_controls):
            stdscr.addstr(height - 2, i * (width // max_controls), control[:width // max_controls - 1])
        stdscr.refresh()

        c = stdscr.getch()
        if c == ord('p'):
            if player.playing and not player.paused:
                player.pause()
            else:
                player.play()
        elif c == ord('s'):
            player.stop()
        elif c == ord('r'):
            player.toggle_repeat()
        elif c == ord('h'):
            player.toggle_shuffle()
        elif c == ord('n'):
            player.next_track()
        elif c == ord('b'):
            player.previous_track()
        elif c == curses.KEY_LEFT:
            player.seek(current_pos - 5)
        elif c == curses.KEY_RIGHT:
            player.seek(current_pos + 5)
        elif c == curses.KEY_UP:
            player.set_volume(player.volume + 0.05)
        elif c == curses.KEY_DOWN:
            player.set_volume(player.volume - 0.05)
        elif c == ord('f'):
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter the path to your music folder (use '~/Music/') or press ESC to cancel: ")
            stdscr.refresh()

            folder_path = ""
            while True:
                c = stdscr.getch()

                if c == curses.KEY_BACKSPACE or c == 127:  # Handle backspace
                    folder_path = folder_path[:-1]
                elif c == 27:  # ESC key to exit
                    break
                elif c == 10:  # Enter key
                    folder_path = os.path.expanduser(folder_path.strip())  # Expand '~/...' to a full path
                    if os.path.isdir(folder_path):
                        mp3_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
                        if mp3_files:
                            player.mp3_files = mp3_files
                            player.current_file_index = 0
                            player.load_current_file()
                            player.stop()  # Stop any currently playing track
                            playlist = [os.path.basename(f) for f in mp3_files]
                            break
                        else:
                            stdscr.addstr(2, 0, "No MP3 files found in the folder. Press any key to try again.")
                            stdscr.refresh()
                            stdscr.getch()
                    else:
                        stdscr.addstr(2, 0, "Invalid folder path. Press any key to try again.")
                        stdscr.refresh()
                        stdscr.getch()
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Enter the path to your music folder (use '~/Music/') or press ESC to cancel: ")
                else:
                    if 32 <= c <= 126:  # Allow printable characters only
                        folder_path += chr(c)

                stdscr.addstr(1, 0, folder_path + ' ' * (width - len(folder_path)))
                stdscr.refresh()

        elif c == ord('q'):
            break

        # Handle repeat mode and end of song
        if current_pos >= player.duration:
            if player.repeat_mode == 1:  # Repeat One
                player.seek(0)
                player.play()
            elif player.repeat_mode == 2:  # Repeat All
                player.next_track()
            else:  # No Repeat
                player.next_track()

    pygame.mixer.quit()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)