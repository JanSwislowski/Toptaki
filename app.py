import pygame
from assets import TextBox, Button, Label,Icon,Post,Picker,CompCard
from functions import *
class LoginScreen:
    def __init__(self,width, height,next_page):
        self.login=True
        self.width = width
        self.height = height

        self.surface = pygame.surface.Surface((self.width, self.height))
        self.color=(200, 200, 200)

        text_box_width = 200
        text_box_height=40

        self.username_box = TextBox(100, 100, text_box_width, text_box_height,placeholder="Username")
        self.password_box = TextBox(100, 160, text_box_width, text_box_height,placeholder="Password")

        button_width = 200
        button_height = 40

        self.login_button = Button(100, 400, button_width, button_height, "Login",callback=next_page)
        self.register_button = Button(100, 400, button_width, button_height, "Register",callback=next_page)

        self.active=False

    def set_login(self):
        self.login=True
    def set_register(self):
        self.login=False
    def update(self):
        if not self.active:
            return

        self.username_box.update()
        self.password_box.update()

        if self.login: self.login_button.update()
        else: self.register_button.update()
    def draw(self):
        self.surface.fill(self.color)

        self.username_box.draw(self.surface)
        self.password_box.draw(self.surface)

        if self.login:  self.login_button.draw(self.surface)
        else:  self.register_button.draw(self.surface)

        return self.surface
    def reset(self):
        self.username_box.clear()
        self.password_box.clear()
    def activate(self):
        self.reset()
        self.active=True

    def handle_event(self,event):
        if not self.active:
            return
        self.username_box.handle_event(event)
        self.password_box.handle_event(event)
        if self.login: self.login_button.handle_event(event)
        else: self.register_button.handle_event(event)
class StartScreen:
    def __init__(self,width, height,login_function,register_function):
        self.width = width
        self.height = height

        self.surface = pygame.surface.Surface((self.width, self.height))
        self.color=(200, 200, 200)

        button_width = 200
        button_height = 50

        self.login_button = Button(100, 250, button_width, button_height, "Login",callback=login_function)
        self.register_button = Button(100, 320, button_width, button_height, "Register",callback=register_function)

        self.title=Label(100, 50, "Toptaki", font_size=60)

        self.active=False
    def update(self):
        if not self.active:
            return

        self.login_button.update()
        self.register_button.update()
    def draw(self):
        self.surface.fill(self.color)

        self.login_button.draw(self.surface)
        self.register_button.draw(self.surface)

        self.title.draw(self.surface)

        return self.surface
    def activate(self):
        self.active=True

    def handle_event(self,event):
        if not self.active:
            return
        self.login_button.handle_event(event)
        self.register_button.handle_event(event)
class FeedScreen:
    def __init__(self,width,height):
        self.color=(10, 10, 10)
        self.w=width
        self.h=height
        self.surface=pygame.surface.Surface((self.w,self.h))
        text_w=300
        text_h=30
        x,y=50,10
        self.textbox=TextBox(x,y,text_w,text_h,placeholder="Search",font_size=20)

        self.posts=[]
        self.start_y=80
        self.padding=20

        self.last_mouse_y=None
        self.scroll=0

        self.post_h=0

        self.active=False

    def add_post(self, post):
        self.posts.append(post)
        self.post_h=self.posts_height()
    def posts_height(self):
        h=0
        for i in self.posts:
            h+=i.height+self.padding
        return h-self.padding
    def activate(self):
        self.active=True
    def _update_scroll(self):

        for i in self.posts:
            if i.scrolling:
                return

        mc=pygame.mouse.get_pressed()[0]
        mouse_y=pygame.mouse.get_pos()[1]
        Wspeed=1
        if mc and self.last_mouse_y==None:
            self.last_mouse_y=mouse_y
        elif mc:
            self.scroll+=(mouse_y-self.last_mouse_y)*Wspeed
            self.scroll=max(min(self.scroll,0),self.h-self.start_y-self.post_h)
            self.last_mouse_y=mouse_y
        else:
            self.last_mouse_y=None

    def update(self):
        self.textbox.update()
        if not self.posts:
            return
        self._update_scroll()
        x=self.w/2-self.posts[0].width/2
        y=self.start_y+self.scroll
        for i in self.posts:
            i.update(mouse_delta=(-x,-y))
            y+=i.height+self.padding

    def handle_event(self,event):
        self.textbox.handle_event(event)
        if not self.posts:
            return
        x=self.w/2-self.posts[0].width/2
        y=self.start_y+self.scroll
        for i in self.posts:
            i.handle_events(event,mouse_delta=(-x,-y))
            y+=i.height+self.padding
    def reset(self):
        #the great purge
        pass
    def _posts_draw(self):
        if not self.posts:
            return self.surface
        x=self.w/2-self.posts[0].width/2
        y=self.start_y+self.scroll
        for i in self.posts:
            self.surface.blit(i.draw(),(x, y))
            y+=i.height+self.padding
    def draw(self):
        self.surface.fill(self.color)

        self._posts_draw()
        pygame.draw.rect(self.surface,self.color,(0, 0, self.w, self.start_y))

        self.textbox.draw(self.surface)

        return self.surface
