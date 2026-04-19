import pygame
import random
import sys
import csv
from vehicle import Vehicle
from signal import TrafficSignal

pygame.init()
SIM_WIDTH = 800
HUD_WIDTH = 300
SIM_HEIGHT = 600
TITLE_BAR_HEIGHT = 50
SIM_TOP = TITLE_BAR_HEIGHT
SCREEN_WIDTH = SIM_WIDTH + HUD_WIDTH
SCREEN_HEIGHT = SIM_HEIGHT + TITLE_BAR_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Real Time Smart Traffic Simulation")

clock = pygame.time.Clock()

# 4-way geometry
ROAD_H_TOP = 220
ROAD_H_BOTTOM = 380
ROAD_V_LEFT = 320
ROAD_V_RIGHT = 480
INT_LEFT = 340
INT_RIGHT = 460
INT_TOP = 240
INT_BOTTOM = 360

# Two lanes per direction (simple multi-lane setup)
LANE_CENTERS = {
    "E": [320, 350],
    "W": [250, 280],
    "S": [350, 380],
    "N": [420, 450],
}

STOP_LINES = {
    "E": INT_LEFT - 12,
    "W": INT_RIGHT + 12,
    "S": INT_TOP - 12,
    "N": INT_BOTTOM + 12,
}

EMERGENCY_TRIGGER_DISTANCE = 420
EMERGENCY_SIREN_ZONE = 340
PEDESTRIAN_DURATION = 6.0


def parse_duration_argument(default_seconds=60):
    for arg in sys.argv[1:]:
        if arg.startswith("--duration="):
            value = arg.split("=", 1)[1].strip()
            try:
                parsed = float(value)
                if parsed > 0:
                    return parsed
            except ValueError:
                pass
    return default_seconds


def stop_thresholds(rain_mode, night_mode):
    yellow_stop = 85
    red_stop = 130

    if rain_mode:
        yellow_stop += 20
        red_stop += 35

    if night_mode:
        yellow_stop += 12
        red_stop += 20

    return yellow_stop, red_stop


def draw_road(surface, night_mode):
    # Feature: day/night road appearance.
    bg_color = (14, 14, 24) if night_mode else (24, 24, 24)
    road_color = (38, 38, 45) if night_mode else (52, 52, 52)
    mark_color = (210, 210, 230) if night_mode else (214, 214, 214)
    surface.fill(bg_color)

    # Horizontal and vertical roads
    pygame.draw.rect(surface, road_color, (0, ROAD_H_TOP, SIM_WIDTH, ROAD_H_BOTTOM - ROAD_H_TOP))
    pygame.draw.rect(surface, road_color, (ROAD_V_LEFT, 0, ROAD_V_RIGHT - ROAD_V_LEFT, SIM_HEIGHT))

    # Central intersection area
    pygame.draw.rect(surface, (68, 68, 68), (INT_LEFT, INT_TOP, INT_RIGHT - INT_LEFT, INT_BOTTOM - INT_TOP))

    # Dashed lane markings 
    for y in [285, 315]:
        dash_x = 0
        while dash_x < SIM_WIDTH:
            pygame.draw.line(surface, mark_color, (dash_x, y), (dash_x + 24, y), 2)
            dash_x += 44

    for x in [365, 435]:
        dash_y = 0
        while dash_y < SIM_HEIGHT:
            pygame.draw.line(surface, mark_color, (x, dash_y), (x, dash_y + 24), 2)
            dash_y += 44

    # Stop lines at all four approaches
    pygame.draw.line(surface, (240, 240, 240), (STOP_LINES["E"], ROAD_H_TOP), (STOP_LINES["E"], ROAD_H_BOTTOM), 3)
    pygame.draw.line(surface, (240, 240, 240), (STOP_LINES["W"], ROAD_H_TOP), (STOP_LINES["W"], ROAD_H_BOTTOM), 3)
    pygame.draw.line(surface, (240, 240, 240), (ROAD_V_LEFT, STOP_LINES["S"]), (ROAD_V_RIGHT, STOP_LINES["S"]), 3)
    pygame.draw.line(surface, (240, 240, 240), (ROAD_V_LEFT, STOP_LINES["N"]), (ROAD_V_RIGHT, STOP_LINES["N"]), 3)


def draw_rain(surface):
    # Feature: lightweight rain effect.
    for _ in range(70):
        x = random.randint(0, SIM_WIDTH)
        y = random.randint(0, SIM_HEIGHT)
        pygame.draw.line(surface, (165, 180, 210), (x, y), (x - 5, y + 10), 1)


def group_for_direction(direction):
    return TrafficSignal.group_for_direction(direction)


def progress_along_direction(car):
    if car.direction == "E":
        return car.x
    if car.direction == "W":
        return -car.x
    if car.direction == "S":
        return car.y
    return -car.y


