import arcade
import random
import math


# 화면 크기
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "씨부엉이를 이겨라!"

CHOICES = ["가위", "바위", "보"]

# 폭죽 색상 팔레트
FIREWORK_COLORS = [
    arcade.color.RED, arcade.color.YELLOW, arcade.color.BLUE,
    arcade.color.GREEN, arcade.color.ORANGE, arcade.color.PURPLE,
    arcade.color.PINK, arcade.color.WHITE, arcade.color.GOLD
]

# GUI 구성용 스프라이트 저장 배열
visual_sprites = arcade.SpriteList()


class Particle:
    """ 간단한 폭죽 파티클 """
    def __init__(self, x, y, angle_deg=None, speed_range=(2.0, 5.0)):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 6)
        self.color = random.choice(FIREWORK_COLORS)
        self.lifetime = random.uniform(1.0, 2.0)  # 초 단위
        self.age = 0.0

        # 각도/속도 설정
        if angle_deg is None:
            angle_deg = random.uniform(0, 360)
        speed = random.uniform(*speed_range)

        rad = math.radians(angle_deg)
        self.dx = speed * math.cos(rad)
        self.dy = speed * math.sin(rad)

    def update(self, delta_time):
        self.x += self.dx
        self.y += self.dy
        self.age += delta_time
        if self.radius > 0:
            self.radius -= 0.05  # 서서히 소멸

    def draw(self):
        if self.is_alive():
            arcade.draw_circle_filled(self.x, self.y, max(1, self.radius), self.color)

    def is_alive(self):
        return self.age < self.lifetime and self.radius > 0


class MenuView(arcade.View):
    """ 초기 화면 (메뉴) """
    def __init__(self):
        super().__init__()

        # 씨부엉 로고
        self.logo = arcade.Sprite("bin/logo.png", scale=0.15)
        self.logo.right = SCREEN_WIDTH
        self.logo.bottom = 0
        visual_sprites.append(self.logo)

        # 부엉이
        self.owl = arcade.Sprite("bin/default.png", scale=0.3)
        self.owl.center_x = SCREEN_WIDTH // 2
        self.owl.center_y = SCREEN_HEIGHT // 2
        visual_sprites.append(self.owl)

        self.title_text = arcade.Text(
            SCREEN_TITLE,
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
            arcade.color.BLACK, 40, anchor_x="center"
        )
        self.info_text = arcade.Text(
            "화면을 클릭하면 게임이 시작됩니다!",
            SCREEN_WIDTH // 2, 75,
            arcade.color.BLACK, 24, anchor_x="center"
        )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.ARCADE_YELLOW)

    def on_draw(self):
        self.clear()
        visual_sprites.draw()
        self.title_text.draw()
        self.info_text.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        self.window.show_view(GameView(self.owl))


