from assets import Post,Leader_board
from app import *
import pygame
screen=pygame.display.set_mode((500, 700))
text=("This is a test post. It should be long enough"
      " to test the text wrapping functionality of"
      " the Post class. Let's see how it looks when"
      " rendered on the screen.")
images=[pygame.image.load("photo.jpg"),pygame.image.load("photo2.jpg"),pygame.image.load("photo2.jpg"),

        ]
c=[{"user":"User1","text":"This is a comment."},
   {"user":"User2","text":"This is another comment."},
   {"user":"User3","text":"This is yet another comment."},
   {"user":"User4","text":"This is a fourth comment."}]

post=Post(400, "Test Post",None,c,images=images,text=text,)
post2=Post(400, "Test Post 2",None,c,images=images,text=text,)
post3=Post(400, "Test Post 3",None,c,images=images,text=text,)

description=r"This is a test description\n for the leaklonsadgobder board. It should be long enough to test the text wrapping functionality of the Leader_board class. Let's see how it looks when rendered on the screen."
card_info={"img":"photo3.PNG","name":"User1","avatar":"photo2.jpg","title":"Nigga","date":"2024-06-01","cords":((10,0),(10,0)),"description":description*1}
card2_info=card_info.copy()

card2_info["name"]="User2"
card2_info["description"]=description*2
card2_info["img"]="photo.jpg"


pos=(0, 0)
pos_delta=(-pos[0], -pos[1])

w=500
h=700
bs=BattleScreen(w,h,400,500)
bs.load(card_info,card2_info)
pos=(screen.get_width()//2-w//2, screen.get_height()//2-h//2)
print(pos)
running=True
# lb_pos_delta=(0, 0)
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        bs.handle_event(event,)
    screen.fill((0, 0, 0))
    bs.update(pos_delta)

    fps = clock.get_fps()
    print(f"FPS: {fps:.2f}")

    screen.blit(bs.draw(), pos)

    clock.tick(60)  # target FPS
    pygame.display.flip()
