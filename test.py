from assets import Post
from app import ProfileScreen
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

ps=ProfileScreen(500, 700)
text=r"This is a test profile screen. It should display the user's information and their posts. asifdafi as asf afs fafas\n asdaffas\n dasdasdad asdfasf"
posts=[post, post, post]
ps.load(None,"NIGGer",text,posts,None)

pos=(0, 0)
pos_delta=(-pos[0], -pos[1])

running=True
# post_pos_delta=(0, 0)
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        ps.handle_event(event,)
    screen.fill((0, 0, 0))
    ps.update()

    screen.blit(ps.draw(), pos)

    pygame.display.flip()
