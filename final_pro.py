
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time

W, H = 1100, 760
LANES = (-4.2, 0.0, 4.2)
SEGMENT_LENGTH = 14.0
SEGMENT_COUNT = 17
PLAYER_Y = 0.0

# Game state
game_started = False
game_over = False
player_lane = 1
player_x = 0.0
player_z = 0.0
jump_velocity = 0.0
slide_timer = 0.0
lives = 3
coins_collected = 0
score = 0
distance_run = 0.0
base_speed = 18.0

super_run = False
super_run_timer = 0.0
super_run_cooldown = 0.0


shield_active = False
shield_charges = 0
character_index = 0
run_angle = 0.0
last_time = time.perf_counter()
hit_cooldown = 0.0
# message = "PRESS ENTER TO BEGIN YOUR ESCAPE"
message_timer = 999.0

next_fireball = 8.0
next_shield_distance = 260.0

next_collapse = 105.0
coin_spin = 0.0

blink_timer = 0.0



bridge = []
coins = []
obstacles = []
fireballs = []
shield_pickups = []
scenery = []

CHARACTERS = [
    ("Abir", (0.90, 0.08, 0.08), (0.50, 0.05, 0.05)),
    ("Zafra", (0.95, 0.95, 0.95), (0.65, 0.65, 0.65)),
    ("Karib", (0.20, 0.75, 1.00), (0.05, 0.45, 0.75)),
]


def set_message(text, seconds=2.2):
    global message, message_timer
    message, message_timer = text, seconds


def draw_text(x, y, text, color=(1, 1, 1), font=GLUT_BITMAP_HELVETICA_18):
    glDisable(GL_LIGHTING)
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)


def draw_control_arrow(x, y, direction, color=(.9, .92, .84)):
    """Draw a simple outlined arrow for the start-screen control legend."""
    directions = {
        "left": (-1, 0),
        "right": (1, 0),
        "up": (0, 1),
        "down": (0, -1),
    }
    dx, dy = directions[direction]
    half_length = 11
    wing = 6
    tip_x, tip_y = x + dx * half_length, y + dy * half_length
    tail_x, tail_y = x - dx * half_length, y - dy * half_length

    glDisable(GL_LIGHTING)
    glColor3f(*color)
    glLineWidth(3.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_LINES)
    glVertex2f(tail_x, tail_y)
    glVertex2f(tip_x, tip_y)
    glVertex2f(tip_x, tip_y)
    glVertex2f(tip_x - dx * wing - dy * wing, tip_y - dy * wing + dx * wing)
    glVertex2f(tip_x, tip_y)
    glVertex2f(tip_x - dx * wing + dy * wing, tip_y - dy * wing - dx * wing)
    glEnd()
    glLineWidth(1.0)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)


