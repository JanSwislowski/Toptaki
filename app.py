import pygame
from assets import TextBox, Button, Label
class LoginScreen:
    def __init__(self,width, height):
        self.login=False
        self.width = width
        self.height = height

        self.surface = pygame.surface.Surface((self.width, self.height))
        self.surface_color=(200, 200, 200)

        text_box_width = 200
        text_box_height=40

        self.username_box = TextBox(100, 100, text_box_width, text_box_height,placeholder="Username")
        self.password_box = TextBox(100, 160, text_box_width, text_box_height,placeholder="Password")

        button_width = 80
        button_height = 40

        self.login_button = Button(100, 220, button_width, button_height, "Login")
        self.register_button = Button(200, 220, button_width, button_height, "Register")

        self.fade_in=False
        self.fade_out=False
        self.fade_duration=400
        self.fade_start_time=0


        self.active=False

    def start_fade_out(self):
        if self.fade_out:
            return
        self.fade_out=True
        self.active=False
        self.fade_start_time=pygame.time.get_ticks()
    def end_fade_out(self):
        self.fade_out=False
        self.active=False
    def is_fade_out_complete(self):
        if not self.fade_out:
            return False
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        return elapsed >= self.fade_duration

    def start_fade_in(self):
        if self.fade_in:
            return
        self.fade_in=True
        self.fade_start_time=pygame.time.get_ticks()
    def end_fade_in(self):
        self.fade_in=False
        self.active=True
    def is_fade_in_complete(self):
        if not self.fade_in:
            return False
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        return elapsed >= self.fade_duration
    def fade_surface(self,reverse=False):
        rev=255 if reverse else 0
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        alpha = max(0, abs(rev-int(255 * (elapsed / self.fade_duration))))
        fade_surface = pygame.Surface((self.width, self.height))
        fade_surface.fill(self.surface_color)
        fade_surface.set_alpha(alpha)
        return fade_surface

    def set_login(self):
        self.login=True
    def set_register(self):
        self.login=False

    def draw(self):
        self.surface.fill(self.surface_color)

        if not (self.active or self.fade_out or self.fade_in):
            return self.surface

        self.username_box.update()
        self.password_box.update()

        if self.login: self.login_button.update()
        else: self.register_button.update()

        self.username_box.draw(self.surface)
        self.password_box.draw(self.surface)

        if self.login:  self.login_button.draw(self.surface)
        else:  self.register_button.draw(self.surface)

        if self.fade_out or self.fade_in:
            self.surface.blit(self.fade_surface(self.fade_in), (0, 0))

        if self.fade_out:
            if self.is_fade_out_complete():
                self.end_fade_out()
        if self.fade_in:
            if self.is_fade_in_complete():
                self.end_fade_in()

        return self.surface

    def reset(self):
        self.username_box.clear()
        self.password_box.clear()
        self.active=False
        self.fade_out=False
    def activate(self):
        self.reset()
        self.start_fade_in()

    def handle_event(self,event):
        if not self.active:
            return
        self.username_box.handle_event(event)
        self.password_box.handle_event(event)
        if self.login: self.login_button.handle_event(event)
        else: self.register_button.handle_event(event)
class StartScreen:
    def __init__(self,width, height,next_page_function):
        self.width = width
        self.height = height

        self.surface = pygame.surface.Surface((self.width, self.height))
        self.surface_color=(200, 200, 200)

        button_width = 200
        button_height = 50

        self.login_button = Button(100, 250, button_width, button_height, "Login",callback=next_page_function)
        self.register_button = Button(100, 320, button_width, button_height, "Register")

        self.title=Label(100, 50, "Toptaki", font_size=60)

        self.fade_in=False
        self.fade_out=False
        self.fade_duration=400
        self.fade_start_time=0

        self.active=False

    def start_fade_out(self):
        if self.fade_out:
            return
        self.fade_out=True
        self.active=False
        self.fade_start_time=pygame.time.get_ticks()
    def end_fade_out(self):
        self.fade_out=False
        self.active=False
    def is_fade_out_complete(self):
        if not self.fade_out:
            return False
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        return elapsed >= self.fade_duration

    def start_fade_in(self):
        if self.fade_in:
            return
        self.fade_in=True
        self.fade_start_time=pygame.time.get_ticks()
    def end_fade_in(self):
        self.fade_in=False
        self.active=True
    def is_fade_in_complete(self):
        if not self.fade_in:
            return False
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        return elapsed >= self.fade_duration
    def fade_surface(self,reverse=False):
        rev=255 if reverse else 0
        elapsed = pygame.time.get_ticks() - self.fade_start_time
        alpha = max(0, abs(rev-int(255 * (elapsed / self.fade_duration))))
        fade_surface = pygame.Surface((self.width, self.height))
        fade_surface.fill(self.surface_color)
        fade_surface.set_alpha(alpha)
        return fade_surface

    def draw(self):
        self.surface.fill(self.surface_color)

        if not (self.active or self.fade_out or self.fade_in):
            return self.surface

        self.login_button.update()
        self.register_button.update()

        self.login_button.draw(self.surface)
        self.register_button.draw(self.surface)

        self.title.draw(self.surface)

        if self.fade_out or self.fade_in:
            self.surface.blit(self.fade_surface(self.fade_in), (0, 0))

        if self.fade_out:
            if self.is_fade_out_complete():
                self.end_fade_out()
        if self.fade_in:
            if self.is_fade_in_complete():
                self.end_fade_in()
        return self.surface
    def reset(self):
        self.active=False
        self.fade_out=False
    def activate(self):
        self.reset()
        self.start_fade_in()

    def handle_event(self,event):
        if not self.active:
            return
        self.login_button.handle_event(event)
        self.register_button.handle_event(event)

class FeedScreen:
    def __init__(self):
        pass
    def add_post(self, post):
        pass
    def activate(self):
        pass
    def update(self):
        pass
    def handle_event(self,event):
        pass
    def reset(self):
        pass
    def draw(self):
        pass
class ProfileScreen:
    pass

class App:
    def __init__(self):
        pygame.init()
        self.width = 400
        self.height = 600
        self.screen=pygame.display.set_mode((self.width, self.height))
        self.pages={
                "start": StartScreen(self.width, self.height,lambda: self.switch_page("login")),
                "login": LoginScreen(self.width, self.height)
        }
        self.next_page=None
    def switch_page(self,page_name):
        # if page_name not in self.pages:
        #     return

        self.pages[self.current_page].start_fade_out()
        self.next_page=page_name
    def update(self):
        if self.next_page and not self.pages[self.current_page].fade_out:
            self.current_page=self.next_page
            self.pages[self.current_page].activate()
            self.next_page=None
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
            if keys[pygame.K_RETURN]:
                self.pages[self.current_page].start_fade_out()


            self.screen.blit(self.pages[self.current_page].draw(),(0,0))

            pygame.display.flip()
        pygame.quit()
if __name__ == "__main__":
    app = App()
    app.run()