# -*- Mode: Python; tab-width: 4 -*-

error = 'npstruct module error'

# A version of pack/unpack that doesn't pad.
# Useful for portable binary data, like images, network packets,
# sound files, etc...

# Enhancements compared to the struct module:
# 1) Allows specification of byte order - the format string
#    starts with 'B' or 'L'.
# 2) Bitfields - designated by a series of numbers in parens,
#    like so: 'B(1 1 4 2)'
# 3) 'Procfields' - fields that crack open with user-specified
#    functions.  Useful for variable-length fields, and higher-level
#    parsing.

# Missing features compared to the struct module:
# 1) well, no way to specify any alignment.
# 2) no pad char ('x')
# 3) no floats or doubles.

# FIXME: Might want to make the byte-order specifier optional, and
#   then use a guessed value.
#
# TODO: recode in C.

def little_encode_word (x):
	return chr(int(x&0xff)) + chr(int(x>>8&0xff))

def little_decode_word (data):
	return ord(data[1])<<8 | ord(data[0])

def little_encode_long (x):
	return chr(int(x&0xff))+chr(int(x>>8&0xff))+ \
		   chr(int(x>>16&0xff))+chr(int(x>>24&0xff))

def little_decode_long (data):
	return ord(data[3])<<24 | ord(data[2])<<16 | \
		   ord(data[1])<<8  | ord(data[0])

def big_encode_word (x):
	return  chr(int(x>>8&0xff)) + chr(int(x&0xff))

def big_decode_word (data):
	return ord(data[0])<<8 | ord(data[1])

def big_encode_long (x):
	return chr(int(x>>24&0xff))+chr(int(x>>16&0xff))+ \
		   chr(int(x>>8&0xff))+chr(int(x&0xff))

def big_decode_long (data):
	return ord(data[0])<<24 | ord(data[1])<<16 | \
		   ord(data[2])<<8  | ord(data[3])

import string

def pack (format, args, funs={}):
	if format[0] == 'L':
		encode_word = little_encode_word
		encode_long = little_encode_long
	elif format[0] == 'B':
		encode_word = big_encode_word
		encode_long = big_encode_long
	else:
		raise error, 'unsupported byte order code'
	result = ''
	i = 1
	argnum = 0
	while i < len(format):
		ch = format[i]
		if ch == 'h':
			result = result + encode_word (args[argnum])
		elif ch == 'l':
			result = result + encode_long (args[argnum])
		elif ch == 'b':
			result = result + chr(args[argnum])
		elif ch == 'c':
			result = result + args[argnum]
		elif ch in string.digits:
			num_digits = 0
			while format[i] in string.digits:
				num_digits = num_digits + 1
				i = i + 1
			num = string.atoi(format[i-num_digits:i])
			format_code = format[i]
			sub_result = pack(format[0] + format_code * num, args[argnum])
			result = result + sub_result
		elif ch == '[':
			# procfield
			procname_end = string.find (format, ']', i+1)
			if procname_end == -1:
				raise error, 'no closing bracket for procedure name'
			else:
				procname = format[i+1:procname_end]
			if funs.has_key(procname):
				fun = funs[procname]
				sub_result  = apply (fun, (args[argnum],))
				result = result + sub_result
			else:
				raise error, 'procfield function "%s" missing!' % procname
			i = procname_end
		elif ch == '(':
			# bitfield
			bit_lengths = []
			while 1:
				if format[i] == ')':
					break
				else:
					i = i + 1
				num_digits = 0
				while format[i] in string.digits:
					num_digits = num_digits + 1
					i = i + 1
				num = string.atoi (format[i-num_digits:i])
				bit_lengths.append (num)
			total_bits = reduce (lambda x,y: x + y, bit_lengths)
			if (total_bits % 8) != 0:
				raise error, 'bitfield not a multiple of 8 bits %s' % (format)
			bitfield_size = total_bits / 8
			sub_result = pack_bitfield (
					bit_lengths,
					#args[argnum]
					args[argnum:argnum+len(bit_lengths)]
					)
			#print args, argnum, argnum+len(bit_lengths)
			argnum = argnum + (len(bit_lengths)-1)
			result = result + sub_result
		else:
			raise error, 'unsupported format character "%s"' % ch
		i = i + 1
		argnum = argnum + 1
	return result

converter = {'b':1,
			 'c':1,
			 'h':2,
			 'l':4
			 }	

