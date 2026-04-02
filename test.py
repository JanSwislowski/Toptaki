from assets import Post, ComentSection
import pygame
screen=pygame.display.set_mode((500, 700))
text=("This is a test post. It should be long enough"
      " to test the text wrapping functionality of"
      " the Post class. Let's see how it looks when"
      " rendered on the screen.")

c=[{"user":"User1","text":"This is a comment."},
   {"user":"User2","text":"This is another comment."},
   {"user":"User3","text":"This is yet another comment."},
   {"user":"User4","text":"This is a fourth comment."}]

post=Post(400, "Test Post",None,c,images=[],text=text)
post_pos=(50, 100)
post_pos_delta=(-post_pos[0], -post_pos[1])
running=True
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        post.handle_events(event,post_pos_delta)
    screen.fill((0, 0, 0))
    post.update(post_pos_delta)
    screen.blit(post.draw(), post_pos)
    pygame.display.flip()
