import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import threading
import time
import os

class MediaDisplay:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.media_label = tk.Label(parent_frame, bg="black")
        self.media_label.pack(pady=10)
        self.current_media_thread = None
        self.stop_video_flag = False
        self.loop_video = True

    def display_image(self, image_path):
        self.stop_current_media()
        self.media_label.config(image='', bg="black")
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return
        try:
            img = Image.open(image_path)
            img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.media_label.config(image=photo, bg="black")
            self.media_label.image = photo
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.media_label.config(image='', bg="black")

    def play_video(self, video_path, loop=True):
        self.stop_current_media()
        self.media_label.config(image='', bg="black")
        self.loop_video = loop
        self.stop_video_flag = False

        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            self.media_label.config(image='', bg="black")
            return

        self.current_media_thread = threading.Thread(target=self._play_video_thread, args=(video_path,))
        self.current_media_thread.daemon = True
        self.current_media_thread.start()

    def _play_video_thread(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path} within thread.")
            self.parent_frame.after(0, lambda: self.media_label.config(image='', bg="black"))
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        delay = 1 / fps if fps > 0 else 0.033

        while not self.stop_video_flag:
            ret, frame = cap.read()
            if not ret:
                if self.loop_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        break
                else:
                    break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image=img)

            self.parent_frame.after(0, lambda p=photo: self.media_label.config(image=p, bg="black"))
            self.parent_frame.after(0, lambda p=photo: setattr(self.media_label, 'image', p))

            time.sleep(delay)

        cap.release()
        if not self.stop_video_flag and not self.loop_video:
            self.parent_frame.after(0, lambda: self.media_label.config(image='', bg="black"))

    def stop_current_media(self):
        self.stop_video_flag = True
        if self.current_media_thread and self.current_media_thread.is_alive():
            self.current_media_thread.join(timeout=0.2)
        self.media_label.config(image='', bg="black")
        self.media_label.image = None

class TreasureIslandGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Treasure Island Adventure")

        # --- IMPORTANT: Clear all existing widgets before setting up new ones ---
        self.clear_all_widgets()

        self.story_text = tk.StringVar()
        self.buttons = []

        self.media_display = MediaDisplay(root)

        self.story_label = tk.Label(root, textvariable=self.story_text, wraplength=500, font=("Helvetica", 14), justify="left", padx=10, pady=10)
        self.story_label.pack(pady=10)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack()

        self.state = "start"
        self.update_story("Welcome to Treasure Island!\nYour mission is to find the treasure!\n\nYou're at a crossroad.")
        self.media_display.play_video("cross road.mp4")
        self.set_buttons(["Left", "Right", "Straight"], self.crossroad_choice)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def clear_all_widgets(self):
        # Stop any active media before destroying widgets
        if hasattr(self, 'media_display') and self.media_display:
            self.media_display.stop_current_media()

        # Destroy all child widgets in the root window
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_closing(self):
        self.media_display.stop_current_media()
        self.root.destroy()

    def update_story(self, text):
        self.story_text.set(text)

    def clear_buttons(self):
        for b in self.buttons:
            b.destroy()
        self.buttons = []

    def set_buttons(self, options, command):
        self.clear_buttons()
        for opt in options:
            btn = tk.Button(self.button_frame, text=opt, width=20, command=lambda o=opt: command(o))
            btn.pack(pady=5)
            self.buttons.append(btn)

    # ---- Game Logic Begins ----

    def crossroad_choice(self, choice):
        if choice == "Left":
            self.state = "ocean"
            self.update_story("You've arrived at the ocean.\nWill you wait or explore?")
            self.media_display.play_video("ocean_wait (1).mp4")
            self.set_buttons(["Wait", "Explore"], self.ocean_choice)
        elif choice == "Right":
            self.update_story("You reached a desert and died of heat and thirst. GAME OVER!")
            self.media_display.play_video("desert (1).mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))
        elif choice == "Straight":
            self.update_story("You're lost in a jungle.\nDo you want to keep walking?")
            self.media_display.play_video("jungle.mp4")
            self.set_buttons(["Yes", "No"], self.jungle_choice)

    def jungle_choice(self, choice):
        if choice == "Yes":
            self.update_story("You walked into a lion's den.\nYou’re now their lunch. GAME OVER!")
            self.media_display.play_video("lion.mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))
        else:
            self.update_story("You stayed in place. A grizzly bear found you.\nGAME OVER!")
            self.media_display.play_video("bear.mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def ocean_choice(self, choice):
        if choice == "Wait":
            self.update_story("You waited for too long.\nNo ship arrived. GAME OVER!")
            self.media_display.play_video("ocean_wait (1).mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))
        else:
            self.update_story("You find a lighthouse. Ask for help?")
            self.media_display.play_video("found a light house.mp4")
            self.set_buttons(["Yes", "No"], self.lighthouse_choice)

    def lighthouse_choice(self, choice):
        if choice == "Yes":
            self.update_story("The lighthouse is empty.\nContinue alone?")
            self.media_display.play_video("empty_lighthouse.mp4")
            self.set_buttons(["Yes", "No"], self.search_choice)
        else:
            self.update_story("Too arrogant to ask for help. GAME OVER!")
            self.media_display.stop_current_media()
            self.root.after(0, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(3000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def search_choice(self, choice):
        if choice == "Yes":
            self.update_story("You found a tree.\nDo you want to chop it?")
            self.media_display.play_video("found a tree.mp4")
            self.set_buttons(["Yes", "No"], self.tree_choice)
        else:
            self.update_story("You gave up and got lost. GAME OVER!")
            self.media_display.stop_current_media()
            self.root.after(0, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(3000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def tree_choice(self, choice):
        if choice == "Yes":
            self.update_story("You built a boat and sailed to an island.\nCan you see land?")
            self.media_display.play_video("boating.mp4")
            self.set_buttons(["Yes", "No"], self.boat_choice)
        else:
            self.update_story("Good intentions won't save you here. GAME OVER!")
            self.media_display.stop_current_media()
            self.root.after(0, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(3000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def boat_choice(self, choice):
        if choice == "Yes":
            self.update_story("You reach the island.\nThree doors: Red, Blue, or Black?")
            self.media_display.stop_current_media()
            self.set_buttons(["Red", "Blue", "Black"], self.door_choice)
        else:
            self.update_story("You got lost at sea. GAME OVER!")
            self.media_display.play_video("ocean_wait (1).mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def door_choice(self, choice):
        if choice == "Red":
            self.update_story("Fire behind the door! You burn. GAME OVER!")
            self.media_display.stop_current_media()
            self.root.after(0, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(3000, lambda: self.set_buttons(["Restart"], self.restart_game))
        elif choice == "Black":
            self.update_story("A black hole sucks you in. GAME OVER!")
            self.media_display.play_video("black hole.mp4", loop=False)
            self.root.after(2000, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))
        elif choice == "Blue":
            self.update_story("🎉 Congratulations! You found the treasure!")
            self.media_display.play_video("treasure.mp4", loop=False)
            self.root.after(5000, lambda: self.set_buttons(["Restart"], self.restart_game))
        else:
            self.update_story("Wrong door. GAME OVER!")
            self.media_display.stop_current_media()
            self.root.after(0, lambda: self.media_display.play_video("Game_over.mp4", loop=False))
            self.root.after(3000, lambda: self.set_buttons(["Restart"], self.restart_game))

    def restart_game(self, _=None):
        # Stop any currently playing media
        self.media_display.stop_current_media()
        # Explicitly destroy all existing widgets in the root window
        self.clear_all_widgets()
        # Re-initialize the game, which will now create fresh widgets
        self.__init__(self.root)

# Run the game
if __name__ == "__main__":
    root = tk.Tk()
    game = TreasureIslandGame(root)
    root.mainloop()