def distance_to_stop_line(car):
    if car.direction == "E":
        return STOP_LINES["E"] - (car.x + car.length)
    if car.direction == "W":
        return car.x - STOP_LINES["W"]
    if car.direction == "S":
        return STOP_LINES["S"] - (car.y + car.width)
    return car.y - STOP_LINES["N"]


def has_crossed_intersection(car):
    if car.direction == "E":
        return car.x > INT_RIGHT + 70
    if car.direction == "W":
        return (car.x + car.length) < INT_LEFT - 70
    if car.direction == "S":
        return car.y > INT_BOTTOM + 70
    return (car.y + car.width) < INT_TOP - 70


def is_out_of_bounds(car):
    if car.direction == "E":
        return car.x > SIM_WIDTH + 80
    if car.direction == "W":
        return (car.x + car.length) < -80
    if car.direction == "S":
        return car.y > SIM_HEIGHT + 80
    return (car.y + car.width) < -80


def spawn_vehicle(direction=None, lane_index=None, is_emergency=False):
    if direction is None:
        direction = random.choice(["E", "W", "S", "N"])

    lane_count = len(LANE_CENTERS[direction])
    if lane_index is None:
        lane_index = random.randint(0, lane_count - 1)

    lane_center = LANE_CENTERS[direction][lane_index]
    speed = 7 if is_emergency else random.randint(3, 6)

    if direction == "E":
        x = random.randint(-600, -80)
        y = lane_center
    elif direction == "W":
        x = random.randint(SIM_WIDTH + 80, SIM_WIDTH + 600)
        y = lane_center
    elif direction == "S":
        x = lane_center
        y = random.randint(-600, -80)
    else:
        x = lane_center
        y = random.randint(SIM_HEIGHT + 80, SIM_HEIGHT + 600)

    return Vehicle(x, y, speed, lane=(direction, lane_index), is_emergency=is_emergency, direction=direction)


def respawn_vehicle(car):
    direction = car.direction
    lane_index = random.randint(0, len(LANE_CENTERS[direction]) - 1)
    fresh = spawn_vehicle(direction=direction, lane_index=lane_index, is_emergency=car.is_emergency)
    car.__dict__.update(fresh.__dict__)


def adjacent_lane_indices(direction, lane_index):
    candidates = []
    if lane_index - 1 >= 0:
        candidates.append(lane_index - 1)
    if lane_index + 1 < len(LANE_CENTERS[direction]):
        candidates.append(lane_index + 1)
    return candidates


def lane_change_safe(car, target_lane_index, all_vehicles, rain_mode):
    direction = car.direction
    target_lane = (direction, target_lane_index)

    back_buffer = 70 if rain_mode else 55
    front_buffer = 90 if rain_mode else 75

    car_progress = progress_along_direction(car)

    for other in all_vehicles:
        if other is car or other.lane != target_lane:
            continue

        other_progress = progress_along_direction(other)
        delta = other_progress - car_progress
        if -back_buffer < delta < front_buffer:
            return False

    return True


def try_simple_lane_change(car, all_vehicles, rain_mode):
    # Feature: simple lane change / overtake logic.
    direction, lane_index = car.lane
    candidates = adjacent_lane_indices(direction, lane_index)

    best_lane = None
    best_front_space = -1
    car_progress = progress_along_direction(car)

    for target_lane_index in candidates:
        if not lane_change_safe(car, target_lane_index, all_vehicles, rain_mode):
            continue

        front_space = 9999
        target_lane = (direction, target_lane_index)
        for other in all_vehicles:
            if other is car or other.lane != target_lane:
                continue
            delta = progress_along_direction(other) - car_progress
            if delta > 0:
                front_space = min(front_space, delta)

        if front_space > best_front_space:
            best_front_space = front_space
            best_lane = target_lane_index

    if best_lane is not None:
        car.lane = (direction, best_lane)
        car.lane_center = LANE_CENTERS[direction][best_lane]
        return True

    return False


def try_emergency_lane_clear(car, emergency_vehicle, all_vehicles, rain_mode):
    # Emergency-specific clearing: vehicles in ambulance lane try to move out.
    if car.direction != emergency_vehicle.direction:
        return False

    emg_direction, emg_lane_index = emergency_vehicle.lane
    car_direction, car_lane_index = car.lane

    if car_direction != emg_direction:
        return False

    if car_lane_index != emg_lane_index:
        return True

    for target_lane_index in adjacent_lane_indices(car_direction, car_lane_index):
        if target_lane_index == emg_lane_index:
            continue

        if lane_change_safe(car, target_lane_index, all_vehicles, rain_mode):
            car.lane = (car_direction, target_lane_index)
            car.lane_center = LANE_CENTERS[car_direction][target_lane_index]
            return True

    return False


