import requests

SERVER = "https://sunny-conor-premorse.ngrok-free.dev"
token=-1
def send_image(filepath):
    with open(filepath, "rb") as f:
        files = {"file": (filepath, f, "image/jpeg")}
        response = requests.post(f"{SERVER}/upload", files=files,data={"token": token})
    print(response.json())
def sign_in():
    login=input("Username: ")
    password=input("Password: ")
    # login="adad"
    # password="sadasnd"
    data={"username": login, "password": password}
    response = requests.post(f"{SERVER}/sign_in", json=data)
    print(response.json())


def log_in():
    login=input("Username: ")
    password=input("Password: ")
    # login="adadda"
    # password="sd"
    data={"username": login, "password": password}
    response = requests.post(f"{SERVER}/login", json=data)
    global token
    token=response.json().get("token")
    print(response.json())
# send_image("photo.jpg")
# sign_in()
# log_in()
while True:
    operation=input("Choose operation (1: sign in, 2: log in, 3: send image, 4: exit): ")
    if operation=="1":
        sign_in()
    elif operation=="2":
        log_in()
    elif operation=="3":
        if token==-1:
            print("You must log in first.")
        else:
            filepath="photo.jpg"
            send_image(filepath)
    elif operation=="4":
        break
    else:
        print("Invalid operation. Try again.")