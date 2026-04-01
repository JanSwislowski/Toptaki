import os

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