def cube(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(*color)
    glutSolidCube(1)
    glPopMatrix()


def cylinder(radius, height, color, slices=12):
    glColor3f(*color)
    gluCylinder(gluNewQuadric(), radius, radius * .88, height, slices, 2)


def reset_game(keep_start=False):
    global game_started, game_over, player_lane, player_x, player_z, jump_velocity
    global slide_timer, lives, coins_collected, score, distance_run, base_speed
    global shield_active, shield_charges, character_index, run_angle, hit_cooldown
    global next_fireball, next_collapse, bridge, coins, obstacles, fireballs, shield_pickups, scenery
    global blink_timer, next_shield_distance
    global super_run, super_run_timer, super_run_cooldown


    game_started = not keep_start
    game_over = False
    player_lane, player_x, player_z, jump_velocity, slide_timer = 1, 0.0, 0.0, 0.0, 0.0
    lives, coins_collected, score, distance_run, base_speed = 3, 0, 0, 0.0, 18.0
    super_run, shield_active, shield_charges, character_index, run_angle, hit_cooldown = False, False, 0, 0, 0.0, 0.0
    blink_timer= 0.0
    super_run_timer, super_run_cooldown = 0.0, 0.0


    next_fireball = random.uniform(8, 12)
    next_shield_distance = random.uniform(240, 320)
    next_collapse = random.uniform(110, 145)

    bridge, coins, obstacles, fireballs, shield_pickups, scenery = [], [], [], [], [], []
    for i in range(SEGMENT_COUNT):
        bridge.append({"y": (i - 3) * SEGMENT_LENGTH, "state": "safe", "lane": -1,
                       "timer": 0.0, "drop": 0.0})
    for i in range(24):
        scenery.append({"y": i * 15 - 30, "side": -1 if i % 2 else 1,
                        "kind": 1 if i % 3 == 1 else 0, "x": random.uniform(10, 18)})
    seed_world()
    set_message("PRESS ENTER TO BEGIN YOUR ESCAPE" if keep_start else "RUN! COLLECT COINS AND SURVIVE", 3.0)


def seed_world():
    for start in (36, 62, 91, 125, 154):
        spawn_coin_pattern(start)
    spawn_obstacle(82, "low")
    spawn_obstacle(116, "high")
    spawn_obstacle(149, "rock")


def spawn_coin_pattern(start_y):
    pattern = random.choice(("line", "curve", "jump"))
    lane = random.randrange(3)
    for i in range(6):
        if pattern == "curve":
            lane_i = max(0, min(2, lane + (i - 3) // 2))
            z = 1.4 + math.sin(i * .75) * 1.2
        elif pattern == "jump":
            lane_i, z = lane, 2.0 + (1.8 if 1 <= i <= 4 else 0)
        else:
            lane_i, z = lane, 1.35
        coins.append({"x": LANES[lane_i], "y": start_y + i * 3.1, "z": z,
                      "taken": False})


def spawn_obstacle(y=None, kind=None):
    kinds = ("low", "high", "rock", "pillar")
    kind = kind or random.choice(kinds)
    obstacles.append({"x": LANES[random.randrange(3)], "y": y if y is not None else random.uniform(105, 155),
                      "kind": kind, "hit": False})


def current_speed():
    normal = min(60.0, base_speed + distance_run * .035)
    return normal * (1.70 if super_run else 1.0)


def damage(reason):
    global lives, game_over, shield_active, hit_cooldown
    if hit_cooldown > 0 or super_run:
        return
    hit_cooldown = 1.25

    if shield_active:
        shield_active = False
        set_message("SHIELD BROKEN!", 2.0)
        return
    
    lives -= 1
    set_message(reason + "  -1 LIFE", 1.8)
    if lives <= 0:
        game_over = True
        set_message("GAME OVER", 999)


def activate_shield():
    global shield_active, shield_charges
    if not shield_active and shield_charges > 0 and game_started and not game_over:
        shield_charges -= 1
        shield_active = True
        set_message("SHIELD ACTIVATED", 1.6)
    elif not shield_active and game_started and not game_over:
        set_message("NO SHIELD", 1.8)


def trigger_collapse():
    candidates = [s for s in bridge if 10 < s["y"] < 80 and s["state"] == "safe"]
    if not candidates:
        return
    segment = min(candidates, key=lambda s: s["y"])
    segment["state"] = "warning"
    segment["lane"] = random.randrange(3)
    segment["timer"] = 0.25


def update_bridge(dt, speed):
    global blink_timer
    for segment in bridge:
        segment["y"] -= speed * dt

        if segment["state"] == "warning":
            segment["timer"] -= dt

            if segment["timer"] <= 0:
                segment["state"] = "falling"
                segment["drop"] = 0.0

        elif segment["state"] == "falling":
            segment["drop"] += 45 * dt 

            if abs(segment["y"]) < 4.3 and player_lane == segment["lane"] and player_z < 1.4:
                if not super_run:
                    blink_timer = 1.5
                damage("FELL WITH THE BRIDGE")


        if segment["y"] < -55:
            segment.update({
                "y": max(s["y"] for s in bridge) + SEGMENT_LENGTH,
                "state": "safe",
                "lane": -1,
                "timer": 0.0,
                "drop": 0.0
            })

def update_super_run_targeting():
    global player_lane

    if not super_run:
        return

    targets = [
        (coin["y"], coin["x"])
        for coin in coins
        if not coin["taken"] and 1.0 < coin["y"] < 45.0
    ]

    targets += [
        (pickup["y"], pickup["x"])
        for pickup in shield_pickups
        if 1.0 < pickup["y"] < 45.0
    ]

    if targets:
        _, target_x = min(targets, key=lambda target: target[0])
        player_lane = min(range(3), key=lambda lane: abs(LANES[lane] - target_x))


def update_world(dt):
    global distance_run, base_speed, run_angle, slide_timer, blink_timer
    global player_z, jump_velocity, player_x
    
    global next_fireball, next_collapse, coin_spin, hit_cooldown, message_timer, next_shield_distance

    if not game_started or game_over:
        return
    speed = current_speed()
    update_super_run_targeting()

    global super_run, super_run_timer, super_run_cooldown

    if super_run:
        super_run_timer -= dt
        if super_run_timer <= 0:
            super_run = False
            super_run_timer = 0.0
            super_run_cooldown = 10.0
            set_message("SUPER RUN ENDED — RESETTING", 2.0)
    elif super_run_cooldown > 0:
        super_run_cooldown = max(0.0, super_run_cooldown - dt)


    distance_run += speed * dt
    run_angle = (run_angle + speed * dt * 12) % 360
    coin_spin = (coin_spin + speed * dt * 20) % 360

    blink_timer = max(0.0, blink_timer - dt)

    player_x += (LANES[player_lane] - player_x) * min(1, 10 * dt)
    if player_z > 0 or jump_velocity > 0:
        player_z += jump_velocity * dt
        jump_velocity -= 23 * dt
        if player_z <= 0:
            player_z, jump_velocity = 0, 0
    slide_timer = max(0.0, slide_timer - dt)
    hit_cooldown = max(0.0, hit_cooldown - dt)
  
    message_timer -= dt
    update_bridge(dt, speed)
    update_coins(dt, speed)
    update_shield_pickups(dt, speed)
    update_obstacles(dt, speed)
    update_fireballs(dt, speed)
    update_scenery(dt, speed)
    next_fireball -= dt

    if next_fireball <= 0:
        lane = player_lane
        fall_speed = 8.0 + speed * .45

        fireballs.append({
            "x": LANES[lane],
            "y": random.uniform(38, 50),
            "z": 40,
            "vy": -fall_speed,
            "gravity": 17.0 + speed * .25,
            "warned": False
        })

        next_fireball = random.uniform(9, 15)

        
    if distance_run >= next_collapse:
        trigger_collapse()
        next_collapse += random.uniform(35, 55)

    # Periodic shield collectible; this makes a broken shield recoverable.
    if distance_run >= next_shield_distance:
        shield_pickups.append({
            "x": LANES[random.randrange(3)],
            "y": random.uniform(112, 150),
            "z": 1.7
        })
        next_shield_distance += random.uniform(240, 340)


def update_coins(dt, speed):
    global score, coins_collected
    for coin in coins:
        coin["y"] -= speed * dt
        if not coin["taken"] and abs(coin["y"] - PLAYER_Y) < 2.0 and abs(coin["x"] - player_x) < 1.6:
            if abs(coin["z"] - (player_z + 1.3)) < 2.7 or super_run:
                coin["taken"] = True
                coins_collected += 1
                score += 10
    coins[:] = [c for c in coins if c["y"] > -24 and not c["taken"]]
    while len(coins) < 25:
        farthest = max([c["y"] for c in coins] + [105])
        spawn_coin_pattern(farthest + random.uniform(15, 29))


def update_shield_pickups(dt, speed):
    global shield_charges
    for pickup in shield_pickups:
        pickup["y"] -= speed * dt
        if abs(pickup["y"]) < 2.0 and abs(pickup["x"] - player_x) < 1.5:
            pickup["z"] = -99
            shield_charges = min(2, shield_charges + 1)
            set_message("SHIELD CHARGE COLLECTED", 1.8)
    shield_pickups[:] = [s for s in shield_pickups if s["y"] > -24 and s["z"] > -20]


def update_obstacles(dt, speed):
    global blink_timer
    for obj in obstacles:
        obj["y"] -= speed * dt
        close = abs(obj["y"]) < 2.1 and abs(obj["x"] - player_x) < 1.75
        if close and not obj["hit"]:
            obj["hit"] = True
            if obj["kind"] == "low" and player_z > 1.25:
                score_bonus(15)
            elif obj["kind"] == "high" and slide_timer > 0:
                score_bonus(15)
            else:
                if not super_run:
                    blink_timer = 1.5 
                damage("OBSTACLE HIT")
    obstacles[:] = [o for o in obstacles if o["y"] > -20]
    while len(obstacles) < 6:
        farthest = max([o["y"] for o in obstacles] + [105])
        spawn_obstacle(farthest + random.uniform(20, 37))


def score_bonus(amount):
    global score
    score += amount


def update_fireballs(dt, speed):
    for ball in fireballs:
        ball["y"] -= speed * dt
        ball["z"] += ball["vy"] * dt
        ball["vy"] -= ball["gravity"] * dt
        if ball["z"] < .7 and abs(ball["y"]) < 5 and abs(ball["x"] - player_x) < 2.0:
            ball["z"] = -99
            damage("FIREBALL STRIKE")
    fireballs[:] = [f for f in fireballs if f["y"] > -25 and f["z"] > -20]


def update_scenery(dt, speed):
    for item in scenery:
        item["y"] -= speed * dt * .92
        if item["y"] < -38:
            item["y"] += 15 * len(scenery)
            item["kind"] = random.choice((0, 0, 1))
            item["x"] = random.uniform(10, 18)


def draw_bridge():
    for seg in bridge:
        for lane in range(3):
            glPushMatrix()
            glTranslatef(LANES[lane], seg["y"], -0.35)
            collapsed = seg["lane"] == lane and seg["state"] in ("warning", "falling")
            if collapsed:
                if seg["state"] == "warning":
                    glColor3f(.72, .20 + .15 * abs(math.sin(time.perf_counter() * 8)), .08)
                    glRotatef(5 * math.sin(time.perf_counter() * 14), 0, 1, 0)
                else:
                    glTranslatef(0, 0, -seg["drop"])
                    glRotatef(min(78, seg["drop"] * 7), 0, 1, 0)
                    glColor3f(.24, .18, .13)
            else:
                glColor3f(.34, .31, .25)
            glScalef(3.95, SEGMENT_LENGTH - .35, .62)
            glutSolidCube(1)
            glPopMatrix()
            if not collapsed or seg["state"] == "warning":
                cube(LANES[lane], seg["y"] + SEGMENT_LENGTH / 2 - .35, .06, 3.82, .12, .11, (.61, .56, .43))
        # low stone rails at far edges
        cube(-6.35, seg["y"], .35, .25, SEGMENT_LENGTH, .8, (.27, .25, .19))
        cube(6.35, seg["y"], .35, .25, SEGMENT_LENGTH, .8, (.27, .25, .19))


def draw_coin(coin):
    glPushMatrix()
    glTranslatef(coin["x"], coin["y"], coin["z"])
    glDisable(GL_LIGHTING)
    glColor3f(1.0, .72, .08)
    glutSolidSphere(.52, 16, 12)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_obstacle(obj):
    x, y, kind = obj["x"], obj["y"], obj["kind"]
    if kind == "low":
        # A bright, solid jump block: it cannot be passed underneath.
        cube(x, y, .75, 2.7, .72, 1.5, (.88, .20, .05))
        cube(x, y - .38, 1.05, 2.35, .08, .22, (1.0, .78, .08))
        cube(x, y - .38, 1.38, 1.65, .08, .18, (1.0, .78, .08))
        for dx in (-1.08, 1.08):
            cube(x + dx, y, 1.55, .22, .25, .35, (.45, .07, .03))
    elif kind == "high":
        # A cool-blue overhead gate: its raised lower edge leaves room to slide.
        cube(x, y, 2.62, 2.95, .70, .62, (.08, .75, .15))
        for dx in (-1.1, 1.1):
            cube(x + dx, y, 1.31, .28, .34, 2.62, (.04, .45, .10))
            cube(x + dx, y - .42, 2.62, .42, .10, .18, (.35, 1.0, .45))
    elif kind == "pillar":
        # Match the former outer-bridge pillar design for a consistent obstacle.
        cube(x, y, 2.2, 1.0, 1.0, 4.4, (.29, .27, .22))
        cube(x, y, 4.7, 1.65, 1.55, .45, (.35, .32, .25))
    else:
        glPushMatrix(); glTranslatef(x, y, .7); glColor3f(.30, .28, .23); glScalef(1.4, 1.2, .9); glutSolidSphere(1, 12, 8); glPopMatrix()


def draw_fireball(ball):
    glPushMatrix()
    glTranslatef(ball["x"], ball["y"], ball["z"])
    glDisable(GL_LIGHTING)
    glColor3f(1.0, .16, .02)
    glutSolidSphere(.82, 14, 12)
    glColor3f(1.0, .72, .08)
    glutSolidSphere(.48, 12, 10)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_shield_pickup(pickup):
    glPushMatrix()
    glTranslatef(pickup["x"], pickup["y"], pickup["z"])
    glDisable(GL_LIGHTING)
    glColor3f(.10, .78, 1.0)
    glutSolidSphere(.55, 16, 12)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_tree(x, y):
    glPushMatrix()
    glTranslatef(x, y, 0)
    cylinder(.44, 5.3, (.22, .13, .06), 10)
    # One round canopy keeps the tree silhouette simple and circular.
    glPushMatrix(); glTranslatef(0, 0, 5.45); glColor3f(.08, .30, .10); glutSolidSphere(1.6, 12, 12); glPopMatrix()
    glPopMatrix()


def draw_scenery():
    for item in scenery:
        x = item["side"] * item["x"]
        y = item["y"]
        if item["kind"] == 0:
            draw_tree(x, y)
        elif item["kind"] == 1:
            # torch
            cylinder_at(x, y, .0, .18, 3.0, (.22, .16, .09))
            glPushMatrix(); glTranslatef(x, y, 3.18); glDisable(GL_LIGHTING); glColor3f(1,.34,.03); glutSolidSphere(.42, 10, 8); glEnable(GL_LIGHTING); glPopMatrix()


def cylinder_at(x, y, z, radius, height, color):
    glPushMatrix(); glTranslatef(x, y, z); cylinder(radius, height, color); glPopMatrix()


def draw_player():
    if blink_timer > 0 and int(blink_timer * 12) % 2 == 0:
        return

    name, body, accent = CHARACTERS[character_index]
    glPushMatrix()
    glTranslatef(player_x, PLAYER_Y, player_z)
    glRotatef(180, 0, 0, 1)  # face along positive Y
    scale = .72
    glScalef(scale, scale, scale)
    crouch = slide_timer > 0
    if crouch:
        glTranslatef(0, 0, -.4)
    swing = 0 if (player_z > .1 or crouch) else math.sin(math.radians(run_angle)) * 28

    # Legs (using accent color)
    for x, phase in ((-.42, swing), (.42, -swing)):
        glPushMatrix(); glTranslatef(x, 0, .05); glRotatef(phase, 1, 0, 0); cylinder(.22, 1.25, accent); glPopMatrix()

    # Torso (using main body color)
    cylinder_at(0, 0, 1.08, .57, 1.36 if not crouch else .82, body)
    torso_top = 2.44 if not crouch else 1.65

    # Arms (using body color)
    for x, phase in ((-.73, -swing), (.73, swing)):
        glPushMatrix(); glTranslatef(x, 0, torso_top - .48); glRotatef(phase, 1, 0, 0); cylinder(.16, 1.05, body); glPopMatrix()

    # Head (Standardized across all characters)
    glPushMatrix(); glTranslatef(0, 0, torso_top + .36); glColor3f(.83,.60,.42); glutSolidSphere(.48, 14, 12); glPopMatrix()

    glPopMatrix()
    draw_shield()

    if super_run:
        glDisable(GL_LIGHTING)
        glColor4f(.20, .75, 1.0, .32)
        for i in range(4):
            cube(player_x, -2.2 - i * 1.3, player_z + 1.2, .6 - i*.1, 1.5, .25, (.10,.6,1.0))
        glEnable(GL_LIGHTING)


def draw_shield():
    if shield_active:
        glPushMatrix()
        glTranslatef(player_x, PLAYER_Y, player_z + 1.65)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(.10, .72, 1.0, .22)
        glutSolidSphere(2.3, 18, 14)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(62, W / float(H), .1, 260)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(player_x * .22, -20, 10.8, player_x * .50, 20, 2.3, 0, 0, 1)


def draw_hud():
    if not game_started:
        draw_text(W//2 - 155, H - 135, "RUN FOR LIFE", (1,.75,.15), GLUT_BITMAP_TIMES_ROMAN_24)
        control_x = W//2 - 145
        description_x = W//2 - 65
        first_row_y = H - 205

        # Draw the movement controls as arrows; gameplay keys remain unchanged.
        draw_control_arrow(control_x - 25, first_row_y, "left")
        draw_control_arrow(control_x + 25, first_row_y, "right")
        draw_text(description_x, first_row_y - 7, "Move left / right", (.9,.92,.84))
        draw_control_arrow(control_x, first_row_y - 31, "up")
        draw_text(description_x, first_row_y - 38, "Jump", (.9,.92,.84))
        draw_control_arrow(control_x, first_row_y - 62, "down")
        draw_text(description_x, first_row_y - 69, "Slide", (.9,.92,.84))

        lines = ["   C               Change character", "   S               Activate shield", "   X               Super Run", "   R               Restart", "ENTER       Start game"]
        for i, line in enumerate(lines):
            draw_text(W//2 - 170, H - 298 - i*31, line, (.9,.92,.84))
        return
    name = CHARACTERS[character_index][0]
    draw_text(18, H - 32, "RUN FOR LIFE", (1,.75,.12), GLUT_BITMAP_TIMES_ROMAN_24)
    rows = [f"Character: {name}", f"Lives: {lives}", f"Coins: {coins_collected}",
            f"Score: {score}", f"Distance: {int(distance_run)}", f"Speed: {current_speed():.1f}",
            "Shield: ACTIVE" if shield_active else f"Shield Number: {shield_charges} (S)",
            "SUPER RUN: ON" if super_run else "Super Run: OFF"]
    for i, row in enumerate(rows):
        color = (.25,.85,1) if "ACTIVE" in row else ((1,.32,.12) if "ON" in row else (1,1,1))
        draw_text(18, H - 65 - i*24, row, color)
    if message_timer > 0:
        draw_text(W//2 - max(100, len(message)*4.8), H - 45, message, (1,.48,.08), GLUT_BITMAP_HELVETICA_18)
    if game_over:
        draw_text(W//2 - 85, H//2 + 55, "GAME OVER", (1,.20,.08), GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(W//2 - 105, H//2 + 20, f"Score: {score}    Coins: {coins_collected}")
        draw_text(W//2 - 95, H//2 - 10, f"Distance: {int(distance_run)}")
        draw_text(W//2 - 120, H//2 - 55, "Press R to RESTART", (1,.82,.2))


def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, W, H)
    setup_camera()
    glLightfv(GL_LIGHT0, GL_POSITION, (8, -8, 24, 1))
    draw_scenery()
    draw_bridge()
    for coin in coins: draw_coin(coin)
    for pickup in shield_pickups: draw_shield_pickup(pickup)
    for obstacle in obstacles: draw_obstacle(obstacle)
    for ball in fireballs: draw_fireball(ball)
    draw_player()
    draw_hud()
    glutSwapBuffers()


def keyboard_listener(key, x, y):
    global character_index, super_run, game_started, super_run_timer, super_run_cooldown

    if key in (b'\r', b'\n') and not game_started:
        game_started = True
        set_message("RUN! COLLECT COINS AND SURVIVE", 2.5)

    if key in (b'r', b'R'):
        reset_game(False)
        return

    if game_over or not game_started:
        return

    if key in (b'c', b'C'):
        character_index = (character_index + 1) % len(CHARACTERS)
        set_message("CHARACTER: " + CHARACTERS[character_index][0], 1.5)

    elif key in (b's', b'S'):
        activate_shield()

    elif key in (b'x', b'X'):
        if super_run:
            super_run = False
            super_run_timer = 0.0
            super_run_cooldown = 10.0
            set_message("SUPER RUN OFF — RESETTING FOR 10 SECONDS", 2.0)
        elif super_run_cooldown > 0:
            set_message(f"SUPER RUN READY IN {math.ceil(super_run_cooldown)} SECONDS", 1.5)
        else:
            super_run = True
            super_run_timer = 15.0
            set_message("SUPER RUN ACTIVATED — 15 SECONDS", 1.8)

    glutPostRedisplay()


def special_key_listener(key, x, y):
    global player_lane, jump_velocity, slide_timer

    if game_over or not game_started:
        return

    if key == GLUT_KEY_LEFT:
        player_lane = max(0, player_lane - 1)

    elif key == GLUT_KEY_RIGHT:
        player_lane = min(2, player_lane + 1)

    elif key == GLUT_KEY_UP:
        if player_z <= 0.01 and slide_timer <= 0:
            jump_velocity = 9.3

    elif key == GLUT_KEY_DOWN:
        if player_z <= 0.05:
            slide_timer = 0.2

    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    # No essential mouse controls by design.
    glutPostRedisplay()


def idle():
    global last_time
    now = time.perf_counter()
    dt = min(.05, now - last_time)
    last_time = now
    update_world(dt)
    glutPostRedisplay()


def main():
    global last_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W, H)
    glutInitWindowPosition(70, 45)
    glutCreateWindow(b"Run for Life")
    glClearColor(.035, .095, .105, 1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, .84, .62, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (.28, .30, .34, 1))
    glShadeModel(GL_SMOOTH)
    reset_game(True)
    last_time = time.perf_counter()
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()