def find_lead_vehicle(car, all_vehicles):
    lead = None
    closest_gap = None
    car_progress = progress_along_direction(car)

    for other in all_vehicles:
        if other is car or other.lane != car.lane:
            continue

        gap = progress_along_direction(other) - car_progress
        if gap > 0 and (closest_gap is None or gap < closest_gap):
            closest_gap = gap
            lead = other

    return lead


def run_metrics_simulation(duration_seconds, adaptive_enabled, seed=12345):
    random.seed(seed)

    vehicles = []
    for _ in range(16):
        vehicles.append(spawn_vehicle())

    emergency_vehicle = spawn_vehicle(is_emergency=True)
    vehicles.append(emergency_vehicle)

    signal = TrafficSignal(400, 140, green_time=7, yellow_time=3, red_time=6, adaptive_enabled=adaptive_enabled)

    traffic_history = []
    avg_wait_history = []
    vehicles_passed = 0

    rain_mode = False
    night_mode = False
    pedestrian_active = False
    frame_count = max(1, int(duration_seconds * 60))
    delta_seconds = 1.0 / 60.0

    for _ in range(frame_count):
        congestion_ns = 0
        congestion_ew = 0
        wait_ns_values = []
        wait_ew_values = []

        for car in vehicles:
            dist = distance_to_stop_line(car)
            group = group_for_direction(car.direction)

            if 0 < dist < 150:
                if group == "NS":
                    congestion_ns += 1
                else:
                    congestion_ew += 1

            if not car.is_emergency:
                if group == "NS":
                    wait_ns_values.append(car.wait_time)
                else:
                    wait_ew_values.append(car.wait_time)

        total_congestion = congestion_ns + congestion_ew
        traffic_history.append(total_congestion)

        avg_wait_ns = sum(wait_ns_values) / max(1, len(wait_ns_values))
        avg_wait_ew = sum(wait_ew_values) / max(1, len(wait_ew_values))
        avg_wait_history.append((avg_wait_ns + avg_wait_ew) / 2.0)

        emergency_distance = distance_to_stop_line(emergency_vehicle)
        emergency_group = group_for_direction(emergency_vehicle.direction)
        emergency_approaching = -20 <= emergency_distance <= (EMERGENCY_TRIGGER_DISTANCE + 80)

        if (not pedestrian_active) and emergency_approaching:
            signal.activate_emergency_override(emergency_group)

        if signal.is_emergency_active() and has_crossed_intersection(emergency_vehicle):
            signal.clear_emergency_override()

        signal.update(congestion_ns, congestion_ew, avg_wait_ns, avg_wait_ew)

        yielding_ids = set()
        for car in vehicles:
            if car.is_emergency:
                continue

            if emergency_approaching and car.direction == emergency_vehicle.direction:
                ahead_gap = progress_along_direction(car) - progress_along_direction(emergency_vehicle)
                if 0 < ahead_gap < EMERGENCY_SIREN_ZONE:
                    changed = try_emergency_lane_clear(car, emergency_vehicle, vehicles, rain_mode)
                    if not changed:
                        yielding_ids.add(id(car))
                    continue

            lead = find_lead_vehicle(car, vehicles)
            if lead is None:
                continue

            gap = progress_along_direction(lead) - progress_along_direction(car) - car.length
            overtake_gap = 55 if rain_mode else 45
            if gap < overtake_gap and lead.current_speed < (car.max_speed * 0.8):
                try_simple_lane_change(car, vehicles, rain_mode)

        if emergency_approaching:
            emg_lead = find_lead_vehicle(emergency_vehicle, vehicles)
            if emg_lead is not None:
                emg_gap = progress_along_direction(emg_lead) - progress_along_direction(emergency_vehicle) - emergency_vehicle.length
                if emg_gap < 70:
                    try_simple_lane_change(emergency_vehicle, vehicles, rain_mode)

        all_lanes = []
        for direction in ["E", "W", "S", "N"]:
            for lane_index in range(len(LANE_CENTERS[direction])):
                all_lanes.append((direction, lane_index))

        for lane_key in all_lanes:
            lane_cars = [car for car in vehicles if car.lane == lane_key]
            lane_cars.sort(key=progress_along_direction, reverse=True)
            lead_vehicle = None

            for car in lane_cars:
                car.set_environment(rain_mode, night_mode)

                distance = distance_to_stop_line(car)
                light_state = signal.light_for_direction(car.direction)
                can_go = signal.can_move(car.direction) or car.is_emergency
                yellow_stop_dist, red_stop_dist = stop_thresholds(rain_mode, night_mode)

                if distance < 0:
                    desired_speed = car.max_speed
                else:
                    if car.is_emergency:
                        desired_speed = car.max_speed
                    else:
                        if light_state == "GREEN":
                            desired_speed = car.max_speed
                        elif light_state == "YELLOW":
                            desired_speed = 0.0 if distance < yellow_stop_dist else car.max_speed * 0.42
                        else:
                            desired_speed = 0.0 if distance < red_stop_dist else car.max_speed * 0.5

                if pedestrian_active:
                    desired_speed = 0.0

                near_stop_line = 0 <= distance < 140
                desired_speed = car.apply_reaction_delay(desired_speed, can_go, near_stop_line, delta_seconds)

                if signal.is_emergency_active() and (not car.is_emergency):
                    if group_for_direction(car.direction) != group_for_direction(emergency_vehicle.direction):
                        if distance < 220:
                            desired_speed = 0.0
                        else:
                            desired_speed = min(desired_speed, car.max_speed * 0.35)
                    elif car.direction == emergency_vehicle.direction:
                        ahead_gap = progress_along_direction(car) - progress_along_direction(emergency_vehicle)
                        if 0 < ahead_gap < EMERGENCY_SIREN_ZONE:
                            desired_speed = min(desired_speed, car.max_speed * 0.22)

                if id(car) in yielding_ids:
                    desired_speed = min(desired_speed, car.max_speed * 0.25)

                car.update_speed(desired_speed, lead_vehicle)
                car.move()
                car.update_wait_time(delta_seconds)

                if is_out_of_bounds(car):
                    if car.is_emergency:
                        fresh = spawn_vehicle(is_emergency=True)
                        car.__dict__.update(fresh.__dict__)
                        emergency_vehicle = car
                    else:
                        respawn_vehicle(car)
                        vehicles_passed += 1

                    car.reset_wait_time()

                lead_vehicle = car

    avg_wait = sum(avg_wait_history) / max(1, len(avg_wait_history))
    avg_congestion = sum(traffic_history) / max(1, len(traffic_history))

    return {
        "avg_wait": avg_wait,
        "throughput": vehicles_passed,
        "avg_congestion": avg_congestion,
    }


