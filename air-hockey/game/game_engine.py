"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

Task 3 adds a 30-second match timer and match-ending result handling.
"""

import random
import pygame

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5

MATCH_DURATION = 30.0


class GameEngine:
    def __init__(self):
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15,
            y=HEIGHT / 2,
            radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS,
            max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS,
            max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.computer = Paddle(
            x=WIDTH * 0.85,
            y=HEIGHT / 2,
            radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS,
            max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS,
            max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.ai = ComputerAI()

        # Task 2: scores.
        self.player_score = 0
        self.computer_score = 0

        # Task 3: match timer/state.
        self.match_start_time = pygame.time.get_ticks()
        self.match_time_remaining = MATCH_DURATION
        self.match_over = False
        self.result = None

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)

        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        # Do not allow player movement after the match has ended.
        if self.match_over:
            return

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
        # Once the match has ended, the entire game state is frozen.
        if self.match_over:
            return

        self._update_timer()

        # The timer may have expired during _update_timer().
        if self.match_over:
            return

        self.ai.update(self.computer, self.puck)

        self.puck.move()
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        # Task 1 collision handling remains unchanged.
        handle_paddle_collision(self.puck, self.player)
        handle_paddle_collision(self.puck, self.computer)

        self._handle_goals()

    def _update_timer(self):
        """
        Update the remaining match time using real elapsed time.

        pygame.time.get_ticks() is used instead of frame counting so the
        match lasts 30 real seconds regardless of the frame rate.
        """
        current_time = pygame.time.get_ticks()

        elapsed_seconds = (
            current_time - self.match_start_time
        ) / 1000.0

        self.match_time_remaining = max(
            0.0,
            MATCH_DURATION - elapsed_seconds,
        )

        if self.match_time_remaining <= 0.0:
            self.match_time_remaining = 0.0
            self._end_match()

    def _end_match(self):
        """Stop the match and determine its final result."""
        if self.match_over:
            return

        self.match_over = True

        # Stop the puck so nothing continues moving visually after time expires.
        self.puck.vx = 0.0
        self.puck.vy = 0.0

        if self.player_score > self.computer_score:
            self.result = "Player Wins!"
        elif self.computer_score > self.player_score:
            self.result = "Computer Wins!"
        else:
            self.result = "Draw"

    def _handle_goals(self):
        """
        Detect goals and update the appropriate player's score.

        A goal is awarded only after the puck has completely passed through
        the goal opening.
        """

        # Left goal: Computer scores.
        if self.puck.x + self.puck.radius < 0:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                self.computer_score += 1
                self._reset_puck()
            else:
                self.puck.x = MARGIN + self.puck.radius
                self.puck.vx = -self.puck.vx

        # Right goal: Player scores.
        elif self.puck.x - self.puck.radius > WIDTH:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                self.player_score += 1
                self._reset_puck()
            else:
                self.puck.x = WIDTH - MARGIN - self.puck.radius
                self.puck.vx = -self.puck.vx

    def _reset_puck(self):
        """
        Reset the puck to the center.

        Task 4 will change this so the puck immediately launches again
        after a goal.
        """
        self.puck.x = WIDTH / 2
        self.puck.y = HEIGHT / 2
        self.puck.vx = 0
        self.puck.vy = 0

    def get_winner(self):
        """
        Return the current/final match result.

        Before the match ends, return None.
        """
        if not self.match_over:
            return None

        return self.result

    def is_match_over(self):
        """Return True once the 30-second match has ended."""
        return self.match_over

    def draw(self, surface, font):
        from game import renderer

        renderer.draw_table(surface)

        # Task 2: score display.
        renderer.draw_score(
            surface,
            font,
            self.player_score,
            self.computer_score,
        )

        # Task 3: countdown timer.
        renderer.draw_timer(
            surface,
            font,
            self.match_time_remaining,
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

        renderer.draw_puck(
            surface,
            self.puck,
        )

        # Task 3: final result.
        if self.match_over:
            renderer.draw_result(
                surface,
                font,
                self.result,
            )