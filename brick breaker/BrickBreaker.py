# coding: utf-8

from scene import *
import sound
import pickle
import time
from math import sin, cos, pi, ceil
from random import uniform as rnd, choice, randint
from game_menu import MenuScene
from game_levels import colors
from colorsys import hsv_to_rgb
import sys
with open('game_levels_normal.pkl', 'rb') as f:
	levels = pickle.load(f)
with open('game_levels_special.pkl', 'rb') as f:
	specials = pickle.load(f)
A = Action
print(">>>BrickBreaker<<<")


def _cmp(a, b):
	return ((a>b)-(a<b))

if sys.version_info[0] >= 3:
	cmp = _cmp

paddle_speed = 100
min_ball_speed = 5
max_ball_speed = 20
distance_move = 2
# How much faster the ball gets when it hits a brick:
brick_speedup = 0.0
# How much faster the ball gets when a new level is reached:
level_speedup = 1
powerup_chance = 0.4
filter_names = ['None', 'Gray', 'B&W', 'LCD', 'Wavy', 'Retro', 'invert']
# Helper functions for collision testing:
def closest_point(rect, circle):
	return Point(max(rect.min_x, min(rect.max_x, circle.x)), max(rect.min_y, min(rect.max_y, circle.y)))

def hit_test(rect, circle, radius, bbox=None):
	if bbox and not rect.intersects(bbox):
		return False
	return abs(closest_point(rect, circle) - circle) < radius

# Particle effect when the ball hits a brick:
class Explosion (Node):
	def __init__(self, brick, *args, **kwargs):
		Node.__init__(self, *args, **kwargs)
		self.position = brick.position
		for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
			p = SpriteNode(brick.texture, scale=0.5, parent=self)
			p.position = brick.size.w/4 * dx, brick.size.h/4 * dy
			p.size = brick.size
			d = 0.4
			r = 30
			p.run_action(A.move_to(rnd(-r, r), rnd(-r, r), d))
			p.run_action(A.scale_to(0, d))
			p.run_action(A.rotate_to(rnd(-pi/2, pi/2), d))
		self.run_action(A.sequence(A.wait(d), A.remove()))
#flash when a eating brick is hit		
class black_hole(Node):
	def __init__(self, ball, *args, **kwargs):
		Node.__init__(self, *args, **kwargs)
		for i in range(10):
			sound.play_effect('arcade:Explosion_5', .5)
			p = SpriteNode('shp:Spark', z_position=-1, parent=self)
			p.blend_mode = BLEND_ADD
			p.color = '#ffffff'
			angle = rnd(0, pi*2)
			d = rnd(0, 11)
			p.scale = 5
			x, y = cos(angle)*d, sin(angle)*d
			p.position = ball
			p.run_action(A.sequence(A.fade_to(0, 0.8), A.wait(d), A.remove()))
#Score pop up when a brick is hit			
class Texter (Node):
	def __init__(self, brick, *args, **kwargs):
		text = str(brick.text)
		p = LabelNode(text, font=('Arial Rounded MT Bold', 6), position=brick.position, scale=6, parent=self)
		p.color = '#000000'
		pb = LabelNode(text, font=('Arial Rounded MT Bold', 6), position=brick.position, scale=5, parent=self)
		pb.color = '#ffffff'
		d = 0.4
		r = 0
		ar = rnd(-pi/2, pi/2)
		pb.run_action(A.scale_to(0, d))
		p.run_action(A.scale_to(0, d))
		pb.run_action(A.rotate_to(ar, d))
		p.run_action(A.rotate_to(ar, d))
		self.run_action(A.sequence(A.wait(d), A.remove()))
		del self
# Simple SpriteNode subclasses for the different game objects:

