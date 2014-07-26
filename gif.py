#! /usr/local/bin/python
# -*- Mode: Python; tab-width: 4 -*-
# 	$Id: gif.py,v 1.5 1996/04/07 09:39:28 rushing Exp $	
#	Author: Sam Rushing <rushing@nightmare.com>

# Grok a GIF file.  Uses the actual grammar from the GIF specification,
# so it should be capable of handling any legal gif file, including
# application, plain text, and comment extensions.

# I have a separate C module for doing GIF lzw decompression, so
# using this alone you're stuck with compressed data.

import string
import npstruct

ParseError = 'gif parse error'

# Note: the functions in this file treat 'data' as a string array.
# A file-object like interface could probably be cooked up using
# a sequence-like class wrapper.

# Holds a list of GIF data blocks.  Data blocks are used to
# store not only image data, but application and comment extension
# data.

class Data_Block_List:
	def __init__ (self, blocks):
		self.blocks = blocks
		self.length = reduce (lambda x,y: x+y, map (len, blocks))
	def __repr__ (self):
		return '<GIF Data Block List: %d bytes>' % self.length

def read_data_blocks (results, data, pos):
	start_pos = pos
	blocks = []
	while 1:
		block_size = ord(data[pos])
		if block_size:
			blocks.append (data[pos+1:pos+1+block_size])
			pos = pos + 1 + block_size
		else:
			pos = pos + 1
			break
	return Data_Block_List (blocks), (pos - start_pos)

header = npstruct.Oracle ('GIF Header',
						  'L3c3c',
						  ('signature',
						   'version'))

def read_global_color_table (results, data, pos):
	if results[2]:				# global color table flag
		size = 2<<(results[5])	# global color table size
		ct = Color_Table()
		ct.read (results, data, pos, size)
		return ct, size * 3
	else:
		return None, 0

logical_screen_descriptor = npstruct.Oracle (
	'Logical Screen Descriptor',
	'Lhh(1 3 1 3)bb[gct]',
	('width',
	 'height',
	 'global color table flag',
	 'color resolution',
	 'sort flag',
	 'global color table size',
	 'background color index',
	 'pixel aspect ratio',
	 'global color table'),
	gct=read_global_color_table
	)

image_descriptor = npstruct.Oracle (
	'Image Descriptor',
	'Lbhhhh(1 1 1 2 3)',
	('separator', # always 0x2c
	 'left',
	 'top',
	 'width',
	 'height',
	 'local color table flag',
	 'interlace flag',
	 'sort flag',
	 'reserved',
	 'local color table size'
	 )
	)

graphic_control_extension = npstruct.Oracle (
	'Graphic Control Extension',
	'Lbbb(3 3 1 1)hbb',
	('extension introducer',	# always 0x21
	 'graphic control label',	# always 0xf9
	 'block size',
	 'reserved',
	 'disposal method',
	 'user input flag',
	 'transparent color flag',
	 'delay time',
	 'transparent color index',
	 'block terminator'			# always 0
	 )
	)

comment_extension = npstruct.Oracle (
	'Comment Extension',
	'Lbb[db]',
	('extension introducer',	# always 0x21
	 'comment label',			# always 0xfe
	 'data'),
	db=read_data_blocks
	)

plain_text_extension = npstruct.Oracle (
	'Plain Text Extension',
	'Lbbbhhhhbbbb',
	('extension introducer',	# always 0x21
	 'plain text label',		# always 0x01
	 'block size',
	 'text grid left',
	 'text grid top',
	 'text grid width',
	 'text grid height',
	 'char cell width',
	 'char cell height',
	 'text foreground color index',
	 'text background color index'
	 )
	)

application_extension = npstruct.Oracle (
	'Application Extension',
	'Lbbb8b3b[db]',
	('extension introducer',	# always 0x21	
	 'application label',		# always 0xff
	 'block size',
	 'identifier',
	 'authentication code',
	 'data'),
	db=read_data_blocks
	)

import string

# [This is the grammar given at the end of the GIF specification.]
# The Grammar.
# <GIF Data Stream>	::= Header <Logical Screen> <Data>* Trailer
# <Logical Screen>	::= Logical Screen Descriptor [Global Color Table]
# <Data>			::= <Graphic Block>  | <Special-Purpose Block>
# <Graphic Block>	::= [Graphic Control Extension] <Graphic-Rendering Block>
# <Graphic-Rendering Block> ::= <Table-Based Image> | Plain Text Extension
# <Table-Based Image> ::= Image Descriptor [Local Color Table] Image Data
# <Special-Purpose Block> ::=Application Extension | Comment Extension

def read_gif_header (results, data, pos):
	h, l = header.unpack (data, pos)
	sig = string.joinfields (h['signature'], '')
	ver = string.joinfields (h['version'], '')
	if sig != 'GIF':
		raise ParseError, 'Not a GIF file'
	elif ver not in ['89a', '87a']:
		raise ParseError, 'Unknown GIF version "%s"' % ver
	return (sig, ver), l

class Color_Table:
	def __init__ (self, table=None):
		if table == None:
			self.table = []
		else:
			self.table = table

	def read (self, results, data, pos, size):
		table = range(size)
		for i in range(size):
			table[i] = tuple (map (ord, data[pos:pos+3]))
			pos = pos + 3
		self.table = table

	def __len__ (self):
		return len(self.table)

	def __repr__ (self):
		return '<GIF color table: %d entries>' % len(self.table)

# Sort of like a 'desktop' for the images to sit on,
# though usually there's only a single image.