def unpack (format, data, offset=0, funs={}):
	if format[0] == 'L':
		decode_word = little_decode_word
		decode_long = little_decode_long
	elif format[0] == 'B':
		decode_word = big_decode_word
		decode_long = big_decode_long
	else:
		raise error, 'unsupported byte order code'
	result = []
	pos = offset
	i = 1
	while i < len(format):
		ch = format[i]
		# word
		if ch == 'h':
			result.append (decode_word (data[pos:pos+2]))
			pos = pos + 2
		# long
		elif ch == 'l':
			result.append (decode_long (data[pos:pos+4]))
			pos = pos + 4
		# byte
		elif ch == 'b':
			result.append (ord (data[pos:pos+1]))
			pos = pos + 1
		# character
		elif ch == 'c':
			result.append (data[pos:pos+1])
			pos = pos + 1
		# numeric argument
		elif ch in string.digits:
			num_digits = 0
			while format[i] in string.digits:
				num_digits = num_digits+1
				i = i + 1
			num = string.atoi (format[i-num_digits:i])
			format_code = format[i]

			sub_result, sub_len = unpack (
				# this is cheating somewhat, should probably do
				# it in a loop. 8^)
				format[0] + format_code * num, data, pos
				)
			result.append (sub_result)
			pos = pos + sub_len
		# 'procfield' (used for variable-length fields)
		# a procedure is invoked to decode at this point.
		elif ch == '[':
			procname_end = string.find (format, ']', i+1)
			if procname_end == -1:
				raise error, 'no closing bracket for procedure name'
			else:
				procname = format[i+1:procname_end]
			if funs.has_key(procname):
				fun = funs[procname]
				sub_result, length = apply (fun, (result, data, pos))
				result.append (sub_result)
				pos = pos + length
			else:
				raise error, 'procfield function "%s" missing!' % procname
			i = procname_end
		# start of a bitfield
		elif ch == '(':
			bit_lengths = []
			while 1:
				if format[i] == ')':
					break
				else:
					i = i + 1
				num_digits = 0
				while format[i] in string.digits:
					num_digits = num_digits + 1
					i = i + 1
				num = string.atoi (format[i-num_digits:i])
				bit_lengths.append (num)
			total_bits = reduce (lambda x,y: x + y, bit_lengths)
			if (total_bits % 8) != 0:
				raise error, 'bitfield not a multiple of 8 bits %s' % (format)
			bitfield_size = total_bits / 8
			result = result + (unpack_bitfield (bit_lengths, data[pos:pos+bitfield_size]))
			pos = pos + bitfield_size
		i = i + 1
	# return the result, and the length of parsed data
	return tuple(result), pos-offset

#
# To my mind, there should never be a question of what order
# to read bits in.  They should be read MSB to LSB, and interpreted
# in the same fashion.  When a series of bitfields is packed, then
# they should be read and written in the same direction - that is
# from the MSB to the LSB.
#
# When building a bitfield descriptor, be careful - double-check your
# reference.  It may be necessary to reverse the list of bitfields!
#

class bit_stream_reader:
	def __init__ (self, data, byte_pos=0, bit_pos=0):
		self.data = data
		self.byte_pos = byte_pos
		self.bit_pos = bit_pos

	def next_bit (self):
		byte = ord(self.data[self.byte_pos])
		result = (byte & (1<< (7-self.bit_pos)) and 1)
		self.bit_pos = self.bit_pos + 1
		if self.bit_pos == 8:
			self.bit_pos = 0
			self.byte_pos = self.byte_pos + 1
		return result

	def read_bits (self, num_bits):
		# [76543210][76543210][76543210][76543210][76543210]
		#    bit_pos---^ (== 2)
		# byte_pos--^ (== 1)
		r = 0
		for i in range(num_bits):
			bit = self.next_bit()
			r = r << 1
			if bit:
				r = r + 1
		return r

class bit_stream_writer:
	def __init__ (self):
		self.bit_pos = 0
		self.byte = 0
		self.result = ''

	def write_bits (self, number, num_bits):
		if number >= (1L << num_bits):
			raise error, 'number too big for specified number of bits'
		while num_bits:
			if self.bit_pos == 8:
				# start a new output byte
				self.result = self.result + chr(self.byte)
				self.byte = 0
				self.bit_pos = 0
			num_bits = num_bits - 1
			self.byte = self.byte << 1
			if number & (1<<num_bits):
				self.byte = self.byte | 1
			self.bit_pos = self.bit_pos + 1

	def done (self):
		if self.bit_pos != 8:
			raise error, "didn't finish on a byte boundary!"
		self.result = self.result + chr(self.byte)
		return self.result

def print_binary (num, width=8):
	result = ''
	while (width > 0) or num:
		if num & 0x01:
			result = '1' + result
		else:
			result = '0' + result
		num = num >> 1
		width = width - 1
	return result

def unpack_bitfield (bit_lengths, data):
	br = bit_stream_reader (data)
	result = map (lambda x,y=br: y.read_bits (x), bit_lengths)
	return result

def pack_bitfield (bit_lengths, data):
	bw = bit_stream_writer()
	map (bw.write_bits, data, bit_lengths)
	return bw.done()

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
# write out its data.  [currently not true for all field types!]
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

def test_procfield ():
	def read_pascal_string (result, data, pos):
		length = ord(data[pos])
		return data[pos+1:pos+1+length], 1+length

	format = 'Bb[read_pascal_string]l'
	data = '\001\005abcde\000\004\313/'
	print unpack (format, data, 0, {'read_pascal_string':read_pascal_string})

def test_oracle_with_procfield():
	def read_pascal_string (result, data, pos):
		length = ord(data[pos])
		return data[pos+1:pos+1+length], 1+length

	o = Oracle ('procfield test',
				'Bb[rps]l',
				('a byte',
				 'string',
				 'a long'),
				rps=read_pascal_string
				)

	data = '\001\005abcde\000\004\313/'
	print o.unpack (data)
