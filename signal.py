import time
import pygame
class TrafficSignal:
    def __init__(self, x, y, green_time=6, yellow_time=4, red_time=6, adaptive_enabled=True):
        self.x = x
        self.y = y
        self.green_time = green_time
        self.yellow_time = yellow_time
        self.red_time = red_time
        self.adaptive_enabled = adaptive_enabled

        self.state = "GREEN"
        self.active_group = "NS"
        self.current_green_time = self.green_time
        self.emergency_override = False
        self.emergency_group = None
        self.pedestrian_override = False

        # Debug values for real-time HUD display.
        self.last_congestion_ns = 0
        self.last_congestion_ew = 0
        self.last_avg_wait_ns = 0.0
        self.last_avg_wait_ew = 0.0
        self.last_score_ns = 0.0
        self.last_score_ew = 0.0

        self.last_switch = time.time()

    @staticmethod
    def group_for_direction(direction):
        return "NS" if direction in ("N", "S") else "EW"

    @staticmethod
    def traffic_score(congestion, avg_wait):
        return (0.6 * congestion) + (0.4 * avg_wait)

    def _duration_for_state(self):
        if self.state == "GREEN":
            return self.current_green_time
        if self.state == "YELLOW":
            return self.yellow_time
        return self.red_time

    def current_state_label(self):
        if self.pedestrian_override:
            return "PED_RED"
        if self.emergency_override:
            return f"{self.emergency_group}_PRIORITY"
        return f"{self.active_group}_{self.state}"

    def short_state_label(self):
        if self.pedestrian_override:
            return "PED"
        if self.emergency_override:
            return f"EMG-{self.emergency_group}"
        return f"{self.active_group}-{self.state[0]}"

    def get_remaining_time(self):
        if self.emergency_override or self.pedestrian_override:
            return None

        elapsed = time.time() - self.last_switch
        remaining = self._duration_for_state() - elapsed
        return max(0.0, remaining)

    def activate_emergency_override(self, group):
        if self.pedestrian_override:
            return
        self.emergency_override = True
        self.emergency_group = group
        self.active_group = group
        self.state = "GREEN"
        self.last_switch = time.time()

    def clear_emergency_override(self):
        self.emergency_override = False
        self.emergency_group = None
        self.state = "YELLOW"
        self.last_switch = time.time()

    def is_emergency_active(self):
        return self.emergency_override

    # Feature: pedestrian crossing override API.
    def activate_pedestrian_override(self):
        self.pedestrian_override = True
        self.state = "RED"
        self.last_switch = time.time()

    def clear_pedestrian_override(self):
        self.pedestrian_override = False
        self.state = "GREEN"
        self.last_switch = time.time()

    def is_pedestrian_active(self):
        return self.pedestrian_override

    def light_for_direction(self, direction):
        group = self.group_for_direction(direction)

        if self.pedestrian_override:
            return "RED"

        if self.emergency_override:
            return "GREEN" if group == self.emergency_group else "RED"

        if group != self.active_group:
            return "RED"

        return self.state

    def can_move(self, direction):
        return self.light_for_direction(direction) == "GREEN"

    def update(self, congestion_ns, congestion_ew, avg_wait_ns=0.0, avg_wait_ew=0.0):
        # Keep latest decision inputs visible for HUD/debug rendering.
        self.last_congestion_ns = congestion_ns
        self.last_congestion_ew = congestion_ew
        self.last_avg_wait_ns = avg_wait_ns
        self.last_avg_wait_ew = avg_wait_ew
        self.last_score_ns = self.traffic_score(congestion_ns, avg_wait_ns)
        self.last_score_ew = self.traffic_score(congestion_ew, avg_wait_ew)

        if self.pedestrian_override:
            self.state = "RED"
            return

        if self.emergency_override:
            self.state = "GREEN"
            return

        current = time.time()
        elapsed = current - self.last_switch

        score_ns = self.last_score_ns
        score_ew = self.last_score_ew
        active_score = score_ns if self.active_group == "NS" else score_ew

        # Fixed mode keeps base timings; adaptive mode extends green by traffic pressure.
        if not self.adaptive_enabled:
            self.current_green_time = self.green_time
        else:
            # Feature: simple smart optimization using congestion + average wait score.
            if active_score >= 5.0:
                self.current_green_time = self.green_time + 4
            elif active_score >= 3.0:
                self.current_green_time = self.green_time + 2
            else:
                self.current_green_time = self.green_time

            # Fairness cap so green does not grow too much.
            self.current_green_time = min(self.current_green_time, self.green_time + 5)

        if self.state == "GREEN" and elapsed > self.current_green_time:
            self.state = "YELLOW"
            self.last_switch = current
            return

        if self.state == "YELLOW" and elapsed > self.yellow_time:
            if self.adaptive_enabled:
                if score_ns > score_ew:
                    self.active_group = "NS"
                elif score_ew > score_ns:
                    self.active_group = "EW"
                else:
                    # Tie-break keeps fairness by alternating when both scores are equal.
                    self.active_group = "EW" if self.active_group == "NS" else "NS"
            else:
                self.active_group = "EW" if self.active_group == "NS" else "NS"

            self.state = "GREEN"
            self.last_switch = current

    def draw(self, screen, night_mode=False):
        # Draw two distinct heads: one for NS and one for EW control groups.
        groups = [
            ("NS", self.x - 58, self.y),
            ("EW", self.x + 58, self.y),
        ]

        for group, head_x, head_y in groups:
            housing_w = 52
            housing_h = 130
            housing_x = head_x - (housing_w // 2)
            housing_y = head_y - (housing_h // 2)

            pygame.draw.rect(screen, (35, 35, 35), (housing_x, housing_y, housing_w, housing_h), border_radius=8)
            pygame.draw.rect(screen, (95, 95, 95), (housing_x, housing_y, housing_w, housing_h), width=2, border_radius=8)
            pygame.draw.rect(screen, (70, 70, 70), (head_x - 5, housing_y + housing_h, 10, 52), border_radius=3)

            red_pos = (head_x, housing_y + 24)
            yellow_pos = (head_x, housing_y + 64)
            green_pos = (head_x, housing_y + 104)

            is_green_group = self.can_move("N" if group == "NS" else "E")
            is_yellow_group = (not self.emergency_override and self.state == "YELLOW" and self.active_group == group)

            colors = {
                "RED": (255, 35, 35) if not is_green_group and not is_yellow_group else (70, 25, 25),
                "YELLOW": (255, 220, 20) if is_yellow_group else (80, 75, 30),
                "GREEN": (35, 255, 90) if is_green_group else (25, 70, 25),
            }

            for name, pos in [("RED", red_pos), ("YELLOW", yellow_pos), ("GREEN", green_pos)]:
                pygame.draw.circle(screen, (20, 20, 20), pos, 13)
                pygame.draw.circle(screen, colors[name], pos, 10)

                is_active = (name == "GREEN" and is_green_group) or (name == "YELLOW" and is_yellow_group) or (
                    name == "RED" and not is_green_group and not is_yellow_group
                )
                if is_active:
                    if night_mode:
                        pygame.draw.circle(screen, colors[name], pos, 18, width=2)
                    pygame.draw.circle(screen, colors[name], pos, 14, width=2)

            label_font = pygame.font.SysFont("arial", 13)
            label = label_font.render(group, True, (220, 220, 220))
            screen.blit(label, (head_x - 10, housing_y - 18))

        indicator_x = self.x
        indicator_y = self.y - 80
        if self.emergency_override:
            pygame.draw.circle(screen, (40, 170, 255), (indicator_x, indicator_y), 6)
        elif self.pedestrian_override:
            pygame.draw.circle(screen, (255, 170, 40), (indicator_x, indicator_y), 6)

    def draw_countdown(self, screen, font):
        if self.pedestrian_override:
            timer_text = "PED"
        elif self.emergency_override:
            timer_text = "PRIORITY"
        else:
            timer_text = str(int(self.get_remaining_time() + 0.99))

        box_x = self.x + 90
        box_y = self.y - 46
        box_w = 110
        box_h = 42

        pygame.draw.rect(screen, (18, 18, 18), (box_x, box_y, box_w, box_h), border_radius=6)
        pygame.draw.rect(screen, (180, 180, 180), (box_x, box_y, box_w, box_h), width=1, border_radius=6)

        label = font.render(self.short_state_label(), True, (230, 230, 230))
        value = font.render(timer_text, True, (255, 230, 120))
        screen.blit(label, (box_x + 8, box_y + 4))
        screen.blit(value, (box_x + 8, box_y + 20))