class Profile_edit_screen:
    def __init__(self,width, height):
        self.color=(10, 10, 10)
        self.width = width
        self.height = height
        self.surface = pygame.surface.Surface((self.width, self.height))
        font_size=30
        self.picker=Picker(width/2, 0, width, 40,font_size,["General","Avatar"],color=(20,20,20))
        self.name_box=TextBox(30, 100, 200, 40,placeholder="Name")
        self.description_box=TextBox(30, 300, 300, 100,placeholder="Description")
    def update(self):
        self.picker.update()
        if self.picker.get_chosen()=="General":
            self.name_box.update()
            self.description_box.update()
    def draw(self):
        self.surface.fill(self.color)
        self.picker.draw(self.surface)
        if self.picker.get_chosen()=="General":
            self.name_box.draw(self.surface)
            self.description_box.draw(self.surface)
        return self.surface
    def handle_event(self,event):
        pass
    def activate(self):
        pass
class ProfileScreen:
    def __init__(self,width, height):
        self.color=(10, 10, 10)
        self.width = width
        self.height = height
        self.surface = pygame.surface.Surface((self.width, self.height))
        self.padding=30
        self.posts=[]
    def activate(self):
        pass
    def get_posts_height(self):
        h=0
        for i in self.posts:
            h+=self.padding+i.height
        return h-self.padding
    def load(self,avatar,username,description,posts: list[Post],own_profile=False,):
        avatar_r=50
        text_color=(255, 255, 255)
        self.avatar=Icon(self.padding+avatar_r,self.padding+avatar_r,avatar_r,avatar,shadow=False)
        self.username=Label(self.avatar._cx+avatar_r+self.padding,self.padding,username,font_size=30,color_text=text_color)
        print(description)

        self.description=Label(self.padding,self.avatar._cy+avatar_r+self.padding,description,font_size=20,max_width=self.width-2*self.padding,color_text=text_color)
        self.posts=posts
        self.posts_starty=self.description._y+self.description.get_rect().h+self.padding

        self.scroll=0
        self.last_mouse_pos=None
        self.block_scroll=False

        self.posts_height=self.get_posts_height()
        self.posts_render_h=self.height-self.posts_starty
        #ładujesz dane użytkownika
    def _update_posts(self):
        if not self.posts or pygame.mouse.get_pos()[1]<self.posts_starty:
            return
        y=self.posts_starty-self.scroll
        starty=self.posts_starty
        x=self.width/2-self.posts[0].width/2
        for i in self.posts:
            if y+i.height<starty:
                y+=i.height+self.padding
                continue
            i.update(mouse_delta=(-x,-y))
            y+=i.height+self.padding
            if y>self.height:
                break
    def _posts_handle_event(self,event):
        if not self.posts:
            return
        y=self.posts_starty-self.scroll
        starty=self.posts_starty
        x=self.width/2-self.posts[0].width/2
        for i in self.posts:
            if y+i.height<starty:
                y+=i.height+self.padding
                continue
            i.handle_events(event,(-x,-y))
            y+=i.height+self.padding
            if y>self.height:
                break
    def _render_posts(self):
        if not self.posts:
            return
        y=self.posts_starty-self.scroll
        starty=self.posts_starty
        x=self.width/2-self.posts[0].width/2
        for i in self.posts:
            if y+i.height<starty:
                y+=i.height+self.padding
                continue
            self.surface.blit(i.draw(),(x, y))
            y+=i.height+self.padding
            if y>self.height:
                break

    def hovered_post(self):
        return pygame.mouse.get_pos()[1]>self.posts_starty
    def update_scroll(self):
        if self.block_scroll:
            return
        mouse_pos=pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and self.last_mouse_pos:
            self.scroll-=mouse_pos[1]-self.last_mouse_pos[1]
            self.scroll=min(max(self.scroll,0),self.posts_height-self.posts_render_h)
            self.last_mouse_pos=mouse_pos
        elif pygame.mouse.get_pressed()[0] and self.hovered_post():
            self.last_mouse_pos=mouse_pos
        else:
            self.last_mouse_pos=None
    def check_scroll_block(self):
        self.block_scroll=False
        for i in self.posts:
            if i.scrolling:
                self.block_scroll=True
                return

    def update(self):
        self._update_posts()
        self.check_scroll_block()
        self.update_scroll()

    def handle_event(self,event):
        self._posts_handle_event(event)
    def reset(self):
        self.posts=[]
        self.avatar=None
        self.username=None

    def draw(self):
        self.surface.fill(self.color)

        self._render_posts()
        pygame.draw.rect(self.surface,self.color,(0, 0, self.width, self.posts_starty))
        self.avatar.draw(self.surface)
        self.username.draw(self.surface)
        self.description.draw(self.surface)

        return self.surface
