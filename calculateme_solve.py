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

# compute (and print) the solution
def solution(seq,verbose=True):
	c = int(seq[0])
	print c,
	for button in seq[1:]:
		c1 = button.compute(c)
		if verbose:
			print "[%s] %d" % (str(button),c1),
		c = c1
	if verbose:
		print
	return c

# recursively try every combination of every available button
def solver(state,buttons,path,args):
	# print (and check) the solution if we've found it
	if state == args.goal:
		assert(solution(path,verbose=True) == args.goal)
	# stop searching (and print the failure) if we're out of moves
	elif len(path) > args.moves:
		if args.verbose:
			solution(path,verbose=True)
	# recurse and try the next button(s)
	else:
		for button in buttons:
			nxstate = button.compute(state)
			# ignore non-ops
			if nxstate != state and nxstate not in (False,None):
				solver(nxstate,buttons,path+[button],args)

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
	solver(args.init,buttons,[str(args.init)],args)