class Ball (SpriteNode):
	def __init__(self, v=(0, 0), r=11, *args, **kwargs):
		SpriteNode.__init__(self, 'pzl:BallBlue', *args, **kwargs)
		self.size = (r*2, r*2)
		self.v = Vector2(*v)
		self.r = r
		self.ball_speed = 10.0
		self.last_collision = None
		self.is_new = True
		self.powerup_type = 0
	
	def update_effects(self):
		# If the ball has a powerup, draw a red or blue "tail"
		if not self.powerup_type:
			return
		for i in range(3):
			p = SpriteNode('shp:Spark', z_position=-1, parent=self.parent)
			p.blend_mode = BLEND_ADD
			p.color = '#ff0000'
			angle = rnd(0, pi*2)
			d = rnd(0, self.r-4)
			if self.powerup_type == 1:
				flame_hue = '#ff5114'
			elif self.powerup_type == 2:
				flame_hue = '#808bff'
			elif self.powerup_type == 6:
				flame_hue = '#2cff00'
			elif self.powerup_type == 7:
				flame_hue = '#f4ff00'
			elif self.powerup_type == 8:
				flame_hue = '#313131'
			p.color = flame_hue
			p.scale = 1.2
			x, y = cos(angle)*d, sin(angle)*d
			p.position = self.position + (x, y)
			p.run_action(A.sequence(A.fade_to(0, 0.2), A.remove()))
#spawn a powerup when a brick is broken
class Powerup (SpriteNode):
	def __init__(self, powerup_type, v=(0, 0), *args, **kwargs):
		if powerup_type == 1:
			img = 'spc:PillRed' 
		elif powerup_type == 2:
			img = 'spc:PillBlue'
		elif powerup_type == 6:
			img = 'spc:PillGreen'
		elif powerup_type == 7:
			img = 'spc:PillYellow'
		else:
			img = 'spc:BoltSilver'
		SpriteNode.__init__(self, img, *args, **kwargs)
		self.powerup_type = powerup_type
		self.v = Vector2(*v)
		
#define brick
class Brick (SpriteNode):
	def __init__(self, brick_type, *args, **kwargs):
		img = colors.get(brick_type, 'pzl:Red8')
		SpriteNode.__init__(self, img, *args, **kwargs)
		self.brick_type = brick_type
		self.asher = ([0,0,0])
		self.v = Vector2(0)
# The actual game logic:

