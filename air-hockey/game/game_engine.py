"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

Task 2 adds scoring and score display. Match timing/end-of-match behavior
is intentionally left for Task 3.
"""

import random

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5


class GameEngine:
    def __init__(self):
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS,
            max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS,
            max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.ai = ComputerAI()

        # Task 2: match scores.
        self.player_score = 0
        self.computer_score = 0

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)

        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        import pygame

        dx = dy = 0

        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED

        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED

        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED

        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED

        self.player.move_by(dx, dy)

    def update(self):
        self.ai.update(self.computer, self.puck)

        self.puck.move()
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        # Task 1 collision handling remains unchanged.
        handle_paddle_collision(self.puck, self.player)
        handle_paddle_collision(self.puck, self.computer)

        self._handle_goals()

    def _handle_goals(self):
        """
        Detect goals and update the appropriate player's score.

        A goal is only awarded once the puck has completely passed through
        the goal opening. Contact with the wall outside the opening causes
        a normal bounce instead.
        """

        # Left goal:
        # The puck must be completely beyond the left edge of the table.
        if self.puck.x + self.puck.radius < 0:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                # Player's opponent scored.
                self.computer_score += 1
                self._reset_puck()
            else:
                # Outside the goal opening: bounce from the wall.
                self.puck.x = MARGIN + self.puck.radius
                self.puck.vx = -self.puck.vx

        # Right goal:
        # The puck must be completely beyond the right edge of the table.
        elif self.puck.x - self.puck.radius > WIDTH:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                # Player scored.
                self.player_score += 1
                self._reset_puck()
            else:
                # Outside the goal opening: bounce from the wall.
                self.puck.x = WIDTH - MARGIN - self.puck.radius
                self.puck.vx = -self.puck.vx

    def _reset_puck(self):
        self.puck.x = WIDTH / 2
        self.puck.y = HEIGHT / 2
        self.puck.vx = 0
        self.puck.vy = 0

    def get_winner(self):
        """
        Return the current score result.

        Task 3 will use this when the 30-second match ends.
        """
        if self.player_score > self.computer_score:
            return "Player"

        if self.computer_score > self.player_score:
            return "Computer"

        return "Draw"

    def draw(self, surface, font):
        from game import renderer

        renderer.draw_table(surface)

        renderer.draw_score(
            surface,
            font,
            self.player_score,
            self.computer_score,
        )

        renderer.draw_paddle(
            surface,
            self.player,
            renderer.COLOR_PLAYER,
        )

        renderer.draw_paddle(
            surface,
            self.computer,
            renderer.COLOR_COMPUTER,
        )

        renderer.draw_puck(surface, self.puck)