def read_logical_screen (results, data, pos):
	lsd, lsd_len = logical_screen_descriptor.unpack (data, pos)
	if lsd['global color table flag']:
		size = 2<<lsd['global color table size']
		color_table = range(size)
		for i in range(len(color_table)):
			color_table[i] = tuple (map (ord, data[pos:pos+3]))
			pos = pos + 3
		return (lsd, Color_Table(color_table)), lsd_len + (size * 3)
	else:
		return (lsd, []), lsd_len

# Read high-level image and extension blocks
def read_gif_data (results, data, pos):
	start_pos = pos
	res = []
	while 1:
		# check for the trailer
		if data[pos] == chr(0x3b):
			break
		elif data[pos:pos+2] == chr(0x21)+chr(0xff):
			# application extension
			stuff, len = application_extension.unpack (data, pos)
			res.append (('application extension', stuff))
		elif data[pos:pos+2] == chr(0x21)+chr(0xfe):
			# comment extension
			stuff, len = comment_extension.unpack (data, pos)
			res.append (('comment extension', stuff))
		else:
			stuff, len = read_graphic_block (data, pos)
			res.append (('graphic block', stuff))
		pos = pos + len
	return res, (pos-start_pos)

def read_graphic_block (data, pos):
	# [graphic control extension] <graphic-rendering block>
	if data[pos:pos+2] == chr(0x21)+chr(0xf9):
		# gce is present
		gce, len = graphic_control_extension.unpack (data, pos)
	else:
		gce, len = (None, 0)
	# now read the graphic rendering block
	pos = pos + len
	gb, gb_len = read_graphic_rendering_block (data, pos)
	return (gce, gb), len+gb_len

def read_graphic_rendering_block (data, pos):
	# plain text extension | <table-based-image>
	if data[pos:pos+2] == chr(0x21)+chr(0x01):
		pte, len = plain_text_extension.unpack (data, pos)
		return ('text', pte), len
	else:
		image, len = table_based_image.procfield_function ([], data, pos)
		return ('image', image), len

def read_local_color_table (results, data, pos):
	if results[-1]['local color table flag']:
		size = 2<<(results[-1]['local color table size'])
		ct = Color_Table()
		ct.read (results, data, pos, size)
		return ct, size * 3
	else:
		return None, 0

table_based_image = npstruct.Oracle (
	'GIF table-based image',
	'L[id][lct]b[data]',
	('image descriptor',
	 'local color table',
	 'lzw code size',
	 'image data'
	 ),
	id=image_descriptor.procfield_function,
	lct=read_local_color_table,
	data=read_data_blocks
	)

def read_trailer (results, data, pos):
	if data[pos] != chr(0x3b):
		raise ParseError, 'expected trailer missing'
	else:
		return 0x3b, 1

# Give a fairly in-depth description of the GIF file

def describe_gif_file (stuff):
	stuff, length = stuff
	print 'GIF Version: %s' % stuff['header'][1]
	print 'File Length: %d' % length
	data = stuff['data']
	screen = stuff['logical screen']
	global_color_table = screen['global color table']
	print 'Width: %d Height: %d' % (screen['width'], screen['height'])
	print 'Colors: %d' % (len(global_color_table))
	print 'Number of Blocks: %d' % len(data)
	for i in range(len(data)):
		thing = data[i]
		print '=' *50
		print 'Block: %d' % i
		if thing[0] == 'graphic block':
			gce, (type, info) = thing[1]
			if gce:
				if gce['transparent color flag']:
					print 'Transparent Color: R:%3d G:%3d B:%3d' % (
						global_color_table.table[gce['transparent color index']]
						)
			if type == 'image':
				id = info['image descriptor']
				lct = info['local color table']
				lzw_size = info['lzw code size']
				print 'Image Data: %d blocks, %d bytes' % (
					len(info['image data'].blocks),
					info['image data'].length
					)
				print 'Local Color Table: ',
				if lct:
					print 'yes, %d colors' % len(lct)
				else:
					print 'no'
				print 'Interlaced: ',
				if id['interlace flag']:
					print 'yes'
				else:
					print 'no'
				print 'LZW starting code size: %d' % lzw_size
			elif type == 'text':
				plain_text_extension.describe (info)
		elif thing[0] == 'application extension':
			print 'Application Extension'
			ae = thing[1]
			print 'identifier %s' % (
				string.joinfields (
					map (lambda x: string.upper(hex(x)[2:]),
						 ae['identifier']),
					''))
			print 'Sample from first Data Block: %s' % repr(ae['data'].blocks[0])
		elif thing[0] == 'comment extension':
			print 'Comment: "%s"' % string.joinfields (thing[1]['data'].blocks, '')

GIF_FILE = npstruct.Oracle (
	'GIF file format Top-Level Parser',
	'L[head][ls][data][trailer]',
	('header',
	 'logical screen',
	 'data',
	 'trailer'
	 ),
	head=read_gif_header,
	ls=logical_screen_descriptor.procfield_function,
	data=read_gif_data,	# one or more graphic or special purpose blocks
	trailer=read_trailer
	)

def test (filename):
	data = open (filename, 'rb').read()
	describe_gif_file (GIF_FILE.unpack (data))

def test_files (files):
	for filename in files:
		print '*' * 50
		print filename
		try:
			test (filename)
		except:
			print 'error parsing %s' % filename
	
def scan_directory (dname):
	def gif_filter (name):
		if len(name) > 4 and string.upper(name[-4:]) == '.GIF':
			return 1
		else:
			return 0
	import os
	cwd = os.getcwd()
	os.chdir (dname)
	test_files (filter (gif_filter, os.listdir ('.')))
	os.chdir (cwd)
	
############################################################################
# testing
############################################################################

if __name__ == '__main__':
	import sys
	test_files (sys.argv[1:])
