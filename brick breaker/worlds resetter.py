import pickle
level = '''
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
x54321hcavqzkmrgbp!u><^|
'''
with open('game_levels_normal.pkl', 'wb') as f:
	pickle.dump([level], f)
with open('game_levels_normal_names.pkl', 'wb') as f:
	pickle.dump(['first'], f)
with open('game_levels_special.pkl', 'wb') as f:
	pickle.dump([level], f)
with open('game_levels_special_names.pkl', 'wb') as f:
	pickle.dump(['first'], f)
