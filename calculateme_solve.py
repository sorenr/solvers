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
		elif self.label in ('+/-','-/+'):
			return -1*int(input)
		elif '=>' in self.label:
			a,b = self.label.split('=>')
			return int(str(input).replace(a,b))
		elif self.label == 'reverse':
			ainput = abs(int(input))
			arev = str(ainput)[::-1]
			return  int(arev) * (int(input)<0 and -1 or 1)
		elif self.label[0] in string.digits:
			return int(str(input)+self.label)
		elif self.label[0] == '+':
			return int(input)+int(self.label[1:])
		elif self.label[0] == '-':
			return int(input)-int(self.label[1:])
		elif self.label[0] in 'x*':
			return int(input)*int(self.label[1:])
		elif self.label[0] == '/':
			if int(input) % int(self.label[1:]) != 0:
				return False
			else:
				return int(input)/int(self.label[1:])
		else:
			raise ValueError( 'Unknown button "%s"' % (iv) )

def printsol(state,path):
	# print the initial state
	print state[0],
	for press,nxstate in zip(path,state[1:]):
		print "[%s] %d" % (str(press),nxstate),
	print "(%d)" % (len(path))

# recursively try every combination of every available button
def solver(state,buttons,path,args):
	# recurse and try the next button(s)
	if len(path)<args.moves and state[-1] != args.goal:
		for button in buttons:
			nxstate = button.compute(state[-1])
			# ignore non-ops and loops
			if nxstate not in (False,None) and nxstate not in state:
				solver(state+[nxstate],buttons,path+[str(button)],args)
	# print the solution if we've found it
	elif state[-1] == args.goal or args.verbose:
		printsol(state,path)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Solver for "Calculator: The Game" by Simple Machine.',
		epilog="EXAMPLE: %s --init 0 --goal 21 --moves 5 --buttons +5 x3 x5 '<<'" % (sys.argv[0]))
	parser.add_argument('-i', '--init', dest='init', type=int, help='init val', required=True)
	parser.add_argument('-g', '--goal', dest='goal', type=int, help='goal', required=True)
	parser.add_argument('-m', '--moves', dest='moves', type=int, help='moves', required=True)
	parser.add_argument('-b', '--buttons', dest='buttons', type=str, help='buttons', nargs='+', required=True)
	parser.add_argument('-v', '--verbose', dest='verbose', action="store_true")

	args = parser.parse_args()
	buttons = map(Button,args.buttons)
	solver([int(args.init)],buttons,[],args)
