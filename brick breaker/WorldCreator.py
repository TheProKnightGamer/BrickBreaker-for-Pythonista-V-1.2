# coding: utf-8

from scene import *
import sound
import console
import os
import time
import pickle
import ui
from collections.abc import Sequence
from math import sin, cos, pi, ceil
from random import uniform as rnd, choice, randint
from game_menu import MenuScene
from game_levels import colors, AIR
from colorsys import hsv_to_rgb
import sys
with open('game_levels_normal.pkl', 'rb') as f:
	levels = pickle.load(f)
with open('game_levels_normal_names.pkl', 'rb') as f:
	levels_names = pickle.load(f)
with open('game_levels_special_names.pkl', 'rb') as f:
	specials_names = pickle.load(f)
with open('game_levels_special.pkl', 'rb') as f:
	specials = pickle.load(f)
A = Action
print("copy and paste")		
Scene.background_color = '#ffffff'
def _cmp(a, b):
	return ((a>b)-(a<b))

if sys.version_info[0] >= 3:
	cmp = _cmp

#define brick
class Brick (SpriteNode):
	def __init__(self, brick_type, *args, **kwargs):
		img = colors.get(brick_type, 'iow:alert_circled_256')
		SpriteNode.__init__(self, img, *args, **kwargs)
		self.brick_type = brick_type
		self.asher = ([0,0,0])
		
class _ListDialogController (object):
	def __init__(self, title, items, multiple=False, done_button_title='Done'):
		self.items = items
		self.selected_item = None
		self.view = ui.TableView()
		self.view.name = title
		self.view.allows_multiple_selection = multiple
		if multiple:
			done_button = ui.ButtonItem(title=done_button_title)
			done_button.action = self.done_action
			self.view.right_button_items = [done_button]
		ds = ui.ListDataSource(items)
		ds.action = self.row_selected
		ds.delete_enabled = False
		self.view.data_source = ds
		self.view.delegate = ds
		self.view.frame = (0, 0, 500, 500)
	
	def done_action(self, sender):
		selected = []
		for row in self.view.selected_rows:
			selected.append(self.items[row[1]])
		self.selected_item = selected
		self.view.close()
		
	def row_selected(self, ds):
		if not self.view.allows_multiple_selection:
			self.selected_item = self.items[ds.selected_row]
			self.view.close()
				
# The actual game logic:

