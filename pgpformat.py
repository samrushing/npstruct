#! /usr/local/bin/python
# -*- Mode: Python; tab-width: 4 -*-

# Author: Sam Rushing <rushing@nightmare.com>

# See 'pgp/doc/pgformat.doc' for details on the file formats.
# To try this file out, just do this:
#
# $ python pgpformat.py pgp/pubring.pgp | less
#
# It'll dump a detailed description of the data tucked into
# your PGP public key ring. [a bit more detailed than 'pgp -kvv']

import npstruct
import string

# Read a multi-precision integer, which starts with
# a word bitcount.  The integer is padded with zero
# MSB's to fit into a byte boundary.

def read_mpi (result, data, pos):
	values, length = npstruct.unpack ('Bh', data, pos)
	bitcount = values[0]
	(d,r) = divmod (bitcount, 8)
	if r:
		d = d + 1
	mpi = data[pos+2:pos+2+d]
	# hexify it
	mpi = string.joinfields (map (lambda x: hex(ord(x))[2:], mpi), '')
	# turn it into a python long
	mpi = eval ('0x%sL' % mpi)
	return (bitcount, mpi), d+2

def read_ctb (result, data, pos):
	dict, length = CTB.unpack (data[pos])
	return dict, length

def read_ctb_len (result, data, pos):
	ctb_dict = result[0]
	size = 1<<ctb_dict['length_of_length']
	if size == 1:
		(length,), len = npstruct.unpack ('Bb', data, pos)
	elif size == 2:
		(length,), len = npstruct.unpack ('Bh', data, pos)
	elif size == 4:
		(length,), len = npstruct.unpack ('Bl', data, pos)
	elif size == 8:
		length, len = 0, 0
	return length, len

import time
def read_timestamp (result, data, pos):
	values, length = npstruct.unpack ('Bl', data, pos)
	return time.ctime (values[0]), length

RSA = npstruct.Oracle (
	'RSA public-key-encrypted packet',
	'B[ctb][len]b8bb[mpi]',
	('ctb',			# CTB for RSA pub-key-encrypted packet
	 'length',		# 16-bit length of packet (in bytes?)
	 'version',		# == 2.
	 'KeyID',		# 64-bit Key ID
	 'algorithm',	# == 1 for RSA
	 'key',			# mpi, encrypted conventional key
	 ),
	ctb=read_ctb,
	len=read_ctb_len,
	mpi=read_mpi
	)

signature_packet = npstruct.Oracle (
	'Signature Packet',
	'B[ctb][len]bbb[ts]8bbb2b[mpi]',
	('ctb',
	 'packet_length',
	 'version',				# == 2, 3 >= PGP2.6 after 9/1/94
	 'md_length',			# == 5
	 'signature_classification',
	 'timestamp',			# 32-bit timestamp: when key was made
	 'KeyID',				# 64-bit key id
	 'pub_key_algorithm',	# RSA=0x01 -- affects field defs that follow
	 'md_algorithm',		# MD5 = 0x01
	 'check_bytes',			# first 2 bytes of message digest
	 'digest',				# encrypted message digest
	 ),
	ctb=read_ctb,
	len=read_ctb_len,
	mpi=read_mpi,
	ts=read_timestamp
	)

signature_classification_table = {
	0x00:'signature of message or document, binary image',
	0x01:'signature of message or document, canonical text',
	0x10:'key certification, generic',
	0x11:'key certification, persona',
	0x12:'key certification, casual',
	0x13:'key certification, positive id',
	0x20:'key compromise',
	0x30:'key/userid revocation',
	0x40:'signature timestamp'
	}

PGP_ASN = [0x30,0x20,0x30,0x0c,0x06,0x08,0x2a,0x86,0x48,
		   0x86,0xf7,0x0d,0x02,0x05,0x05,0x00,0x04,0x10]

# 'pgformat.doc' is somewhat misleading on the meaning of the
# length field.  It's labeled 'length of packet', but seeing how
# when I use it I get 5 extra bytes sitting around I suspect it's
# really the length of the data.

##def read_encrypted_data (result, data, offset):
##	ctb = result[0]
##	# packet length should be here
##	packet_length = result[1]
##	data_length = packet_length - (1 + (1<<ctb['length_of_length']))
##	return data[offset:offset+data_length], data_length

def read_encrypted_data (result, data, offset):
	data_length = result[1]
	return data[offset:offset+data_length], data_length

conventional_packet = npstruct.Oracle (
	'Conventional Key Encrypted data packet',
	'B[ctb][len][ed]',
	('ctb',
	 'length',
	 'data'
	 ),
	ctb=read_ctb,
	len=read_ctb_len,
	ed=read_encrypted_data
	)

def read_compressed_data (result, data, offset):
	raise TypeError, "can't read compressed data yet!!!"

compressed_packet = npstruct.Oracle (
	'Compressed data packet',
	'B[ctb]b[cd]',
	('ctb',
	 'algorithm',	# 1==ZIP
	 'data'			# compressed data
	 ),
	ctb=read_ctb,
	cd=read_compressed_data
	)

def read_pascal_string (result, data, pos):
	length = ord(data[pos])
	return data[pos+1:pos+1+length], length+1

def read_literal_data (result, data, pos):
	# the packet length includes all the other bits,
	# so we have to strain to figure out how big the
	# data is...
	length = result[1] - (1+4+1+4+len(result[3])+1)
	return data[pos:pos+length], length