def percent_improvement(baseline, candidate, lower_is_better):
    if baseline == 0:
        return 0.0
    if lower_is_better:
        return ((baseline - candidate) / baseline) * 100.0
    return ((candidate - baseline) / baseline) * 100.0


def print_comparison(duration_seconds):
    print(f"Running comparison for {duration_seconds:.1f}s per mode...")

    fixed = run_metrics_simulation(duration_seconds, adaptive_enabled=False, seed=12345)
    adaptive = run_metrics_simulation(duration_seconds, adaptive_enabled=True, seed=12345)

    wait_gain = percent_improvement(fixed["avg_wait"], adaptive["avg_wait"], lower_is_better=True)
    throughput_gain = percent_improvement(fixed["throughput"], adaptive["throughput"], lower_is_better=False)
    congestion_gain = percent_improvement(fixed["avg_congestion"], adaptive["avg_congestion"], lower_is_better=True)

    print("\n=== Signal Timing Comparison ===")
    print("Mode 1 (Fixed Timing):")
    print(f"  Avg waiting time: {fixed['avg_wait']:.2f} s")
    print(f"  Throughput:       {fixed['throughput']} vehicles")
    print(f"  Avg congestion:   {fixed['avg_congestion']:.2f} vehicles near junction")

    print("Mode 2 (Adaptive Timing):")
    print(f"  Avg waiting time: {adaptive['avg_wait']:.2f} s")
    print(f"  Throughput:       {adaptive['throughput']} vehicles")
    print(f"  Avg congestion:   {adaptive['avg_congestion']:.2f} vehicles near junction")

    print("\n=== Percentage Improvement (Adaptive vs Fixed) ===")
    print(f"  Waiting time improvement: {wait_gain:.2f}%")
    print(f"  Throughput improvement:   {throughput_gain:.2f}%")
    print(f"  Congestion improvement:   {congestion_gain:.2f}%")


# Optional CLI comparison mode: python main.py --compare --duration=60
if "--compare" in sys.argv:
    print_comparison(parse_duration_argument(default_seconds=60))
    pygame.quit()
    raise SystemExit


# Create regular vehicles in all four directions
vehicles = []
for _ in range(16):
    vehicles.append(spawn_vehicle())

# One emergency vehicle (respawns from random directions)
emergency_vehicle = spawn_vehicle(is_emergency=True)
vehicles.append(emergency_vehicle)

signal = TrafficSignal(400, 140, green_time=7, yellow_time=3, red_time=6, adaptive_enabled=True)
hud_font = pygame.font.SysFont("arial", 18)

traffic_history = []
signal_state_history = []
avg_wait_history = []
passed_per_frame_history = []
vehicles_passed = 0
rain_mode = False
night_mode = False
pedestrian_active = False
pedestrian_timer = 0.0
debug_panel_visible = True
paused = False
pause_started_at = None

