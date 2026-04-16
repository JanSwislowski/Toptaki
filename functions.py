import os
import pygame
import numpy as np
ID_FILE = "ids.txt"
tokens={}
ids={}
def load_ids():
     with open(ID_FILE, "r") as f:
        for line in f:
            username, id = line.strip().split(":")
            ids[username] = int(id)
def save_ids():
    with open(ID_FILE, "w") as f:
        for username, id in ids.items():
            f.write(f"{username}:{id}\n")

def add_paths(id):
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}"
    os.makedirs(path, exist_ok=True)
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/images"
    os.makedirs(path, exist_ok=True)
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    open(path,"w").close()

def add_info(id,username,password):
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    with open(path, "w") as f:
        f.write(f"Username:{username}\n")
        f.write(f"Password:{password}\n")
def add_user(username, password):
    cur_id=len(ids)+1
    ids[username]=cur_id
    print(cur_id)
    add_paths(cur_id)
    add_info(cur_id,username,password)
def check_login(username, password):
    if username not in ids:
        return False
    id=ids[username]
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    with open(path, "r") as f:
        lines=f.readlines()
        stored_password=lines[1].strip().split(":")[1]
        return stored_password==password
def upload_image(token, filename):
    if token not in tokens:
        return False
    username=tokens[token]
    id=ids[username]
    save_path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/images/{filename}"
    return save_path

from assets import ComentSection
def generate_coment_section(comments: list[dict],width, height):
    c=ComentSection(width, height)
    for comment in comments:
        c.add_comment(user=comment["user"], text=comment["text"])
    return c


def fade_surfaces(surface1: pygame.Surface, surface2: pygame.Surface, ratio: float) -> pygame.Surface:
    ratio = max(0.0, min(1.0, ratio))

    arr1 = pygame.surfarray.array3d(surface1).astype(np.float32)
    arr2 = pygame.surfarray.array3d(surface2).astype(np.float32)

    blended = ((arr1 * (1.0 - ratio)) + (arr2 * ratio)).astype(np.uint8)

    return pygame.surfarray.make_surface(blended)