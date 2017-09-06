import string
import argparse
import sys

class Button:
	def __init__(self, label):
		self.label = label
	def __str__(self):
		return self.label
	def compute(self,input):
		if self.label == '<<':
			return int(input)/10
		elif self.label[0] in string.digits:
			return int(str(input)+self.label)
		elif self.label[0] == '+':
			return int(input)+int(self.label[1:])
		elif self.label[0] == '-':
			return int(input)-int(self.label[1:])
		elif self.label[0] in 'x*':
			return int(input)*int(self.label[1:])
		elif self.label[0] == '/':
			return int(input)/int(self.label[1:])
		else:
			raise ValueError( 'Unknown button "%s"' % (iv) )

def verify(seq,goal):
	c = int(seq[0])
	for button in seq[1:]:
		c1 = button.compute(c)
		print c,str(button),'=',c1
		c = c1
	print
	assert(c == goal)

def solver(state,goal,buttons,maxdepth,path):
	rv = []
	if maxdepth<0:
		return False
	if state == goal:
		verify(path,goal)
	for button in buttons:
		nxstate = button.compute(state)
		# ignore non-ops
		if nxstate != state:
			solver(nxstate,goal,buttons,maxdepth-1,path+[button])

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Solver for "Calculator: The Game" by Simple Machine.',
		epilog="EXAMPLE: %s --init 0 --goal 21 --moves 5 --buttons +5 x3 x5 '<<'" % (sys.argv[1]))
	parser.add_argument('-i', '--init', dest='init', type=int, help='init val', required=True)
	parser.add_argument('-g', '--goal', dest='goal', type=int, help='goal', required=True)
	parser.add_argument('-m', '--moves', dest='moves', type=int, help='moves', required=True)
	parser.add_argument('-b', '--buttons', dest='buttons', type=str, help='buttons', nargs='+', required=True)

	args = parser.parse_args()
	buttons = map(Button,args.buttons)
	solver(args.init,args.goal,buttons,args.moves,[str(args.init)])