running = True
while running:
    delta_seconds = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Pause/resume toggle
                if not paused:
                    paused = True
                    pause_started_at = pygame.time.get_ticks() / 1000.0
                else:
                    paused = False
                    if pause_started_at is not None:
                        paused_duration = (pygame.time.get_ticks() / 1000.0) - pause_started_at
                        # Shift signal timing forward so countdown stays frozen while paused.
                        signal.last_switch += paused_duration
                    pause_started_at = None

            # Feature: pedestrian crossing trigger.
            if event.key == pygame.K_p and not pedestrian_active:
                pedestrian_active = True
                pedestrian_timer = PEDESTRIAN_DURATION
                signal.activate_pedestrian_override()

            # Feature: rain mode toggle.
            elif event.key == pygame.K_r:
                rain_mode = not rain_mode

            # Feature: day/night mode toggle.
            elif event.key == pygame.K_n:
                night_mode = not night_mode

            # Feature: debug panel visibility toggle.
            elif event.key == pygame.K_d:
                debug_panel_visible = not debug_panel_visible

    if (not paused) and pedestrian_active:
        pedestrian_timer -= delta_seconds
        if pedestrian_timer <= 0:
            pedestrian_active = False
            pedestrian_timer = 0.0
            signal.clear_pedestrian_override()

    congestion_ns = 0
    congestion_ew = 0
    wait_ns_values = []
    wait_ew_values = []

    for car in vehicles:
        dist = distance_to_stop_line(car)
        group = group_for_direction(car.direction)

        if 0 < dist < 150:
            if group == "NS":
                congestion_ns += 1
            else:
                congestion_ew += 1

        if not car.is_emergency:
            if group == "NS":
                wait_ns_values.append(car.wait_time)
            else:
                wait_ew_values.append(car.wait_time)

    total_congestion = congestion_ns + congestion_ew
    traffic_history.append(total_congestion)

    avg_wait_ns = sum(wait_ns_values) / max(1, len(wait_ns_values))
    avg_wait_ew = sum(wait_ew_values) / max(1, len(wait_ew_values))
    avg_wait_history.append((avg_wait_ns + avg_wait_ew) / 2.0)

    emergency_distance = distance_to_stop_line(emergency_vehicle)
    emergency_group = group_for_direction(emergency_vehicle.direction)

    emergency_approaching = -20 <= emergency_distance <= (EMERGENCY_TRIGGER_DISTANCE + 80)

    if (not paused) and (not pedestrian_active) and emergency_approaching:
        signal.activate_emergency_override(emergency_group)

    if (not paused) and signal.is_emergency_active() and has_crossed_intersection(emergency_vehicle):
        signal.clear_emergency_override()

    if not paused:
        signal.update(congestion_ns, congestion_ew, avg_wait_ns, avg_wait_ew)
    signal_state_history.append(signal.current_state_label())

    # Feature: emergency lane clearing + simple overtaking before movement.
    yielding_ids = set()
    if not paused:
        for car in vehicles:
            if car.is_emergency:
                continue

            # Cars ahead in emergency approach should give way early.
            if emergency_approaching and car.direction == emergency_vehicle.direction:
                ahead_gap = progress_along_direction(car) - progress_along_direction(emergency_vehicle)
                if 0 < ahead_gap < EMERGENCY_SIREN_ZONE:
                    changed = try_emergency_lane_clear(car, emergency_vehicle, vehicles, rain_mode)
                    if not changed:
                        yielding_ids.add(id(car))
                    continue

            lead = find_lead_vehicle(car, vehicles)
            if lead is None:
                continue

            gap = progress_along_direction(lead) - progress_along_direction(car) - car.length
            overtake_gap = 55 if rain_mode else 45
            if gap < overtake_gap and lead.current_speed < (car.max_speed * 0.8):
                try_simple_lane_change(car, vehicles, rain_mode)

        # If ambulance is blocked by a stopped/slow lead vehicle, let it change lane if safe.
        if emergency_approaching:
            emg_lead = find_lead_vehicle(emergency_vehicle, vehicles)
            if emg_lead is not None:
                emg_gap = progress_along_direction(emg_lead) - progress_along_direction(emergency_vehicle) - emergency_vehicle.length
                if emg_gap < 70:
                    try_simple_lane_change(emergency_vehicle, vehicles, rain_mode)

    # Render simulation onto an off-screen surface, then place it below the title bar.
    simulation_surface = pygame.Surface((SIM_WIDTH, SIM_HEIGHT))
    draw_road(simulation_surface, night_mode)
    if rain_mode:
        draw_rain(simulation_surface)

    # Direction labels (render-only UI)
    dir_font = pygame.font.SysFont("arial", 16)
    label_color = (210, 210, 210)
    north_surface = dir_font.render("North", True, label_color)
    south_surface = dir_font.render("South", True, label_color)
    west_surface = dir_font.render("West", True, label_color)
    east_surface = dir_font.render("East", True, label_color)

    simulation_surface.blit(north_surface, ((SIM_WIDTH - north_surface.get_width()) // 2, 54))
    simulation_surface.blit(south_surface, ((SIM_WIDTH - south_surface.get_width()) // 2, SIM_HEIGHT - 34))
    simulation_surface.blit(west_surface, (28, 190))
    simulation_surface.blit(east_surface, (SIM_WIDTH - east_surface.get_width() - 28, 190))

    passed_this_frame = 0

    # Process vehicles lane-by-lane, leader first to preserve collision avoidance.
    all_lanes = []
    for direction in ["E", "W", "S", "N"]:
        for lane_index in range(len(LANE_CENTERS[direction])):
            all_lanes.append((direction, lane_index))

    for lane_key in all_lanes:
        lane_cars = [car for car in vehicles if car.lane == lane_key]
        lane_cars.sort(key=progress_along_direction, reverse=True)
        lead_vehicle = None

        for car in lane_cars:
            car.set_environment(rain_mode, night_mode)

            if not paused:
                distance = distance_to_stop_line(car)
                light_state = signal.light_for_direction(car.direction)
                can_go = signal.can_move(car.direction) or car.is_emergency
                yellow_stop_dist, red_stop_dist = stop_thresholds(rain_mode, night_mode)

                if distance < 0:
                    desired_speed = car.max_speed
                else:
                    if car.is_emergency:
                        desired_speed = car.max_speed
                    else:
                        if light_state == "GREEN":
                            desired_speed = car.max_speed
                        elif light_state == "YELLOW":
                            # Yellow: near stop line must stop, far vehicles continue slowly.
                            desired_speed = 0.0 if distance < yellow_stop_dist else car.max_speed * 0.42
                        else:
                            # Red: vehicles queue safely before stop line.
                            desired_speed = 0.0 if distance < red_stop_dist else car.max_speed * 0.5

                # Feature: pedestrian crossing hard stop for all traffic.
                if pedestrian_active:
                    desired_speed = 0.0

                near_stop_line = 0 <= distance < 140
                desired_speed = car.apply_reaction_delay(desired_speed, can_go, near_stop_line, delta_seconds)

                # Non-emergency vehicles give way to emergency traffic.
                if signal.is_emergency_active() and (not car.is_emergency):
                    if group_for_direction(car.direction) != group_for_direction(emergency_vehicle.direction):
                        if distance < 220:
                            desired_speed = 0.0
                        else:
                            desired_speed = min(desired_speed, car.max_speed * 0.35)
                    elif car.direction == emergency_vehicle.direction:
                        ahead_gap = progress_along_direction(car) - progress_along_direction(emergency_vehicle)
                        if 0 < ahead_gap < EMERGENCY_SIREN_ZONE:
                            desired_speed = min(desired_speed, car.max_speed * 0.22)

                if id(car) in yielding_ids:
                    desired_speed = min(desired_speed, car.max_speed * 0.25)

                car.update_speed(desired_speed, lead_vehicle)
                car.move()
                car.update_wait_time(delta_seconds)

                if is_out_of_bounds(car):
                    if car.is_emergency:
                        # Keep emergency feature alive from different approaches.
                        fresh = spawn_vehicle(is_emergency=True)
                        car.__dict__.update(fresh.__dict__)
                        emergency_vehicle = car
                    else:
                        respawn_vehicle(car)
                        vehicles_passed += 1
                        passed_this_frame += 1

                    car.reset_wait_time()
            lead_vehicle = car

            car.draw(simulation_surface, night_mode=night_mode)

    signal.draw(simulation_surface, night_mode=night_mode)
    signal.draw_countdown(simulation_surface, hud_font)

    # Frame background and title bar.
    screen.fill((12, 15, 20))
    title_bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, TITLE_BAR_HEIGHT)
    pygame.draw.rect(screen, (20, 24, 30), title_bar_rect)
    pygame.draw.line(screen, (55, 65, 78), (0, TITLE_BAR_HEIGHT - 1), (SCREEN_WIDTH, TITLE_BAR_HEIGHT - 1), 1)

    title_font = pygame.font.SysFont("segoe ui", 26, bold=True)
    title_surface = title_font.render("SMART TRAFFIC CONTROL SYSTEM", True, (228, 236, 245))
    title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
    title_y = (TITLE_BAR_HEIGHT - title_surface.get_height()) // 2
    screen.blit(title_surface, (title_x, title_y))

    # Place simulation below the title bar and draw split divider.
    screen.blit(simulation_surface, (0, SIM_TOP))
    pygame.draw.line(screen, (80, 90, 105), (SIM_WIDTH, SIM_TOP), (SIM_WIDTH, SCREEN_HEIGHT), 2)

    # Feature: real-time dashboard (clean grouped layout)
    emergency_text = "ON" if signal.is_emergency_active() else "OFF"
    weather_text = "RAIN" if rain_mode else "CLEAR"
    day_text = "NIGHT" if night_mode else "DAY"

    hud_x = SIM_WIDTH + 12
    hud_y = SIM_TOP + 12
    hud_w = HUD_WIDTH - 24
    hud_h = 336

    # Semi-transparent overlay panel.
    hud_surface = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
    hud_surface.fill((16, 20, 26, 190))
    pygame.draw.rect(hud_surface, (160, 170, 182, 220), (0, 0, hud_w, hud_h), width=1, border_radius=10)

    font_family = "segoe ui"
    hud_title_font = pygame.font.SysFont(font_family, 16, bold=True)
    hud_font_small = pygame.font.SysFont(font_family, 15)
    hud_font_value = pygame.font.SysFont(font_family, 15, bold=True)

    if signal.is_pedestrian_active():
        signal_state_text = "RED"
    elif signal.is_emergency_active():
        signal_state_text = "GREEN"
    else:
        signal_state_text = signal.state

    state_colors = {
        "GREEN": (80, 220, 120),
        "YELLOW": (245, 210, 70),
        "RED": (240, 95, 95),
    }
    signal_state_color = state_colors.get(signal_state_text, (225, 225, 225))

    label_x = 14
    value_x = 170
    row_h = 21
    y = 12

    def draw_section_title(text, current_y):
        title = hud_title_font.render(text, True, (205, 220, 235))
        hud_surface.blit(title, (label_x, current_y))
        return current_y + row_h

    def draw_row(label, value, current_y, value_color=(235, 235, 235)):
        label_surface = hud_font_small.render(label, True, (185, 195, 205))
        value_surface = hud_font_value.render(value, True, value_color)
        hud_surface.blit(label_surface, (label_x, current_y))
        hud_surface.blit(value_surface, (value_x, current_y))
        return current_y + row_h

    y = draw_section_title("SIGNAL", y)
    y = draw_row("State", signal_state_text, y, signal_state_color)
    y = draw_row("Active Group", signal.active_group, y)

    y += 2
    pygame.draw.line(hud_surface, (70, 80, 92, 220), (label_x, y), (hud_w - label_x, y), 1)
    y += 7

    y = draw_section_title("TRAFFIC", y)
    y = draw_row("Congestion NS/EW", f"{congestion_ns} / {congestion_ew}", y)
    y = draw_row("Avg Wait NS/EW", f"{avg_wait_ns:.1f}s / {avg_wait_ew:.1f}s", y)
    y = draw_row("Vehicles Passed", f"{vehicles_passed}", y)

    y += 2
    pygame.draw.line(hud_surface, (70, 80, 92, 220), (label_x, y), (hud_w - label_x, y), 1)
    y += 7

    y = draw_section_title("SYSTEM", y)
    y = draw_row("Emergency", emergency_text, y)
    y = draw_row("Weather", weather_text, y)
    y = draw_row("Mode", day_text, y)

    y += 2
    pygame.draw.line(hud_surface, (70, 80, 92, 220), (label_x, y), (hud_w - label_x, y), 1)
    y += 7

    controls_title = hud_title_font.render("CONTROLS", True, (205, 220, 235))
    controls_font = pygame.font.SysFont(font_family, 13)
    hud_surface.blit(controls_title, (label_x, y))
    y += row_h

    control_lines = [
        "[Space] Pause",
        "[P] Pedestrian",
        "[R] Rain",
        "[N] Day/Night",
        "[D] Debug",
    ]
    for line in control_lines:
        line_surface = controls_font.render(line, True, (185, 195, 205))
        hud_surface.blit(line_surface, (label_x, y))
        y += 18

    screen.blit(hud_surface, (hud_x, hud_y))

    dbg_x = hud_x
    dbg_y = hud_y + hud_h + 8
    dbg_w = hud_w
    dbg_h = 70
    if debug_panel_visible:
        # Debug panel: live signal decision inputs and scores (top-left).
        pygame.draw.rect(screen, (18, 18, 18), (dbg_x, dbg_y, dbg_w, dbg_h), border_radius=6)
        pygame.draw.rect(screen, (150, 150, 150), (dbg_x, dbg_y, dbg_w, dbg_h), width=1, border_radius=6)

        debug_line_1 = f"NS_score:{signal.last_score_ns:.2f}  EW_score:{signal.last_score_ew:.2f}"
        debug_line_2 = f"NS cong:{signal.last_congestion_ns} wait:{signal.last_avg_wait_ns:.2f}s"
        debug_line_3 = f"EW cong:{signal.last_congestion_ew} wait:{signal.last_avg_wait_ew:.2f}s"
        screen.blit(hud_font_small.render(debug_line_1, True, (210, 240, 255)), (dbg_x + 8, dbg_y + 6))
        screen.blit(hud_font_small.render(debug_line_2, True, (235, 235, 235)), (dbg_x + 8, dbg_y + 27))
        screen.blit(hud_font_small.render(debug_line_3, True, (235, 235, 235)), (dbg_x + 8, dbg_y + 48))

    if pedestrian_active:
        ped_msg = f"PEDESTRIAN CROSSING {pedestrian_timer:0.1f}s"
        ped_y = (dbg_y + dbg_h + 6) if debug_panel_visible else (hud_y + hud_h + 6)
        screen.blit(hud_font_small.render(ped_msg, True, (255, 220, 120)), (hud_x + 10, ped_y))

    if paused:
        pause_font = pygame.font.SysFont("arial", 36)
        pause_surface = pause_font.render("PAUSED", True, (255, 230, 120))
        pause_x = (SCREEN_WIDTH - pause_surface.get_width()) // 2
        screen.blit(pause_surface, (pause_x, SIM_TOP + 120))

    if not paused:
        passed_per_frame_history.append(passed_this_frame)
    pygame.display.flip()

pygame.quit()

# Analytics graph after simulation window closes
import matplotlib.pyplot as plt


def moving_average(data, window):
    if not data:
        return []
    if window <= 1:
        return list(data)

    output = []
    running_sum = 0.0
    for i, value in enumerate(data):
        running_sum += value
        if i >= window:
            running_sum -= data[i - window]
        current_window = min(i + 1, window)
        output.append(running_sum / current_window)
    return output


def state_spans(states):
    if not states:
        return []

    spans = []
    start = 0
    current_state = states[0]

    for i in range(1, len(states)):
        if states[i] != current_state:
            spans.append((start, i - 1, current_state))
            start = i
            current_state = states[i]

    spans.append((start, len(states) - 1, current_state))
    return spans


def export_metrics_to_csv(traffic_data, wait_data, throughput_data, signal_states, total_passed):
    # Align series lengths safely in case pause mode affects throughput samples.
    target_len = min(len(traffic_data), len(wait_data), len(signal_states))
    throughput_series = list(throughput_data[:target_len])
    if len(throughput_series) < target_len:
        throughput_series.extend([0] * (target_len - len(throughput_series)))

    throughput_per_second = [value * 60 for value in throughput_series]

    metrics_csv = "simulation_metrics.csv"
    with open(metrics_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time", "congestion", "avg_wait", "throughput", "signal_state"])
        for i in range(target_len):
            writer.writerow([
                round(i / 60.0, 2),
                traffic_data[i],
                round(wait_data[i], 4),
                throughput_per_second[i],
                signal_states[i],
            ])

    average_waiting_time = (sum(wait_data) / max(1, len(wait_data)))
    max_congestion = max(traffic_data) if traffic_data else 0

    summary_csv = "simulation_summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["metric", "value"])
        writer.writerow(["total_vehicles_passed", total_passed])
        writer.writerow(["average_waiting_time", round(average_waiting_time, 4)])
        writer.writerow(["max_congestion", max_congestion])

    print(f"Exported metrics to {metrics_csv}")
    print(f"Exported summary to {summary_csv}")


time_axis = list(range(len(traffic_history)))
sample_step = 5
sampled_x = time_axis[::sample_step]
sampled_congestion = traffic_history[::sample_step]

smooth_window = 120
congestion_smooth = moving_average(traffic_history, smooth_window)
wait_smooth = moving_average(avg_wait_history, smooth_window)

# Throughput: vehicles passed per second (smoothed).
throughput_per_second = [value * 60 for value in passed_per_frame_history]
throughput_smooth = moving_average(throughput_per_second, smooth_window)

export_metrics_to_csv(
    traffic_history,
    avg_wait_history,
    passed_per_frame_history,
    signal_state_history,
    vehicles_passed,
)

fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

# Panel 1: congestion raw + smooth
axes[0].plot(sampled_x, sampled_congestion, color="#4e79a7", linewidth=1.0, alpha=0.65, label="Raw (sampled)")
axes[0].plot(time_axis, congestion_smooth, color="#1f77b4", linewidth=2.0, label="Smoothed")
axes[0].set_ylabel("Near Junction")
axes[0].set_title("Traffic Metrics Over Time")
axes[0].legend(loc="upper right")

# Shade by signal phase for readability.
phase_colors = {
    "NS_GREEN": "#d7f5d1",
    "NS_YELLOW": "#fff5cc",
    "EW_GREEN": "#d1e7ff",
    "EW_YELLOW": "#fff5cc",
}
for start, end, phase in state_spans(signal_state_history):
    axes[0].axvspan(start, end, color=phase_colors.get(phase, "#eeeeee"), alpha=0.12)

# Panel 2: average waiting time
axes[1].plot(time_axis, wait_smooth, color="#f28e2b", linewidth=2.0)
axes[1].set_ylabel("Avg Wait (s)")

# Panel 3: throughput
axes[2].plot(time_axis, throughput_smooth, color="#59a14f", linewidth=2.0)
axes[2].set_ylabel("Vehicles/s")
axes[2].set_xlabel("Time (frames)")

for ax in axes:
    ax.grid(alpha=0.2)

plt.tight_layout()
plt.show()
