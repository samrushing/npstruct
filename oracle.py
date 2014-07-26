# -*- Mode: Python; tab-width: 4 -*-

# very quickly hacked to verify the C version of npstruct.
# these are the pieces of npstruct.py that aren't implemented
# in npstructmodule.c

import string

from npstruct import pack, unpack

converter = {
	'b':1,
	'c':1,
	'h':2,
	'l':4
	}	

def calcsize (format):
	size = 0
	i = 1
	while i < len(format):
		if format[i] in string.digits:
			num_digits = 0
			while format[i] in string.digits:
				num_digits = num_digits+1
				i = i + 1
				num = string.atoi (format[i-num_digits:i])
			format_code = format[i]
			size = size + converter[format[i]] * num
		elif format[i] == '(':
			end = string.index (format, ')', i)
			bits = reduce (lambda x,y: x+ y,
						   map (string.atoi, string.split (format[i+1:end])))
			if (bits % 8) != 0:
				raise error, 'bitfield not a multiple of 8 bits %s' % (format)
			size = size + bits/8
			i = end
		elif format[i] == '[':
			# this is a variable-sized struct.  should this ignore the
			# variable parts, or return -1 or something? [how about
			# -s, where s is the size of the fixed part?]
			i = string.find (format, ']', i+1)
		else:
			size = size + converter[format[i]]
		i = i + 1
	return size

# ---------------------------------------------------------------------------
# an Oracle can be used to divine the contents of mysterious block
# data, using struct-module-like format strings.  an Oracle can also
# write out its data.
# ---------------------------------------------------------------------------
# here's an example from a gif decoder module:
#
# logical_screen_descriptor = npstruct.Oracle (
# 	'Logical Screen Descriptor',
# 	'Lhh(1 3 1 3)bb',
# 	('width',
# 	 'height',
# 	 'global color table flag',
# 	 'color resolution',
# 	 'sort flag',
# 	 'size of global color table',
# 	 'background color index',
# 	 'pixel aspect ratio'))
# 
# >>> logical_screen_descriptor.unpack (strange_data)
# ({'width':100, 'height':100, 'global color table flag':1 ...}, <size_of_struct>)

# 'functions' values are optionally a tuple of two functions,
# one for unpacking, and one for packing.  Otherwise, this expects
# only a reading function.

def get_functions (function_dict):
	rf = {}
	wf = {}
	for key, value in function_dict.items():
		if type(value) == type(()):
			rf[key] = value[0]
			wf[key] = value[1]
		else:
			rf[key] = value
			wf[key] = None
	return rf, wf

class Oracle:

	def __init__ (self, name, format, names, **functions):
		self.name = name
		self.format = format
		# fixme: need to sanity check len(names) against self.format
		self.names = names
		self.functions = functions
		(self.read_functions, self.write_functions) = get_functions (functions)
		self.size = calcsize (format)

	def __repr__ (self):
		return '<%s oracle>' % self.name

	def new_raw (self):
		return '\000' * self.size

	def new (self):
		return self.unpack (self.new_raw())[0]

	def unpack (self, data, offset=0):
		members, length = unpack (self.format, data, offset, self.read_functions)
		result = {}
		for i in range(len(self.names)):
			result[self.names[i]] = members[i]
		return result, length

	def procfield_function (self, results, data, offset):
		return self.unpack (data, offset)

	def procfield_read (self, results, data, offset):
		return self.unpack (data, offset)

	def procfield_write (self, dict):
		return self.pack (dict)

	def pack (self, dict):
		members = map (lambda x,d=dict: d[x], self.names)
		return pack (self.format, members, self.write_functions)

	def describe (self, dict):
		print '%s:' % self.name
		print '--------------------'
		for key in self.names:
			print '%s: %s' % (key, repr(dict[key]))