class Game (Scene):
	def setup(self):
		self.special = specials
		self.fun = 0
		self.music = sound.Player("Songs/Rock fight.m4a")
		self.music.stop()
		self.sp_power = 0
		self.filter = 0
		self.cow = 0
		self.dog = 0
		self.score = 0
		self.level_music = 0
		self.level = 0
		self.same_level = 0
		self.level_loader = []
		self.apple = 0
		self.paddle_powerup = 0
		self.paddle_charge = 0
		self.lives_left = 6
		self.level_start_time = 0
		self.bricks = []
		self.balls = []
		self.glitch = 0
		self.points = 0
		self.powerups = []
		self.top_bg = SpriteNode(parent=self, size=(self.size.w, 90), position=(self.size.w/2, self.size.y-45))
		self.top_bg.color = '#000000'
		prep = self.size.h / 550
		brick_w = self.size.w / 24
		brick_h = (self.size.y - self.top_bg.size.h*prep) / 28
		self.spw, self.sph = brick_w, brick_h
		self.moveh = self.sph*distance_move
		self.movew = self.spw*distance_move
		self.ball_r = 11 if self.size.w > 760 else 7
		# Lower ball speed on iPhone (everything is smaller):
		self.speed_scale = 1.0 if self.size.w > 760 else 0.65
		self.effect_node = EffectNode(parent=self)
		with open('filters.fsh') as f:
			self.effect_node.shader = Shader(f.read())
		self.effect_node.crop_rect = self.bounds
		self.effect_node.effects_enabled = False
		self.game_node = Node(parent=self.effect_node)
		self.hud_hearts = [SpriteNode('plf:HudHeart_full', position = (30 + i * 32, self.size.h - 65), scale=0.5, parent=self) for i in range(6)]
		self.pause_button = SpriteNode('iow:pause_32', position=(32, self.size.h-32), parent=self)
		paddle_y = 120 if self.size.w > 760 else 70
		self.paddle = SpriteNode('pzl:PaddleBlue', position=(self.size.w/2, paddle_y), parent=self.game_node)
		self.paddle.scale = 1.0 if self.size.w > 760 else 0.7
		self.paddle_target = self.size.w/2
		self.score_label = LabelNode('Brick Breaker', font=('Avenir Next', 40), position=(self.size.w/2, self.size.h-50), parent=self)
		right_wall = Rect(self.size.w, 0, 100, self.size.h)
		left_wall = Rect(-100, 0, 100, self.size.h)
		top_wall = Rect(0, self.size.h-90, self.size.w, 100)
		self.walls = [SpriteNode(position=rect.center(), size=rect.size) for rect in (left_wall, right_wall, top_wall)]
		self.background_color = '#838383'
		self.load_highscore()
		self.show_start_menu()
		
	def load_highscore(self):
		try:
			with open('.brickbreaker_highscore', 'r') as f:
				self.highscore = int(f.read())
		except:
			self.highscore = 0
	
	def save_highscore(self):
		with open('.brickbreaker_highscore', 'w') as f:
			f.write(str(self.highscore))
	
	def new_game(self):
		self.music = sound.Player("Songs/Broken beat.m4a")
		self.music.stop()
		self.sounder = "Songs/Broken beat.m4a"
		self.level = 0
		for b in self.bricks:
			b.remove_from_parent()
		self.bricks = []
		for b in self.balls:
			b.remove_from_parent()
		self.balls = []
		self.spawn_ball()
		self.level = randint(0, len(levels) - 1)
		self.load_level(levels[randint(0, len(levels) - 1)])
		self.level_loader.append(self.level)
		self.score = 0
		self.lives_left = 6
		self.paddle_powerup = 0
		self.paddle_charge = 0
		for h in self.hud_hearts:
			h.alpha = 1
		self.score_label.text = '0'
	
	def load_level(self, level_str):
		self.sp_power = 0
		lines = level_str.splitlines()
		brick_w = self.size.w / 24
		brick_h = (self.top_bg.position.y - 45) / 30
		self.spw, self.sph = brick_w, brick_h
		min_x = 0 + brick_w/2
		min_y = 0 + brick_h/2
		for y, line in enumerate(reversed(lines)):
			for x, char in enumerate(line):
				if char == ' ': 
					continue
				pos = Point(x * brick_w + min_x, min_y + y * brick_h)
				brick = Brick(char, position=pos, parent=self.game_node)
				brick.size = (brick_w, brick_h)
				if brick.brick_type == 'u':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 0
				elif brick.brick_type == '>':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 1
				elif brick.brick_type == '<':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 2
				elif brick.brick_type == '^':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 3
				elif brick.brick_type == '|':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 4
				elif brick.brick_type == '!':
					brick.alpha = 100
				else:
					brick.asher[0] = 0
					brick.asher[1] = 0
					brick.asher[2] = 0
				self.bricks.append(brick)
		for i, b in enumerate(self.bricks):
			b.scale = 0
			b.run_action(A.sequence(A.wait(i*0.001), A.scale_to(1, 0.25, 4)))
		self.level_start_time = self.t
	
	def load_special(self, level_str):
		lines = level_str.splitlines()
		brick_w = self.size.w / 24
		brick_h = (self.top_bg.position.y - 45) / 30
		self.spw, self.sph = brick_w, brick_h
		min_x = 0 + brick_w/2
		min_y = 0 + brick_h/2
		for y, line in enumerate(reversed(lines)):
			for x, char in enumerate(line):
				if char == ' ': continue
				pos = Point(x * brick_w + min_x, min_y + y * brick_h)
				brick = Brick(char, position=pos, parent=self.game_node)
				brick.size = (brick_w, brick_h)
				if brick.brick_type == 'u':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 0
				elif brick.brick_type == '>':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 1
				elif brick.brick_type == '<':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 2
				elif brick.brick_type == '^':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 3
				elif brick.brick_type == '|':
					brick.asher[0] = 1
					brick.asher[1] = 0
					brick.asher[2] = 4
				elif brick.brick_type == '!':
					brick.color ='#ffffff'
				else:
					brick.asher[0] = 0
					brick.asher[1] = 0
					brick.asher[2] = 0
				self.bricks.append(brick)
		for i, b in enumerate(self.bricks):
			b.scale = 0
			b.run_action(A.sequence(A.wait(i*0.001), A.scale_to(1, 0.25, 4)))
		self.level_start_time = self.t
	
	def song(self):
		if self.music.playing == False:
			self.music = sound.Player(self.sounder)
			self.music.play()
			
		
	def glitcher(self):
		self.cow += 1
		if self.cow == 100:
			self.apple += 1
			if self.apple == 1:
				self.background_color = '#168200'
			elif self.apple == 2:
				self.background_color = '#820000'
			elif self.apple == 3:
				self.background_color = '#000b82'
			elif self.apple == 4:
				self.background_color = '#008070'
			elif self.apple == 5:
				self.background_color = '#7a0080'
			elif self.apple == 6:
				self.background_color = '#808080'
			elif self.apple == 7:
				self.background_color = '#7c8100'
			elif self.apple == 8:
				self.background_color = '#ff8500'
			elif self.apple == 9:
				self.background_color = '#000000'
			elif self.apple == 10:
				self.background_color = '#9a9a9a'
			if self.apple >= 10:
				self.apple = 0
		if self.cow == 100:
			self.cow = 0
		
	def move_brick(self):
		apple = 0
		while apple + 1 <= len(self.bricks):
			if self.bricks[apple].asher[2] == 1:
				self.bricks[apple].asher[1] += 1
				self.bricks[apple].position += (self.movew/100, 0)
				if self.bricks[apple].asher[1] >= 100:
					self.bricks[apple].asher[2] = 2
			elif self.bricks[apple].asher[2] == 2:
				self.bricks[apple].asher[1] -= 1
				self.bricks[apple].position -= (self.movew/100, 0)
				if self.bricks[apple].asher[1] <= -100:
					self.bricks[apple].asher[2] = 1
			elif self.bricks[apple].asher[2] == 3:
				self.bricks[apple].asher[1] += 1
				self.bricks[apple].position += (0, self.moveh/100)
				if self.bricks[apple].asher[1] >= 100:
					self.bricks[apple].asher[2] = 4
			elif self.bricks[apple].asher[2] == 4:
				self.bricks[apple].asher[1] -= 1
				self.bricks[apple].position -= (0, self.moveh/100)
				if self.bricks[apple].asher[1] <= -100:
					self.bricks[apple].asher[2] = 3
			apple += 1

	def glitche(self):
		if randint(1, 2) == 2:
			self.apple = randint(1, 10)
			if self.apple == 1:
				self.background_color = '#2cff00'
			elif self.apple == 2:
				self.background_color = '#ff0000'
			elif self.apple == 3:
				self.background_color = '#0016ff'
			elif self.apple == 4:
				self.background_color = '#00ffdf'
			elif self.apple == 5:
				self.background_color = '#f300ff'
			elif self.apple == 6:
				self.background_color = '#ffffff'
			elif self.apple == 7:
				self.background_color = '#f5ff00'
			elif self.apple == 8:
				self.background_color = '#ff8500'
			elif self.apple == 9:
				self.background_color = '#000000'
			elif self.apple == 10:
				self.background_color = '#838383'
	
	def update(self):
		if self.glitch == 1:
			self.glitcher()
		self.song()
		self.move_brick()
		self.move_paddle()
		self.update_all_balls()
		self.update_powerups()
		if not self.balls:
			self.ball_lost()
		if not self.bricks:
			self.level_finished()
		else:
			cat = 0
			yoyo = 1
			while len(self.bricks) != cat and yoyo == 1:
				apple = self.bricks[cat]
				if apple.asher[0] == 0:
					yoyo = 0
				cat += 1
			if yoyo == 1:
				apple = 0
				while len(self.bricks) >= apple + 1:
					self.bricks[apple].remove_from_parent()
					del self.bricks[apple]

	def update_powerups(self):
		for p in list(self.powerups):
			p.position += p.v
			if p.position.y < -50:
				p.remove_from_parent()
				self.powerups.remove(p)
			if self.paddle.frame.intersects(p.frame):
				sound.play_effect('arcade:Powerup_1', 0.25, 0.8)
				p.remove_from_parent()
				self.powerups.remove(p)
				self.paddle_powerup = p.powerup_type
				if p.powerup_type == 1:
					self.paddle_charge = 3
				else:
					if p.powerup_type ==  6 and self.paddle_charge <= 4:
						self.paddle_charge += 1
					else:
						self.paddle_charge = 1
				if p.powerup_type == 1:
					self.paddle.color = '#ffa7a8'
				elif p.powerup_type == 2:
					self.paddle.color = '#a7e2ff'
				elif p.powerup_type == 6:
					self.paddle.color = '#75ff58'
				elif p.powerup_type == 7:
					self.paddle.color = '#f4ff00'
				elif p.powerup_type == 8:
					self.paddle.color = '#141414'
					self.glitch = 1

	def update_all_balls(self):
		for ball in list(self.balls):
			ball.update_effects()
			# Update in multiple steps, so a ball cannot pass through a brick in a single frame:
			steps = int(ceil(abs(ball.v)/5.0))
			for i in range(steps):
				self.update_ball(ball, ball.v / steps)
			if ball.position.y + 75 <= 0:
				self.balls.remove(ball)
				ball.remove_from_parent()
				del ball
			elif ball.position.y - 75 >= self.size.h:
				self.balls.remove(ball)
				ball.remove_from_parent()
				del ball
			elif ball.position.x - 75 >= self.size.w:
				self.balls.remove(ball)
				ball.remove_from_parent()
				del ball
			elif ball.position.x + 75 <= 0:
				self.balls.remove(ball)
				ball.remove_from_parent()
				del ball
				
	def update_ball(self, ball, v):
		bp = ball.position + v
		ball_r = ball.r
		colliders = self.bricks + self.walls + [self.paddle]
		ball_bbox = Rect(bp.x-ball_r, bp.y-ball_r, ball_r*2, ball_r*2)
		collisions = []
		new_ball = ball.is_new
		for node in colliders:
			if new_ball and node != self.paddle:
				continue
			if node == ball.last_collision:
				continue
			frame = node.frame
			if node == self.paddle:
				# Make the paddle a little larger than it actually is:
				frame = frame.inset(-10, -5, 0, -5)
			if hit_test(frame, bp, ball_r, ball_bbox):
				collisions.append((frame, node))
		if not collisions:
			ball.position = bp
			return
		# Move the ball back where it came from until it doesn't collide anymore:
		while any(hit_test(c[0], bp, ball_r) for c in collisions):
			bp -= (v / abs(v))
		# Find the closest collision point:
		collisions = [(c[1], closest_point(c[0], bp)) for c in collisions] 
		sorted_collisions = sorted(collisions, key=lambda x: abs(x[1] - bp))
		collider, p = sorted_collisions[0]
		if isinstance(collider, Brick):
			if collider.brick_type == '!':
				bp = Point(100, -100)
				ball.v = (0.00, -5.00)
				ball.powerup_type = 0
			self.destroy_brick(ball, collider)
			if ball.powerup_type == 2 and collider.asher[0] != 1:
				sound.play_effect('digital:Laser5', 0.2)
				return 
			elif ball.powerup_type == 6:
				sound.play_effect('arcade:Explosion_7', 0.2)
			elif ball.powerup_type == 7:
				sound.play_effect('arcade:Explosion_2', 0.2)
			elif ball.powerup_type == 8 and collider.asher[0] != 1:
				sound.play_effect('arcade:Hit_2', 0.2)
				return 
		self.play_collision_sound(collider)
		ball.last_collision = collider
		side_hit = abs(v.x) > 0 and cmp(bp.x - collider.position.x, 0) != cmp(v.x, 0) and abs(bp.x - p.x) > abs(bp.y - p.y)
		v *= (-1, 1) if side_hit else (1, -1)
		if collider == self.paddle and v.y > 0:
			# Adjust the ball's direction relative to where it hit the paddle
			dx = bp.x - self.paddle.position.x
			paddle_w = self.paddle.size.w
			angle = dx / (paddle_w/3.0) * pi/6
			if abs(angle) < 0.22:
				angle = 0.22 * (cmp(angle, 0) or 1.0)
			v = Vector2(sin(angle), cos(angle))
			ball.powerup_type = self.paddle_powerup
			self.paddle_charge = max(0, self.paddle_charge - 1)	
			if self.paddle_charge <= 0:
				self.paddle_powerup = 0
				self.paddle.color = 'white'
		ball.position = bp
		ball.is_new = False
		ball.v = (v/abs(v)) * ball.ball_speed * self.speed_scale
	
	def ball_lost(self):
		sound.play_effect('digital:ZapThreeToneDown', 0.5)
		self.lives_left -= 1
		for i, heart in enumerate(self.hud_hearts):
			heart.alpha = 1 if self.lives_left > i else 0
		if self.lives_left <= 0:
			self.game_over()
		else:
			self.spawn_ball()
	
	def game_over(self):
		self.music = sound.Player("Songs/Love?.m4a")
		self.music.number_of_loops = 10
		self.music.play()
		if self.score > self.highscore:
			self.highscore = self.score
			self.save_highscore()
		self.paused = True
		self.menu = MenuScene('Game Over', 'Highscore: %i' % self.highscore, ['New Game', 'Filter: ' + filter_names[self.filter]])
		self.present_modal_scene(self.menu)
		
	def level_finished(self):
		self.glitch = 0
		self.score += max(0, 100-int(self.t - self.level_start_time)) * (self.level+1)
		self.score_label.text = str(self.score)
		self.level_music += 1
		sound.play_effect('digital:ZapThreeToneUp', 0.5)
		for b in self.balls:
			b.remove_from_parent()
			del b
		self.balls = []
		for p in self.powerups:
			p.remove_from_parent()
			del p
		self.powerups = []
		self.fun = 0
		if self.level_music == 1:
			self.sounder = "Songs/Disco beat.m4a"
			self.background_color = '#005107'
		elif self.level_music == 3:
			self.sounder = "Songs/Rock fight.m4a"
			self.background_color = '#510000'
		elif self.level_music == 7:
			self.background_color = '#144951'
			self.sounder = "Songs/beat boss.m4a"
		elif self.level_music == 11:
			self.background_color = '#0016ff'
			self.sounder = "Songs/the prison battle main.m4a"
		elif self.level_music == 15:
			self.background_color = '#ff0000'
			self.sounder = "Songs/Drum beat.m4a"
		elif self.level_music == 18:
			self.background_color = '#000000'
			self.sounder = "Songs/Rick roll.m4a"
		else:
			self.fun = 1
		if self.fun != 1:
			self.music.stop()
		self.spawn_ball()
		apple = 0
		self.level = randint(0, len(levels) - 1)
		while apple >= len(levels):
			if self.level_loader[apple] == self.level:
				self.level = randint(1, len(levels) - 1)
			else:
				break
		self.level_loader.append(self.level)
		if self.lives_left >= 6 and self.same_level == 0:
			self.same_level = 1
			self.load_special(specials[self.level % 1])
		else:
			self.level_music += 1
			self.same_level = 0
			self.load_level(levels[self.level])
	
	def spawn_ball(self):
		new_ball = Ball(r=self.ball_r, v=(0, -1), position=(self.size.w/2, self.paddle.position.y + 100), parent=self.game_node)
		new_ball.scale = 0
		new_ball.run_action(A.scale_to(1, 0.3))
		new_ball.ball_speed = min(max_ball_speed, min_ball_speed + level_speedup * self.level_music)
		self.balls.append(new_ball)
	
	def destroy_brick(self, ball, brick, with_powerup=True):
		apple = brick.position
		if brick.brick_type == 'p':
			destroy = 1
		elif brick.brick_type == 'd':
			destroy = 1
			self.sp_power = 1
			self.spawn_powerup(ball, brick)
			self.sp_power = 0
		elif brick.brick_type == '!':
			destroy = 1
		else: 
			destroy = 0
		if destroy == 1: 
			self.score += 50
			self.points = 50
			brick.remove_from_parent()
			self.bricks.remove(brick)
			if brick.brick_type == '!':
				self.game_node.add_child(black_hole(apple)) 
			else:
				self.game_node.add_child(Explosion(brick))
			if brick.asher[0] != 1:
				self.score += 10 * (self.level + 1)
			self.score_label.text = str(self.score)
			ball.ball_speed = min(max_ball_speed, ball.ball_speed + brick_speedup)
			if with_powerup and ball.powerup_type == 1 or with_powerup == 1 and ball.powerup_type == 6 or with_powerup == 1 and ball.powerup_type == 7:
				sound.play_effect('digital:Laser3', 0.2)
				for b in list(self.bricks):
					if ball.powerup_type == 6:
						if abs(b.position - ball.position) < brick.size.w * 3:
							self.destroy_brick(ball, b, False)
					elif ball.powerup_type == 1:
						if abs(b.position - ball.position) < brick.size.w * 1.5:
							self.destroy_brick(ball, b, False)
					else:
						if abs(b.position - ball.position) < brick.size.w * 1000:
							self.destroy_brick(ball, b, False)
			spawn_powerup = rnd(0.0, 1.0) <= powerup_chance
			if spawn_powerup:
				self.spawn_powerup(ball, brick)
		else:
			if with_powerup == 1 and ball.powerup_type == 1:
				sound.play_effect('digital:Laser3', 0.2)
			if brick.brick_type == 'x':
				brick.brick_type = '5'
				self.score += 180
				self.points = 180
				self.sp_power = 2
				self.spawn_powerup(ball, brick)
				self.sp_power = 0
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == '5':
				brick.brick_type = '4'
				self.score += 170
				self.points = 170
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == '4':
				brick.brick_type = '3'
				self.score += 160
				self.points = 160
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == '3':
				brick.brick_type = '2'
				self.score += 150
				self.points = 150
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == '2':
				brick.brick_type = '1'
				self.score += 140
				self.points = 140
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == '1':
				brick.brick_type = 'h'
				self.score += 130
				self.points = 130
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'h':
				brick.brick_type = 'c'
				self.score += 120
				self.points = 120
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'c':
				brick.brick_type = 'a'
				self.score += 110
				self.points = 110
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'a':
				brick.brick_type = 'v'
				self.score += 100
				self.points = 100
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'v':
				brick.brick_type = 'q'
				self.score += 90
				self.points = 90
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'q':
				brick.brick_type = 'z'
				self.score += 80
				self.points = 80
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'z':
				brick.brick_type = 'k'
				self.score += 70
				self.points = 70
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'k':
				brick.brick_type = 'm'
				self.score += 60
				self.points = 60
				if ball.powerup_type == 1 or ball.powerup_type == 2:
					ball.powerup_type = 0
			elif brick.brick_type == 'm':
				brick.brick_type = 'r'
				self.score += 50
				self.points = 50
				#if ball.powerup_type == 1 or ball.powerup_type == 2:
				#	ball.powerup_type = 0
			elif brick.brick_type == 'r':
				brick.brick_type = 'y'
				self.score += 40
				self.points = 40
			elif brick.brick_type == 'y':
				brick.brick_type = 'g'
				self.score += 30
				self.points = 30
			elif brick.brick_type == 'g':
				brick.brick_type = 'b'
				self.score += 20
				self.points = 20
			elif brick.brick_type == 'b':
				brick.brick_type = 'p'
				self.score += 10
				self.points = 10
			brick.remove_from_parent()
			asher_copy = brick.asher
			if brick.asher[0] != 1:
				self.score += 10 * (self.level_music + 1)
				self.points += 10 * (self.level_music + 1)
			self.score_label.text = str(self.score)
			self.bricks.remove(brick)
			brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
			brick.size = (self.spw, self.sph)
			brick.asher = asher_copy
			self.bricks.append(brick)
			self.game_node.add_child(Explosion(brick))
			if with_powerup == 1 and ball.powerup_type == 6 or with_powerup == 1 and ball.powerup_type == 1 or with_powerup == 1 and ball.powerup_type == 7:
				sound.play_effect('digital:Laser3')
				for b in list(self.bricks):
					if ball.powerup_type == 6:
						if abs(b.position - ball.position) < brick.size.w * 2.5:
							self.destroy_brick(ball, b, False)
					elif ball.powerup_type == 1:
						if abs(b.position - ball.position) < brick.size.w * 1.5:
							self.destroy_brick(ball, b, False)
					else:
						if abs(b.position - ball.position) < brick.size.w * 1000:
							self.destroy_brick(ball, b, False)
		if brick.asher[0] == 0:
			brick.text = self.points
			self.game_node.add_child(Texter(brick))
			
	def spawn_powerup(self, ball, brick):
		sound.play_effect('digital:PhaserUp5')
		if self.sp_power == 0:
			powerup_type = randint(1, 6)
		else:
			powerup_type = 0
		if powerup_type == 3:
			# Three small extra balls
			for dx in range(-10, 10, 7):
				new_ball = Ball(r=self.ball_r/2, position=brick.position + (dx, 0), parent=self.game_node)
				new_ball.ball_speed = min(max_ball_speed, (min_ball_speed + level_speedup * self.level_music)*1.5)
				self.balls.append(new_ball)
				new_ball.v = Vector2(0, -new_ball.ball_speed/2)
		elif powerup_type == 4:
			# Two small extra balls
			for dx in (-10, 10):
				new_ball = Ball(r=self.ball_r, position=brick.position + (dx, 0), parent=self.game_node)
				new_ball.ball_speed = min(max_ball_speed, min_ball_speed + level_speedup * self.level_music)
				self.balls.append(new_ball)
				new_ball.v = Vector2(0, -new_ball.ball_speed/2)
		elif powerup_type == 5:
			# One large extra ball
			new_ball = Ball(r=self.ball_r*1.5, position=brick.position, parent=self.game_node)
			new_ball.ball_speed = min(max_ball_speed, (min_ball_speed + level_speedup * self.level_music)/2)
			self.balls.append(new_ball)
			new_ball.v = Vector2(0, -new_ball.ball_speed/2)
		else:
			if self.sp_power == 1:
				powerup_type = 7
				self.sp_power = 0
			elif self.sp_power == 2:
				powerup_type = 8
				self.sp_power = 0
			# Blue/red pill/green pill/yellow pill/black bolt
			p = Powerup(powerup_type, v=(0, -ball.ball_speed/2))
			p.position = brick.position
			p.scale = 1.0 if self.size.w > 760 else 0.7
			p.z_position = 2
			self.powerups.append(p)
			self.game_node.add_child(p)
	
	def play_collision_sound(self, collider):
		if isinstance(collider, Brick): 
			sound.play_effect('8ve:8ve-beep-roadblock')
		elif collider == self.paddle:
			if self.paddle_powerup:
				sound.play_effect('digital:Laser2')
			else:
				sound.play_effect('8ve:8ve-beep-shinymetal')
		else:
			sound.play_effect('8ve:8ve-tap-mellow')
		
	def move_paddle(self):
		dx = self.paddle_target - self.paddle.position.x
		if abs(dx) > paddle_speed:
			dx = paddle_speed * cmp(dx, 0)
		self.paddle.position += dx, 0
	
	def touch_began(self, touch):
		x, y = touch.location
		if x < 48 and y > self.size.h - 48:
			self.show_pause_menu()
		else:
			self.paddle_target = x / self.game_node.scale
	
	def touch_moved(self, touch):
		self.paddle_target = touch.location.x / self.game_node.scale
	
	def show_start_menu(self):
		self.paused = True
		self.menu = MenuScene('BrickBreaker', 'Highscore: %i' % self.highscore, ['Play', 'Filter: ' + filter_names[self.filter]])
		self.present_modal_scene(self.menu)
	
	def show_pause_menu(self):
		self.paused = True
		self.menu = MenuScene('Paused', 'Highscore: %i' % self.highscore, ['Continue', 'New Game', 'Filter: ' + filter_names[self.filter]])
		self.present_modal_scene(self.menu)
	
	def menu_button_selected(self, title):
		if title.startswith('Filter:'):
			self.filter = (self.filter + 1) % len(filter_names)
			if self.filter == 0:
				# No filter
				self.effect_node.effects_enabled = False
				self.background_color = '#292e37'
			else:
				# The shader (defined in filters.fsh) decides which filter to use based on this uniform:
				self.effect_node.shader.set_uniform('u_style', self.filter)
				self.effect_node.effects_enabled = True
				if self.filter in (1, 2):
					self.background_color = '#333'
				elif self.filter == 3:
					self.background_color = '#474e3b'
				else:
					self.background_color = '#292e37'
			return 'Filter: ' + filter_names[self.filter]
		elif title in ('Continue', 'New Game', 'Play'):
			self.dismiss_modal_scene()
			self.menu = None
			self.paused = False
			if title in ('New Game', 'Play'):
				self.new_game()

# Run the game:
if __name__ == '__main__':
	run(Game(), PORTRAIT, show_fps=False)