class Game (Scene):
	def setup(self):
		self.destroy = 0
		self.check_type = 'null'
		self.specials = specials
		self.specials_names = specials_names
		self.level_import_type = 0
		self.top_bg = SpriteNode(parent=self, size=(self.size.w, 90), position=(self.size.w/2, self.size.y-45))
		brick_w = self.size.w / 24
		brick_h = (self.top_bg.position.y - 45) / 30
		self.spw, self.sph = brick_w, brick_h
		min_x = 0 + brick_w/2
		min_y = 0 + brick_h/2
		self.slicer = self.size.w / 15
		self.c = SpriteNode('iow:arrow_down_b_24', position=(-10, -10), size=(1,1), parent=self)
		self.c.selected_item = 'null'
		self.top_bg.color = '#000000'
		self.type_board = LabelNode('AIR', font=('Avenir Next', self.slicer/5), position=(self.size.w/2, self.size.h-75), parent=self)
		self.button_left = SpriteNode('iow:arrow_left_b_256', position=(self.slicer*6, self.size.h-45), parent=self)
		self.button_left.size = (self.slicer, self.slicer)
		self.button_right = SpriteNode('iow:arrow_right_b_256', position=(self.slicer*9, self.size.h-45), parent=self)
		self.button_right.size = (self.slicer, self.slicer)
		self.number = 0
		self.magic = 0
		self.level_name = 'My level'
		self.level_number = 'null'
		self.levels = levels
		self.draw_undo = []
		self.draw_undo.append(AIR)
		self.level_names = levels_names
		self.setter = ['@','d','p','b','g','r','m', 'k', 'z', 'q', 'v', 'a', 'c', 'h','1', '2', '3', '4', '5', 'x', '!','u', '+', '-', '*', '/']
		self.words = ['AIR','lives: 1, type: power: yellow','lives: 1', 'lives: 2', 'lives: 3', 'lives: 4', 'lives: 5', 'lives: 6', 'lives: 7', 'lives: 8', 'lives: 9', 'lives: 10', 'lives: 11', 'lives: 12', 'lives: 13', 'lives: 14', 'lives: 15', 'lives: 16', 'lives: 17', 'lives: 18 type: power: lightning', 'lives: 1, type: eat','type: invincible', 'type: invincible, moves: right', 'type: invincible, moves: left', 'type: invincible, moves: up', 'type: invincible, moves: down']
		self.brick_setter = SpriteNode(colors.get('@', 'pzl:Red8'), size=(self.spw, self.sph), position=(self.size.w/2, self.size.h-40), parent=self)
		self.upload = SpriteNode('typw:Export', size=(self.slicer, self.slicer), position=(self.slicer*2, self.size.h-45), parent=self)
		self.filler= SpriteNode('iow:flask_256', size=(self.slicer/1.2, self.slicer/1.2), position=(self.slicer*13, self.size.h-45), parent=self)
		self.download = SpriteNode('typw:Archive', size=(self.slicer, self.slicer), position=(self.slicer, self.size.h-45), parent=self)
		self.level_name_text = LabelNode(self.level_name, font=('Avenir Next', self.slicer/6), position=(self.slicer*14, self.size.h-45), parent=self)
		self.Randomizer = SpriteNode('typw:Shuffle', size=(self.slicer, self.slicer), position=(self.slicer*12, self.size.h-45), parent=self)
		self.erase = SpriteNode('typw:Trash', size=(self.slicer, self.slicer), position=(self.slicer*11, self.size.h-45), parent=self)
		self.deleate = SpriteNode('typw:Delete', size=(self.slicer, self.slicer), position=(self.slicer*3, self.size.h-45), parent=self)
		self.ResetBrush = SpriteNode('typw:Refresh', size=(self.slicer, self.slicer), position=(self.slicer*10, self.size.h-45), parent=self)
		self.Names1 = LabelNode('| Import |', font=('Avenir Next', self.slicer/4), position=(self.slicer, self.size.h-80), parent=self)
		self.Names2 = LabelNode('| Export |', font=('Avenir Next', self.slicer/4), position=(self.slicer*2, self.size.h-80), parent=self)
		self.Names3 = LabelNode('| Delete |', font=('Avenir Next', self.slicer/4), position=(self.slicer*3, self.size.h-80), parent=self)
		self.Names4 = LabelNode('| Trash  |', font=('Avenir Next', self.slicer/4), position=(self.slicer*11, self.size.h-80), parent=self)
		self.Names5 = LabelNode('| Shuffle|', font=('Avenir Next', self.slicer/4), position=(self.slicer*12, self.size.h-80), parent=self)
		self.Names6 = LabelNode('|  Fill  |', font=('Avenir Next', self.slicer/4), position=(self.slicer*13, self.size.h-80), parent=self)
		self.Names7 = LabelNode('|ResetPen|', font=('Avenir Next', self.slicer/4), position=(self.slicer*10, self.size.h-80), parent=self)
		self.location = (0, 0)
		self.bricks	= []
		self.effect_node = EffectNode(parent=self)
		self.game_node = Node(parent=self.effect_node)
		self.level = AIR
		self.load_level(AIR)
		paddle_y = 120 if self.size.w > 760 else 70
		self.paddle = SpriteNode('pzl:Particle2', position=(0, 0), parent=self.game_node)
		self.paddle.size = (.1, .1)
		
	def list_dialog(self, title='', items=None, multiple=False, done_button_title='Done'):
		if not items:
			items = []
		if not isinstance(title, basestring):
			raise TypeError('title must be a string')
		if not isinstance(items, Sequence):
			raise TypeError('items must be a sequence')
		self.c = _ListDialogController(title, items, multiple, done_button_title=done_button_title)
		self.c.view.present('sheet')
		self.c.view.wait_modal()
			
	def Error_system(self, Error):
		console.set_color(1,0,0)
		if Error == 0:
			print('Error0: No level created')
			console.hud_alert('Error0: No level created', 'error', 2)
		elif Error == 1:
			print('Error1: Name already exists')
			console.hud_alert('Error1: Name already exists', 'error', 2)
		console.set_color(1,1,1)
		
	def Success(self, Success):
		console.set_color(0,1,0)
		if Success == 0:
			print('Level exported')
			console.hud_alert('Level exported', 'success', 2)
		if Success == 1:
			print('Level deleted')
			console.hud_alert('Level deleted', 'success', 2)
		
	def text_field_action(self, sender):
		# Handling the text field data
		self.level_name = sender.text
		self.form.close()
		self.refresh()
		apple = 0
		file = []
		loader = []
		extra = 0
		while len(self.bricks) >= apple + 1:
			if self.bricks[apple].brick_type == '@':
				loader.append(' ')
			elif self.bricks[apple].brick_type == '+':
				loader.append('>')
			elif self.bricks[apple].brick_type == '-':
				loader.append('<')
			elif self.bricks[apple].brick_type == '*':
				loader.append('^')
			elif self.bricks[apple].brick_type == '/':
				loader.append('|')
			else:
				loader.append(self.bricks[apple].brick_type)
				extra = 2
			apple += 1
		apple = 0
		while len(self.bricks) >= apple + 1:
			file.append(loader[apple])
			apple += 1
		#27
		tempList=[]
		for i in range(31):
			tempList.append(''.join(file[i*24:(i*24)+24]))
		apple = 30
		reverser = []
		while apple >= 0:
			reverser.append(tempList[apple])
			apple -= 1
		self.level_name = self.text_field.text
		self.level = '\n'.join(reverser)
		apple = 1
		del i	
		templistname = list(self.level_name)
		for i in range(len(self.level_names)):
			if self.level_name == self.level_names[i]:
				extra = 1
		if extra == 0:
			self.Error_system(0)
		elif extra == 1:
			if self.level_number == 'null':
				self.Error_system(1)
			else:
				self.levels.pop(self.level_number)
				self.level_names.pop(self.level_number)
				self.levels.insert(0, self.level)
				self.level_names.insert(0, self.level_name)
				print(self.level_name)
				print("'''")
				print(self.level)
				print("'''")
				self.Success(0)
		elif self.level_number == 'null':
			self.levels.insert(0, self.level)
			self.level_names.insert(0, self.level_name)
			print(self.level_name)
			print("'''")
			print(self.level)
			print("'''")
			self.level_number = 0
			self.Success(0)
		else:
			self.levels.pop(self.level_number)
			self.level_names.pop(self.level_number)
			self.levels.insert(0, self.level)
			self.level_names.insert(0, self.level_name)
			print(self.level_name)
			print("'''")
			print(self.level)
			print("'''")
			self.Success(0)
		with open('game_levels_normal.pkl', 'wb') as f:
			pickle.dump(self.levels, f)
		with open('game_levels_normal_names.pkl', 'wb') as f:
			pickle.dump(self.level_names, f)
		
	def make_form(self):
		# Create the UI form with an input text field.
		self.form = ui.View()
		self.form.name = 'Enter level name:'
		self.form.background_color = 'white'
		self.form.width = 300
		self.form.height = 100
		self.text_field = ui.TextField()
		self.text_field.action = self.text_field_action
		self.text_field.placeholder = 'Level name'
		self.text_field.width = 300
		self.text_field.height = 50
		self.text_field.center = (self.form.width*.5, self.form.height*.5)
		self.text_field.text = self.level_name
		self.text_field.flex = 'LRTB'
		self.form.add_subview(self.text_field)
		return self.form
		
	def text_field_action_special(self, sender):
		# Handling the text field data
		self.level_name = sender.text
		self.form.close()
		self.refresh()
		apple = 0
		file = []
		loader = []
		extra = 0
		while len(self.bricks) >= apple + 1:
			if self.bricks[apple].brick_type == '@':
				loader.append(' ')
			elif self.bricks[apple].brick_type == '+':
				loader.append('>')
			elif self.bricks[apple].brick_type == '-':
				loader.append('<')
			elif self.bricks[apple].brick_type == '*':
				loader.append('^')
			elif self.bricks[apple].brick_type == '/':
				loader.append('|')
			else:
				loader.append(self.bricks[apple].brick_type)
				extra = 2
			apple += 1
		apple = 0
		while len(self.bricks) >= apple + 1:
			file.append(loader[apple])
			apple += 1
		#27
		tempList=[]
		for i in range(31):
			tempList.append(''.join(file[i*24:(i*24)+24]))
		apple = 30
		reverser = []
		while apple >= 0:
			reverser.append(tempList[apple])
			apple -= 1
		self.level_name = self.text_field.text
		self.level = '\n'.join(reverser)
		apple = 1
		del i	
		templistname = list(self.specials)
		for i in range(len(self.specials_names)):
			if self.level_name == self.specials_names[i]:
				extra = 1
		if extra == 0:
			self.Error_system(0)
		elif extra == 1:
			if self.level_number == 'null':
				self.Error_system(1)
			else:
				self.specials.pop(self.level_number)
				self.specials_names.pop(self.level_number)
				self.specials.insert(0, self.level)
				self.specials_names.insert(0, self.level_name)
				print(self.level_name)
				print("'''")
				print(self.level)
				print("'''")
				self.Success(0)
		elif self.level_number == 'null':
			self.specials.insert(0, self.level)
			self.specials_names.insert(0, self.level_name)
			print(self.level_name)
			print("'''")
			print(self.level)
			print("'''")
			self.level_number = 0
			self.Success(0)
		else:
			self.specials.pop(self.level_number)
			self.specials_names.pop(self.level_number)
			self.specials.insert(0, self.level)
			self.specials_names.insert(0, self.level_name)
			print(self.level_name)
			print("'''")
			print(self.level)
			print("'''")
			self.Success(0)
		with open('game_levels_special.pkl', 'wb') as f:
			pickle.dump(self.specials, f)
		with open('game_levels_special_names.pkl', 'wb') as f:
			pickle.dump(self.specials_names, f)
		
	def make_form_special(self):
		# Create the UI form with an input text field.
		self.form = ui.View()
		self.form.name = 'Enter level name:'
		self.form.background_color = 'white'
		self.form.width = 300
		self.form.height = 100
		self.text_field = ui.TextField()
		self.text_field.action = self.text_field_action_special
		self.text_field.placeholder = 'Level name'
		self.text_field.width = 300
		self.text_field.height = 50
		self.text_field.center = (self.form.width*.5, self.form.height*.5)
		self.text_field.text = self.level_name
		self.text_field.flex = 'LRTB'
		self.form.add_subview(self.text_field)
		return self.form
		
	def fill_air(self):
		apple = 0
		while len(self.bricks) >= apple + 1:
			if self.bricks[apple].brick_type == '@':
				self.bricks[apple].brick_type = self.setter[self.number]
				brick = self.bricks[apple]
				brick.brick_type = self.setter[self.number]
				brick = self.bricks[apple]
				brick.remove_from_parent()
				self.bricks[apple] = 0
				brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
				brick.size = (self.spw, self.sph)
				self.bricks[apple] = brick
			apple += 1

	def load_level(self, level):
		lines = level.splitlines() 
		brick_w = self.size.w / 24
		brick_h = (self.top_bg.position.y - 45) / 30
		self.spw, self.sph = brick_w, brick_h
		min_x = 0 + brick_w/2
		min_y = 0 + brick_h/2
		for y, line in enumerate(reversed(lines)):
			for x, char in enumerate(line):
				if char == ' ':
					char = '@'
				pos = Point(x * self.spw + min_x, min_y + y * self.sph)
				brick = Brick(char, position=pos, parent=self.game_node)
				brick.size = (self.spw, self.sph)
				self.bricks.append(brick)
		for i, b in enumerate(self.bricks):
			b.scale = 0
			b.run_action(A.sequence(A.wait(i*0.001), A.scale_to(1, 0.25, 4)))
		self.level_start_time = self.t
		self.ball = SpriteNode('iob:ios7_circle_filled_256', size=(30, 30), position=(self.size.w/2, 120.00), parent=self)
		self.ball.alpha = 0.4
	
	def update_draw(self):
		apple = 0
		while len(self.bricks) >= apple + 1:
			frame = self.paddle.frame
			frame = frame.inset(0, 0, 1, 1)
			rect = frame
			brick = self.bricks[apple]
			if self.paddle.bbox and rect.intersects(brick.bbox):
				brick.brick_type = self.setter[self.number]
				brick = self.bricks[apple]
				brick.remove_from_parent()
				self.bricks[apple] = 0
				brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
				brick.size = (self.spw, self.sph)
				self.bricks[apple] = brick
			apple += 1
			
	def sleep(self):
		time.sleep(.1)

	def download_world(self):
		worlds_file = []
		for i in range(len(self.levels)):
			word = str(i)
			word = list(word)
			word.append(': ')
			word.append(self.level_names[i])
			if i == 0:
				word.append(' <<<Latest world')
			elif i == len(self.levels) - 1:
				word.append(' <<<Oldest world')
			word = ''.join(word)
			worlds_file.append(word)
		self.level_import_type = 1
		(self.list_dialog('Choose a level', worlds_file))
		
	def download_world_special(self):
		worlds_file = []
		for i in range(len(self.specials)):
			word = str(i)
			word = list(word)
			word.append(': ')
			word.append(self.specials_names[i])
			if i == 0:
				word.append(' <<<Latest world')
			elif i == len(self.levels) - 1:
				word.append(' <<<Oldest world')
			word = ''.join(word)
			worlds_file.append(word)
		self.level_import_type = 2
		(self.list_dialog('Choose a level', worlds_file))
		
	def finalize(self, ok):
		word = "1234567890"
		ls = []
		for i in range(len(ok)):
			if ok[i] in word:
				ls.append(ok[i])
			else:
				break
		cat = ''.join(ls)
		cat = int(cat)
		world = self.levels[cat]
		lister = []
		cap = world.splitlines()
		for i in range(30):
			b = cap[i]
			b = list(b)
			if len(b) <= 5:
				continue
			for k in range(24):
				lister.append(b[k])
		cap = lister
		for i in range(len(cap)):
			ca = cap[i]
			if ca == " ":
				ca = "@"
			elif ca == ">":
				ca = "+"
			elif ca == "<":
				ca = "-"
			elif ca == "^":
				ca = "*"
			elif ca == "|":
				ca = "/"
			cap[i] = ca
		tempList=[]
		for i in range(31): 
			tempList.append(''.join(cap[i*24:(i*24)+24]))
		world = '\n'.join(tempList)
		apple = len(self.bricks) - 1
		for i in range(len(self.bricks)):
			self.bricks[apple - i].remove_from_parent()
			del self.bricks[apple - i]
		self.load_level(world)
		self.level_name = self.level_names[cat]
		self.level_number = cat
		self.refresh()
		
	def finalize_specials(self, ok):
		word = "1234567890"
		ls = []
		for i in range(len(ok)):
			if ok[i] in word:
				ls.append(ok[i])
			else:
				break
		cat = ''.join(ls)
		cat = int(cat)
		world = self.specials[cat]
		lister = []
		cap = world.splitlines()
		for i in range(31):
			b = cap[i]
			if len(b) <= 5:
				continue
			for k in range(24):
				b = list(b)
				lister.append(b[k])
		cap = lister
		for i in range(len(cap)):
			ca = cap[i]
			if ca == " ":
				ca = "@"
			elif ca == ">":
				ca = "+"
			elif ca == "<":
				ca = "-"
			elif ca == "^":
				ca = "*"
			elif ca == "|":
				ca = "/"
			cap[i] = ca
		tempList=[]
		for i in range(31): 
			tempList.append(''.join(cap[i*24:(i*24)+24]))
		world = '\n'.join(tempList)
		apple = len(self.bricks) - 1
		for i in range(len(self.bricks)):
			self.bricks[apple - i].remove_from_parent()
			del self.bricks[apple - i]
		self.load_level(world)
		self.level_name = self.specials_names[cat]
		self.level_number = cat
		self.refresh()
		
	def garbage_special(self):
		worlds_file = []
		for i in range(len(self.specials)):
			word = str(i)
			word = list(word)
			word.append(': ')
			word.append(self.specials_names[i])
			if i == 0:
				word.append(' <<<Latest world')
			elif i == len(self.levels) - 1:
				word.append(' <<<Oldest world')
			word = ''.join(word)
			worlds_file.append(word)
		self.destroy = 2
		(self.list_dialog('Choose a level', worlds_file))
		
	def garbage(self):
		worlds_file = []
		for i in range(len(self.levels)):
			word = str(i)
			word = list(word)
			word.append(': ')
			word.append(self.level_names[i])
			if i == 0:
				word.append(' <<<Latest world')
			elif i == len(self.levels) - 1:
				word.append(' <<<Oldest world')
			word = ''.join(word)
			worlds_file.append(word)
		self.destroy = 1
		(self.list_dialog('Choose a level', worlds_file))
		
	def Special_action(self, sender):
		if self.check_type == 1:
			self.export_special()
		elif self.check_type == 2:
			self.download_world_special()
		elif self.check_type == 3:
			self.garbage_special()
		
	def Normal_action(self, sender):
		if self.check_type == 1:
			self.export()
		elif self.check_type == 2:
			self.download_world()
		elif self.check_type == 3:
			self.garbage()
			
	def Handler(self):	
		# create main view
		main_view = ui.View(frame=(0, 0, 300, 300))
		main_view.border_color = '#ffffff'
		main_view.background_color = '#ffffff'
		# create Yes button and assign action
		Sbutton = ui.Button(title='Special_level') 
		Sbutton.action = self.Special_action
		Sbutton.frame = (10, 10, 280, 50)
		Sbutton.tint_color = '#000000'
		
		# create No button and assign action
		Nbutton = ui.Button(title='Normal_level')
		Nbutton.action = self.Normal_action
		Nbutton.frame = (10, 70, 280, 50)
		Nbutton.tint_color = '#000000'
		
		# add buttons to main view
		main_view.add_subview(Sbutton)
		main_view.add_subview(Nbutton)
		
		# present the view
		main_view.present('sheet')
		
	def final_destroy(self, k):
		word = "1234567890"
		ls = []
		for i in range(len(k)):
			if k[i] in word:
				ls.append(k[i])
			else:
				break
		k = ls
		k = ''.join(k)
		k = int(k)
		self.levels.pop(k)
		self.level_names.pop(k)
		with open("game_levels_normal_names.pkl", "wb") as f:
			pickle.dump(self.level_names, f)
		with open("game_levels_normal.pkl", "wb") as f:
			pickle.dump(self.levels, f)
		self.Success(1)
		
	def final_destroy_s(self, k):
		word = "1234567890"
		ls = []
		for i in range(len(k)):
			if k[i] in word:
				ls.append(k[i])
			else:
				break
		k = ls
		k = ''.join(k)
		k = int(k)
		self.specials.pop(k)
		self.specials_names.pop(k)
		with open("game_levels_special_names.pkl", "wb") as f:
			pickle.dump(self.specials_names, f)
		with open("game_levels_special.pkl", "wb") as f:
			pickle.dump(self.specials, f)
		self.Success(1)

	def update(self):	
		self.paddle.position = (self.location)
		self.update_draw()
		if self.c.selected_item is None:
			return 
		elif self.c.selected_item == "null":
			return 
		k = list(self.c.selected_item)
		self.c.selected_item = 'null'
		word = "1234567890"
		if self.level_import_type == 1:
			if k[0] in word:
				self.finalize(k)
		elif self.level_import_type == 2:
			if k[0] in word:
				self.finalize_specials(k)
		elif self.destroy == 1:
			if k[0] in word:
				self.final_destroy(k)
		elif self.destroy == 2:
			if k[0] in word:
				self.final_destroy_s(k)
		self.destroy = 0
		self.level_import_type = 0
		
	def refresh(self):
		self.top_bg = SpriteNode(parent=self, size=(self.size.w, 90), position=(self.size.w/2, self.size.y-45))
		self.top_bg.color = '#000000'
		self.type_board = LabelNode(self.words[self.number], font=('Avenir Next', self.slicer/5), position=(self.size.w/2, self.size.h-75), parent=self)
		self.button_left = SpriteNode('iow:arrow_left_b_256', position=(self.slicer*6, self.size.h-45), parent=self)
		self.button_left.size = (self.slicer, self.slicer)
		self.button_right = SpriteNode('iow:arrow_right_b_256', position=(self.slicer*9, self.size.h-45), parent=self)
		self.button_right.size = (self.slicer, self.slicer)
		self.brick_setter = SpriteNode(colors.get(self.setter[self.number], 'pzl:Red8'), size=(self.spw, self.sph), position=(self.size.w/2, self.size.h-40), parent=self)
		self.upload = SpriteNode('typw:Export', size=(self.slicer, self.slicer), position=(self.slicer*2, self.size.h-45), parent=self)
		self.filler= SpriteNode('iow:flask_256', size=(self.slicer/1.2, self.slicer/1.2), position=(self.slicer*13, self.size.h-45), parent=self)
		self.download = SpriteNode('typw:Archive', size=(self.slicer, self.slicer), position=(self.slicer, self.size.h-45), parent=self)
		self.level_name_text = LabelNode(self.level_name, font=('Avenir Next', self.slicer/6), position=(self.slicer*14, self.size.h-45), parent=self)
		self.Randomizer = SpriteNode('typw:Shuffle', size=(self.slicer, self.slicer), position=(self.slicer*12, self.size.h-45), parent=self)
		self.erase = SpriteNode('typw:Trash', size=(self.slicer, self.slicer), position=(self.slicer*11, self.size.h-45), parent=self)
		self.deleate = SpriteNode('typw:Delete', size=(self.slicer, self.slicer), position=(self.slicer*3, self.size.h-45), parent=self)
		self.ResetBrush = SpriteNode('typw:Refresh', size=(self.slicer, self.slicer), position=(self.slicer*10, self.size.h-45), parent=self)
		self.Names1 = LabelNode('| Import |', font=('Avenir Next', self.slicer/4), position=(self.slicer, self.size.h-80), parent=self)
		self.Names2 = LabelNode('| Export |', font=('Avenir Next', self.slicer/4), position=(self.slicer*2, self.size.h-80), parent=self)
		self.Names3 = LabelNode('| Delete |', font=('Avenir Next', self.slicer/4), position=(self.slicer*3, self.size.h-80), parent=self)
		self.Names4 = LabelNode('| Trash  |', font=('Avenir Next', self.slicer/4), position=(self.slicer*11, self.size.h-80), parent=self)
		self.Names5 = LabelNode('| Shuffle|', font=('Avenir Next', self.slicer/4), position=(self.slicer*12, self.size.h-80), parent=self)
		self.Names6 = LabelNode('|  Fill  |', font=('Avenir Next', self.slicer/4), position=(self.slicer*13, self.size.h-80), parent=self)
		self.Names7 = LabelNode('|ResetPen|', font=('Avenir Next', self.slicer/4), position=(self.slicer*10, self.size.h-80), parent=self)

		
	def change_color_type_right(self):
		self.number += 1
		if self.number >= len(self.setter):
			self.number = 0
		self.refresh()
		
	def change_color_type_left(self):
		self.number -= 1
		if self.number <= -1:
			self.number = len(self.setter) - 1
		self.refresh()
		
	def randomize(self):
		for i in range(len(self.bricks)):
			k = randint(0, len(self.setter) - 1)
			self.bricks[i].brick_type = self.setter[k]
			brick = self.bricks[i]
			brick.remove_from_parent()
			self.bricks[i] = 0
			brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
			brick.size = (self.spw, self.sph)
			self.bricks[i] = brick
		
	def trash(self):
		apple = 0
		while len(self.bricks) >= apple + 1:
			self.bricks[apple].brick_type = '@'
			brick = self.bricks[apple]
			brick.brick_type = '@'
			brick.remove_from_parent()
			self.bricks[apple] = 0
			brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
			brick.size = (self.spw, self.sph)
			self.bricks[apple] = brick
			apple += 1
		self.level_number = 'null'
		self.level_name = 'My level'
		self.level_name_text.text = 'My level'
		
	def eraser(self):
		apple = 0
		while len(self.bricks) >= apple + 1:
			if self.bricks[apple].brick_type == self.setter[self.number]:
				self.bricks[apple].brick_type = '@'
				brick = self.bricks[apple]
				brick.brick_type = '@'
				brick.remove_from_parent()
				self.bricks[apple] = 0
				brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
				brick.size = (self.spw, self.sph)
				self.bricks[apple] = brick
			apple += 1
			
	def Undo(self):
		apple = 0
		num = len(self.draw_undo) - 1
		lev = self.draw_undo[num]
		lev = list(lev)
		print(lev)
		while len(self.bricks) >= apple + 1:
			if lev[apple] == '\n':
				lev.pop(apple)
				continue
			self.bricks[apple].brick_type = lev[apple]
			brick = self.bricks[apple]
			brick.remove_from_parent()
			brick.brick_type = lev[apple]
			self.bricks[apple] = 0
			brick = Brick(brick.brick_type, brick.position, parent=self.game_node)
			brick.size = (self.spw, self.sph)
			self.bricks[apple] = brick
			apple += 1
		if len(self.draw_undo) >= 2:
			self.draw_undo.pop(0) 
		
	def touch_began(self, touch):
		x = touch.location.x
		y = touch.location.y
		self.location = x, y
		if x <= self.button_right.position.x + self.slicer/2 and x >= self.button_right.position.x - self.slicer/2:
			if y <= self.button_right.position.y + self.slicer/2 and y >= self.button_right.position.y - self.slicer/2:
				self.change_color_type_right()
		elif x <= self.button_left.position.x + self.slicer/2 and x >= self.button_left.position.x - self.slicer/2:
			if y <= self.button_left.position.y + self.slicer/2 and y >= self.button_left.position.y - self.slicer/2:
				self.change_color_type_left()
		elif x <= self.upload.position.x + self.slicer/2 and x >= self.upload.position.x - self.slicer/2:
			if y <= self.upload.position.y + self.slicer/2 and y >= self.upload.position.y - self.slicer/2:
				self.check_type = 1
				self.Handler()
		elif x <= self.filler.position.x + self.slicer/2 and x >= self.filler.position.x - self.slicer/2:
			if y <= self.filler.position.y + self.slicer/2 and y >= self.filler.position.y - self.slicer/2:
				self.fill_air()
		elif x <= self.download.position.x + self.slicer/2 and x >= self.download.position.x - self.slicer/2:
			if y <= self.download.position.y + self.slicer/2 and y >= self.download.position.y - self.slicer/2:
				self.check_type = 2
				self.Handler()
		elif x <= self.deleate.position.x + self.slicer/2 and x >= self.deleate.position.x - self.slicer/2:
			if y <= self.deleate.position.y + self.slicer/2 and y >= self.deleate.position.y - self.slicer/2:
				self.check_type = 3
				self.Handler()
		elif x <= self.Randomizer.position.x + self.slicer/2 and x >= self.Randomizer.position.x - self.slicer/2:
			if y <= self.Randomizer.position.y + self.slicer/2 and y >= self.Randomizer.position.y - self.slicer/2:
				self.randomize()
		elif x <= self.erase.position.x + self.slicer/2 and x >= self.erase.position.x - self.slicer/2:
			if y <= self.erase.position.y + self.slicer/2 and y >= self.erase.position.y - self.slicer/2:
				self.trash()
		elif x <= self.ResetBrush.position.x + self.slicer/2 and x >= self.ResetBrush.position.x - self.slicer/2:
			if y <= self.ResetBrush.position.y + self.slicer/2 and y >= self.ResetBrush.position.y - self.slicer/2:
				self.number = 0
				self.refresh()	
	
	def export(self):
		v = self.make_form()
		v.present('sheet')
		
	def export_special(self):
		v = self.make_form_special()
		v.present('sheet')
			
	def touch_moved(self, touch):
		self.location = touch.location / self.game_node.scale
	

# Run the game:
if __name__ == '__main__':
	run(Game(), PORTRAIT, show_fps=False)