class PageSwitcher:
    def __init__(self,x,y,width,height,icons : list[pygame.surface.Surface],functions):
        self.rect=pygame.Rect(x,y,width,height)
        self.icons=icons
        self.functions=functions
        self.color=(100,100,100)
        self.active_color=(70,70,70)
        self.active=1
        self.l=len(self.icons)
        self.w=self.rect.w/self.l
        self.clicked=False

    def draw(self,surface):
        pygame.draw.rect(surface,self.color,self.rect)
        active_rect=pygame.Rect(self.rect.x+self.w*self.active,self.rect.y,self.w,self.rect.h)
        pygame.draw.rect(surface,self.active_color,active_rect)
        for j,i in enumerate(self.icons):
            iw,ih=i.get_width(),i.get_height()
            x=self.rect.x+self.w*j+self.w/2-iw/2
            y=self.rect.centery-ih/2
            surface.blit(i,(x,y))
    def update(self):
        if pygame.mouse.get_pressed()[0]:
            x,y=pygame.mouse.get_pos()
            if self.rect.collidepoint(x,y):
                self.clicked=True
        elif self.clicked:
            self.clicked=False
            x=pygame.mouse.get_pos()[0]
            self.active=int(x//self.w)
            self.functions[self.active]()

class BattleScreen:
    def __init__(self,width, height,img_width,img_height):
        self.width = width
        self.height=height
        self.img_w=img_width
        self.img_h=img_height
        self.surface = pygame.surface.Surface((self.width, self.height))
        self.color=(10, 10, 10)
        button_w=75
        button_h=75
        padding=0
        sz=(button_w-padding,button_h-padding)
        heart_img=scale_surface_proportionally(pygame.image.load("images/heart.png"),sz[0],sz[1]).convert_alpha()
        button_diff=75
        padding_y=40
        self.like_button=Button(self.width//2-button_w//2-button_diff,self.height-button_h-padding_y,button_w,button_h,
                                "",image=heart_img,border_radius=button_w//2,shadow=False,color_bg=(200, 50, 50),
                                color_hover=(255, 80, 80),color_press=(150, 30, 30),color_ripple=(255, 255, 255),callback=lambda: print("Liked!"),
                                )
        switch_img=scale_surface_proportionally(pygame.image.load("images/switch.png"),sz[0],sz[1])
        self.switch_button=Button(self.width//2-button_w//2+button_diff,self.height-button_h-padding_y,button_w,button_h,
                                "",image=switch_img,border_radius=button_w//2,shadow=False,color_bg=(50, 50, 200),
                                color_hover=(80, 80, 255),color_press=(30, 30, 150),color_ripple=(255, 255, 255),callback=lambda: self.switch_cards(),
                                )
        self.transition_duration=800
        self.transition_start_time=None
        self.transiting=False
    def start_transition(self):
        if self.transition_start_time is not None:
            return
        self.current_card^=1
        self.transition_start_time=pygame.time.get_ticks()
        self.transition_surface_1=self.cards[self.current_card^1].draw().convert_alpha()
        self.transition_surface_2=self.cards[self.current_card].draw().convert_alpha()
    def end_transition(self):
        self.transition_start_time=None
        del self.transition_surface_1
        del self.transition_surface_2
    def switch_cards(self):
        self.start_transition()
    def load(self,p1_info,p2_info):

        img1=scale_surface_proportionally(pygame.image.load(p1_info["img"]),self.img_w,self.img_h).convert_alpha()
        img2=scale_surface_proportionally(pygame.image.load(p2_info["img"]),self.img_w,self.img_h).convert_alpha()
        self.cards=[
            CompCard(self.img_w,self.img_h,img1,
                            pygame.image.load(p1_info["avatar"]),p1_info["name"],
                            p1_info["title"],p1_info["date"],p1_info["cords"],p1_info["description"]),

            CompCard(self.img_w,self.img_h,img2,
                            pygame.image.load(p2_info["avatar"]),p2_info["name"],
                            p2_info["title"],p2_info["date"],p2_info["cords"],p2_info["description"])]

        self.img_pos=(self.width//2-self.img_w//2, 50)
        self.current_card=0
    def handle_event(self,event):
        self.like_button.handle_event(event)
        self.switch_button.handle_event(event)
        if self.transition_start_time is not None:
            return
    def update(self,mouse_delta=(0,0)):
        self.like_button.update()
        self.switch_button.update()
        if self.transition_start_time is not None:
            t=pygame.time.get_ticks()-self.transition_start_time
            if t>=self.transition_duration:
                self.end_transition()
            return

        self.cards[self.current_card].update((mouse_delta[0]-self.img_pos[0], mouse_delta[1]-self.img_pos[1]))
    def draw(self):
        self.surface.fill(self.color)
        if self.transition_start_time is None: self.surface.blit(self.cards[self.current_card].draw(),self.img_pos)
        else:
            self.surface.blit(self.transition_surface_1,self.img_pos)
            t=pygame.time.get_ticks()-self.transition_start_time
            self.surface.blit(melt_transition(self.transition_surface_1,self.transition_surface_2,self.transition_duration,t),self.img_pos)

        self.like_button.draw(self.surface)
        self.switch_button.draw(self.surface)
        return self.surface

class App:
    def __init__(self):
        pygame.init()
        self.width = 400
        self.height = 600
        self.screen=pygame.display.set_mode((self.width, self.height))
        psh=70
        self.pages={
                "start": StartScreen(self.width, self.height,lambda: self.switch_page("login"),lambda: self.switch_page("register")),
                "login": LoginScreen(self.width, self.height,lambda: self.switch_page("feed")),
                "feed": FeedScreen(self.width,self.height-psh),
                "profile": ProfileScreen(self.width,self.height-psh),
        }

        icons=[pygame.transform.smoothscale(pygame.image.load("images/profile.png"),(psh-10,psh-10)),
               pygame.transform.smoothscale(pygame.image.load("images/home.png"),(psh-10,psh-10)),
               pygame.transform.smoothscale(pygame.image.load("images/battle.png"),(psh-10,psh-10)),
               pygame.transform.smoothscale(pygame.image.load("images/add.png"),(psh-10,psh-10)),]
        functions=[lambda: self.switch_page("profile"),lambda: self.switch_page("feed"),lambda: self.switch_page("battle"),lambda: print("add")]
        self.page_switcher=PageSwitcher(0,self.height-psh,self.width,psh,icons,functions)
        self.next_page=None

        self.start_fade=None
        self.fade_duration=500
        self.fade_out=False
        self.prev_surface=None
        self.next_surface=None
    def get_surfaces_to_fade(self,prev_page,next_page,reverse=False):
        surface1=pygame.surface.Surface((self.width, self.height))
        surface2=pygame.surface.Surface((self.width, self.height))
        surface1.blit(self.pages[prev_page].draw(),(0,0))
        surface2.fill(self.pages[next_page].color)
        if prev_page in ("feed" or "profile" or "battle"):
            self.page_switcher.draw(surface1)
        if next_page in ("feed" or "profile" or "battle"):
            self.page_switcher.draw(surface2)
        if reverse:
            self.prev_surface,self.next_surface=surface2, surface1
            return
        self.prev_surface, self.next_surface= surface1, surface2
    def switch_page(self,page_name):
        if page_name not in self.pages:
            return

        if page_name=="login":
            self.pages[page_name].set_login()
        if page_name=="register":
            page_name="login"
            self.pages[page_name].set_register()
        if page_name=="profile":
            self.pages[page_name].load()

        self.start_fade=pygame.time.get_ticks()
        self.get_surfaces_to_fade(self.current_page,page_name)

        self.next_page=page_name
    def update_fade(self):
        t = pygame.time.get_ticks() - self.start_fade
        if (not self.fade_out) and t > self.fade_duration // 2:
            print("Fading out...")
            self.get_surfaces_to_fade(self.next_page,self.next_page,reverse=True)
            self.fade_out=True
        if pygame.time.get_ticks() - self.start_fade >= self.fade_duration:
            self.start_fade = None
            self.current_page = self.next_page
            self.prev_surface = None
            self.next_surface = None
            self.pages[self.current_page].activate()
            self.fade_out = False
    def update(self):
        if self.start_fade is not None:
            self.update_fade()
            return
        self.pages[self.current_page].update()


    def draw(self,surface):
        if self.start_fade is not None:
            if not self.fade_out: ratio=(pygame.time.get_ticks()-self.start_fade)*2/(self.fade_duration)
            else: ratio=(pygame.time.get_ticks()-self.start_fade)*2/(self.fade_duration)-1
            surface.blit(fade_surfaces(self.prev_surface,self.next_surface,ratio),(0,0))
            return
        surface.blit(self.pages[self.current_page].draw(),(0,0))

    def run(self):
        clock=pygame.time.Clock()
        running = True
        self.current_page="start"
        self.pages[self.current_page].activate()
        while running:
            keys=pygame.key.get_pressed()
            self.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.pages[self.current_page].handle_event(event)

            if keys[pygame.K_ESCAPE]:
                running=False

            self.draw(self.screen)
            if self.current_page in ("feed" or "profile" or "battle"):
                self.page_switcher.update()
                self.page_switcher.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
if __name__ == "__main__":
    app = App()
    app.run()