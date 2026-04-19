import pygame
import random


class Vehicle:
    def __init__(self, x, lane_center_y, speed, lane, is_emergency=False, direction="E"):
        self.direction = direction
        if self.direction in ("N", "S"):
            self.length = 20
            self.width = 40
        else:
            self.length = 40
            self.width = 20

        self.x = x
        self.y = lane_center_y if self.direction in ("N", "S") else lane_center_y - (self.width // 2)
        self.lane_center = x if self.direction in ("N", "S") else lane_center_y
        self.lane = lane
        self.is_emergency = is_emergency
        self.max_speed = float(speed)
        self.current_speed = float(speed)
        self.rain_mode = False
        self.night_mode = False
        self.acceleration = 0.08
        self.deceleration = 0.2
        self.min_gap = 22
        self.reaction_timer = 0.0
        self.base_reaction_delay = 0.28
        self.waiting_at_stop = False
        self.wait_time = 0.0
        if self.is_emergency:
            self.color = (245, 245, 245)
            self.highlight_color = (220, 40, 40)
            self.max_speed = max(self.max_speed, 5.5)
        else:
            self.color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            self.highlight_color = None

    def desired_speed_from_signal(self, signal_state, distance_to_stop_line):
        if self.is_emergency:
            return self.max_speed

        if distance_to_stop_line < 0:
            return self.max_speed

        if signal_state == "RED":
            if distance_to_stop_line < 120:
                return 0.0
            return self.max_speed

        if signal_state == "YELLOW":
            if distance_to_stop_line < 70:
                return 0.0
            return self.max_speed * 0.45

        return self.max_speed

    def apply_emergency_yield(self, desired_speed, emergency_active, emergency_lane, emergency_x):
        if self.is_emergency or not emergency_active:
            return desired_speed

        if self.lane != emergency_lane:
            return min(desired_speed, self.max_speed * 0.45)

        if self.x > emergency_x:
            distance_from_emergency = self.x - emergency_x
            if distance_from_emergency < 140:
                return min(desired_speed, self.max_speed * 0.2)
            return min(desired_speed, self.max_speed * 0.5)

        return min(desired_speed, self.max_speed * 0.45)

    def update_speed(self, desired_speed, lead_vehicle):
        safe_speed = desired_speed
        active_min_gap = self.min_gap
        accel = self.acceleration
        decel = self.deceleration

        if getattr(self, "rain_mode", False):
            safe_speed *= 0.76
            active_min_gap += 14
            accel *= 0.72
            decel *= 0.8

        if getattr(self, "night_mode", False):
            safe_speed *= 0.92
            active_min_gap += 10
            accel *= 0.9
            decel *= 0.92

        if lead_vehicle is not None:
            gap = self.gap_to_leader(lead_vehicle)

            if gap <= active_min_gap:
                safe_speed = 0.0
            elif gap <= (active_min_gap + 30):
                safe_speed = min(safe_speed, lead_vehicle.current_speed * 0.6)

        if self.current_speed < safe_speed:
            self.current_speed = min(safe_speed, self.current_speed + accel)
        else:
            self.current_speed = max(safe_speed, self.current_speed - decel)

    # Feature: simple reaction delay at stop lines before moving on green.
    def apply_reaction_delay(self, desired_speed, can_go, near_stop_line, delta_seconds):
        if self.is_emergency:
            return desired_speed

        reaction_delay = self.base_reaction_delay
        if self.rain_mode:
            reaction_delay += 0.14
        if self.night_mode:
            reaction_delay += 0.2

        if near_stop_line and self.current_speed < 0.2 and not can_go:
            self.waiting_at_stop = True

        if can_go and self.waiting_at_stop:
            self.reaction_timer += delta_seconds
            if self.reaction_timer < reaction_delay:
                return 0.0

            self.waiting_at_stop = False
            self.reaction_timer = 0.0

        if not can_go:
            self.reaction_timer = 0.0

        return desired_speed

    def gap_to_leader(self, lead_vehicle):
        if self.direction == "E":
            return lead_vehicle.x - (self.x + self.length)
        if self.direction == "W":
            return self.x - (lead_vehicle.x + lead_vehicle.length)
        if self.direction == "S":
            return lead_vehicle.y - (self.y + self.width)
        return self.y - (lead_vehicle.y + lead_vehicle.width)

    def move(self):
        if self.direction == "E":
            self.x += self.current_speed
            self.y = self.lane_center - (self.width // 2)
        elif self.direction == "W":
            self.x -= self.current_speed
            self.y = self.lane_center - (self.width // 2)
        elif self.direction == "S":
            self.y += self.current_speed
            self.x = self.lane_center - (self.length // 2)
        else:
            self.y -= self.current_speed
            self.x = self.lane_center - (self.length // 2)

    # Feature: lightweight weather hook used by main loop.
    def set_rain_mode(self, enabled):
        self.rain_mode = enabled

    # Feature: apply environmental driving conditions in one place.
    def set_environment(self, rain_mode, night_mode):
        self.rain_mode = rain_mode
        self.night_mode = night_mode

    # Feature: track approximate waiting time for dashboard.
    def update_wait_time(self, delta_seconds):
        if self.current_speed < 0.25:
            self.wait_time += delta_seconds

    def reset_wait_time(self):
        self.wait_time = 0.0

    def draw(self, screen, night_mode=False):
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.length, self.width), border_radius=3)
        if self.is_emergency:
            if self.direction in ("E", "W"):
                pygame.draw.rect(screen, self.highlight_color, (int(self.x) + 10, int(self.y) + 4, 18, 6), border_radius=2)
            else:
                pygame.draw.rect(screen, self.highlight_color, (int(self.x) + 4, int(self.y) + 10, 10, 18), border_radius=2)

        # Feature: simple night-mode headlight effect.
        if night_mode:
            if self.direction == "E":
                pygame.draw.rect(screen, (255, 255, 210), (int(self.x) + self.length, int(self.y) + 6, 8, 4), border_radius=2)
            elif self.direction == "W":
                pygame.draw.rect(screen, (255, 255, 210), (int(self.x) - 8, int(self.y) + 6, 8, 4), border_radius=2)
            elif self.direction == "S":
                pygame.draw.rect(screen, (255, 255, 210), (int(self.x) + 6, int(self.y) + self.width, 4, 8), border_radius=2)
            else:
                pygame.draw.rect(screen, (255, 255, 210), (int(self.x) + 6, int(self.y) - 8, 4, 8), border_radius=2)