literal_data = npstruct.Oracle (
	'literal data packet, with filename and mode',
	'B[ctb][len]b[rf][ts][rd]',
	('ctb',
	 'packet_length',
	 'mode',
	 'filename',
	 'timestamp',
	 'data'),
	ctb=read_ctb,
	len=read_ctb_len,
	rf=read_pascal_string,
	rd=read_literal_data,
	ts=read_timestamp
	)

comment_packet = npstruct.Oracle (
	'comment packet',
	'B[ctb][rps]',
	('ctb',
	 'comment',
	 ),
	ctb=read_ctb,
	rps=read_pascal_string
	)

def read_cipher_initial_value (results, data, pos):
	encrypted = results[-1]
	if encrypted:
		iv, length = npstruct.unpack ('B8b', data, pos)
		return iv, length
	else:
		return 0, 0

secret_key_certificate = npstruct.Oracle (
	'secret key certificate',
	'B[ctb][len]b[ts]hb[mpi][mpi]b[civ][mpi][mpi][mpi][mpi]h',
	('ctb',
	 'packet_length',
	 'version',
	 'timestamp',
	 'valid_for',
	 'algorithm',			# 1 == RSA
	 'rsa_pub_mod_n',
	 'rsa_enc_exp',
	 'cipher_algorithm',	# 0==unencrypted, 1==IDEA
	 'cipher_iv',			# not present if unencrypted
	 'sec_exp_d',			# secret decryption exponent d
	 'sec_fac_p',			# secret factor p
	 'sec_fac_q',			# secret factor q
	 'seq_mul_inv_u',		# secret multiplicative inverse u
	 'checksum'				# 16-bit checksum of all preceding
	 						#   secret component bytes
	 ),
	ctb=read_ctb,
	len=read_ctb_len,
	civ=read_cipher_initial_value,
	mpi=read_mpi,
	ts=read_timestamp
	)

public_key_certificate = npstruct.Oracle (
	'public key certificate',
	'B[ctb][len]b[ts]hb[mpi][mpi]',
	('ctb',
	 'length',
	 'version',		# 3 == PGP2.6 or later
	 'timestamp',
	 'valid_for',
	 'algorithm',	# 1 == RSA,
	 # the last 32 bits of this are the user-visible KeyID.
	 'mpi_rsa_pub_mod_n',
	 'mpi_rsa_pub_enc_exp'
	 ),
	ctb=read_ctb,
	len=read_ctb_len,
	mpi=read_mpi,
	ts=read_timestamp
	)

user_id = npstruct.Oracle (
	'User ID packet',
	'B[ctb][rps]',
	('ctb',
	 'user_id',),
	ctb=read_ctb,
	rps=read_pascal_string
	)

# Possible PGP bug - keyring trust packets with
# length_of_length set to '1' instead of '0' (which
# would indicate a 2-byte length, instead of a 1-byte
# length, since length is roughly 1<<l_o_l)
# For this reason we don't try to decode the ctb length.

trust_packet = npstruct.Oracle (
	'keyring trust packet',
	'B[ctb]bb',
#	'B[ctb][len]b',
	('ctb',
	 'length',
	 'flags'),
	ctb=read_ctb,
#	len=read_ctb_len
	)

# TODO: crack the trust packets (tricky because they're context-sensitive,
#   but probably not hard).
# TODO: there's also (trust_after_id, trust_after_signature)

trust_after_key = npstruct.Oracle (
	'trust bits for a key',
	'B(3 2 1 1 1)',
	('ownertrust',
	 'reserved',
	 'disabled',
	 'reserved2',
	 'buckstop'
	 )
	)

CTB = npstruct.Oracle (
	'cipher type byte',
	'B(1 1 4 2)',
	('ctb_designator',
	 'reserved',
	 'type',
	 'length_of_length')
	)

def decode_ctb_type (char):
	dict, size = CTB.unpack(char)
	# sanity check
	if not (dict['ctb_designator']):
		raise TypeError, 'not a CTB byte'
	else:
		# get the type field (bits 5-2)
		type = dict['type']
		if not ctb_type_table.has_key (type):
			raise TypeError, 'unknown CTB type'
		else:
			length = 1<<(dict['length_of_length'])
			if length == 8:
				length = 0
			return type, length

ctb_type_table = {
	1 :('public-key-encrypted packet', RSA),
	2 :('secret-key-encrypted (signature) packet', signature_packet),
	3 :('message digest packet',),
	5 :('Secret key certificate',	secret_key_certificate),
	6 :('Public key certificate',	public_key_certificate),
	8 :('Compressed data packet',	compressed_packet,),
	9 :('Conventional-Key-Encrypted data', conventional_packet),
	11:('Raw literal plaintext data, with filename and mode', literal_data),
	12:('Keyring trust packet', trust_packet),
	13:('User ID packet, associated with public or secret key', user_id),
	14:('Comment packet', comment_packet),
	}

def test (filename):
	test_data (open(filename, 'rb').read())

def test_data (data):
	pos = 0
	while 1:
		if pos == len(data):
			break
		else:
			ctb_type, length = decode_ctb_type (data[pos])
			desc, oracle = ctb_type_table[ctb_type]
			print '='*50
			#print 'position: %d' % pos
			#print 'found "%s"' % desc
			result_data, length = oracle.unpack (data, pos)
			#print 'length: %d' % length
			pos = pos + length
			oracle.describe (result_data)

if __name__ == '__main__':
	import sys
	test(sys.argv[1])
