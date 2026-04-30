from assets import Post
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

pe=Profile_edit_screen(500,700)
#fdxfd
pos=(0, 0)
pos_delta=(-pos[0], -pos[1])

running=True
# post_pos_delta=(0, 0)
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        pe.handle_event(event,)
    screen.fill((0, 0, 0))
    pe.update()

    screen.blit(pe.draw(), pos)

    pygame.display.flip()