class GameView(arcade.View):
    """ 실제 게임 화면 """
    def __init__(self, owl_instance):
        super().__init__()
        self.player_choice = None
        self.computer_choice = None
        self.game_over = False
        self.can_click = True
        self.particles = []
        self.lose_sound = arcade.load_sound("bin/lose.mp3")
        self.win_sound = arcade.load_sound("bin/win.mp3")

        # 부엉이는 시각적으로 변경되기 때문에 MenuView에서 부엉이를 참조해서 변경
        self.owl = owl_instance

        # 가위바위보 관련 텍스트
        self.title_text = arcade.Text(
            "가위바위보 게임",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
            arcade.color.BLACK, 32, anchor_x="center"
        )
        self.result_text = arcade.Text(
            "가위, 바위, 보 중 하나를 클릭하세요!",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150,
            arcade.color.BLACK, 20, anchor_x="center"
        )
        self.player_text = arcade.Text(
            "", 20, SCREEN_HEIGHT // 2,
            arcade.color.AVOCADO, 20, anchor_x="left"
        )
        self.computer_text = arcade.Text(
            "", SCREEN_WIDTH - 20, SCREEN_HEIGHT // 2,
            arcade.color.BROWN, 20, anchor_x="right"
        )

        # 버튼
        self.button_specs = [
            ("가위", SCREEN_WIDTH // 2 - 200, 100),
            ("바위", SCREEN_WIDTH // 2, 100),
            ("보", SCREEN_WIDTH // 2 + 200, 100),
        ]
        self.button_size = (120, 60)
        self.button_labels = {
            name: arcade.Text(name, x, y, arcade.color.BLACK, 20,
                              anchor_x="center", anchor_y="center")
            for name, x, y in self.button_specs
        }

        self._return_scheduled = False

    def on_show_view(self):
        arcade.set_background_color(arcade.color.GOLD)

    def on_draw(self):
        self.clear()
        self.title_text.draw()
        self.result_text.draw()
        visual_sprites.draw()

        # 버튼(항상 동일한 색상)
        for name, x, y in self.button_specs:
            w, h = self.button_size
            arcade.draw_lrbt_rectangle_filled(
                x - w // 2, x + w // 2, y - h // 2, y + h // 2,
                arcade.color.ARCADE_YELLOW
            )
            self.button_labels[name].draw()

        # 결과 텍스트
        self.player_text.draw()
        self.computer_text.draw()

        # 폭죽
        for p in self.particles:
            p.draw()

    def on_update(self, delta_time: float):
        for p in self.particles:
            p.update(delta_time)
        self.particles = [p for p in self.particles if p.is_alive()]

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over or not self.can_click:
            return
        for name, bx, by in self.button_specs:
            w, h = self.button_size
            if (bx - w // 2) < x < (bx + w // 2) and (by - h // 2) < y < (by + h // 2):
                self.play(name)
                break

    def play(self, choice):
        self.player_choice = choice
        self.computer_choice = random.choice(CHOICES)

        # 판정
        if self.player_choice == self.computer_choice:
            self.result_text.text = "무승부! 다시 선택하세요."
            self.player_text.text = f"플레이어 선택: {self.player_choice}"
            self.computer_text.text = f"부엉이의 선택: {self.computer_choice}"
            # 무승부 → 0.2초 클릭 딜레이
            self.can_click = False
            arcade.schedule(self.enable_click, 0.2)
            return

        player_wins = (
            (self.player_choice == "가위" and self.computer_choice == "보") or
            (self.player_choice == "바위" and self.computer_choice == "가위") or
            (self.player_choice == "보"   and self.computer_choice == "바위")
        )

        if player_wins:
            self.result_text.text = "플레이어 승리!"
            # 플레이어 승리 → 부엉이의 슬픈 표정 랜덤 선택 & 폭죽 발사
            self.owl.texture = arcade.load_texture(f"bin/lose{random.randint(1, 4)}.png")
            self.spawn_fireworks_corner("left_bottom_cross")
            self.spawn_fireworks_corner("right_bottom_cross")
            arcade.play_sound(self.win_sound, volume=1.5)
        else:
            self.result_text.text = "부엉이 승리!"
            # 컴퓨터 승리 → 부엉이의 기쁜 표정 랜덤 선택 & 폭죽 없음
            self.owl.texture = arcade.load_texture(f"bin/win{random.randint(1, 4)}.png")
            arcade.play_sound(self.lose_sound)

        self.player_text.text = f"플레이어 선택: {self.player_choice}"
        self.computer_text.text = f"부엉이의 선택: {self.computer_choice}"

        # 승부가 나면 즉시 클릭 차단
        self.game_over = True
        self.can_click = False

        # 3초 후 메뉴 복귀
        if not self._return_scheduled:
            arcade.schedule(self.back_to_menu, 3.0)
            self._return_scheduled = True

    def enable_click(self, dt):
        self.can_click = True
        arcade.unschedule(self.enable_click)

    def spawn_fireworks_corner(self, mode: str):
        """모드별 코너에서 교차 발사"""
        count = 70
        speed_range = (2.5, 5.5)

        if mode == "left_bottom_cross":
            x, y = 0, 0  # 좌하단
            for _ in range(count):
                angle = random.uniform(35, 55)
                self.particles.append(Particle(x, y, angle_deg=angle, speed_range=speed_range))

        elif mode == "right_bottom_cross":
            x, y = SCREEN_WIDTH, 0  # 우하단
            for _ in range(count):
                angle = random.uniform(125, 145)
                self.particles.append(Particle(x, y, angle_deg=angle, speed_range=speed_range))

    def back_to_menu(self, dt):
        arcade.unschedule(self.back_to_menu)
        self._return_scheduled = False
        self.owl.kill()
        self.window.show_view(MenuView())


window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
window.show_view(MenuView())
arcade.run()
