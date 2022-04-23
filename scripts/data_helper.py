import struct, os, csv

class DataHelper(object):

	# Method to convert an IEEE 754 single precision (32-bit) floating-point to its binary string representation
    @classmethod
    def ieee_754_single_precision_float_to_binary(cls, sp_fp):
        return ''.join(bin(c).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', sp_fp))

    # Method to convert an IEEE 754 double precision (64-bit) floating-point to its binary string representation
    @classmethod
    def ieee_754_double_precision_float_to_binary(cls, dp_fp):
        return ''.join(bin(c).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', dp_fp))

    # Method to convert a 32-bit binary string to its IEEE 754 single precision floating-point
    @classmethod
    def binary_32_to_ieee_754_single_precision_float(cls, str_bin_32):
	    return struct.unpack('!f',struct.pack('!I', int(str_bin_32, 2)))[0]

	# Method to convert a 64-bit binary string to its IEEE 754 double precision floating-point
    @classmethod
    def binary_64_to_ieee_754_single_precision_float(cls, str_bin_64):
	    return struct.unpack('!d',struct.pack('!Q', int(str_bin_64, 2)))[0]

	# Method to convert a 16-bit unsigned integer (register) into a 16-bit signed integer (register)
    @classmethod
    def int_16_unsigned_to_signed(cls, int_number):
    	if int_number > 32767:
    		int_number_binary = '{0:16b}'.format(int_number)
    		if int(int_number_binary[0]) != 1:
    			print('***********************************************************')
    			print('***** ERROR CONVERTING THE UNSGINED INT TO SIGNED INT *****')
    			print('***** '+int_number_binary+' *****')
    			print('***********************************************************')
    		else:
    			list_of_char = []
    			for char in int_number_binary:
    				if int(char) == 1:
    					inversed_char = 0
    				elif int(char) == 0:
    					inversed_char = 1
    				list_of_char.append(int(inversed_char))
    			inversed_string = ''
    			for i in range(0, len(list_of_char)):
    				inversed_string += str(list_of_char[i])
    			absol = int(inversed_string, 2)
    			absol = absol + 1
    			int_number = -absol              
    		return int_number
    	else:
    		return int_number
    
    # Method to convert a 16-bit binary string into its 16-bit unsigned integer representation
    @classmethod
    def binary_string_16_bits_to_int_16_unsigned(cls, binary_string_16_bits):
        return struct.unpack('!H',struct.pack('!H', int(binary_string_16_bits, 2)))[0]
    
    # Method to convert a 16-bit unsigned integer data type into its binary string representation on 16 bits
    @classmethod
    def int_16_unsigned_to_binary(cls, uint_number):
        # confirm data type is 'int'
        if isinstance(uint_number, int):
        	# confirm uint_number is unsigned (i.e. >= 0), abort otherwise by returning None
        	if (uint_number < 0) or (uint_number > 65535):
        		print('This function takes UNsigned 16-bit integer numbers to convert them as binary string')
        		print('The provided input value is not within the 16-bit unsigned boundaries: '+str(uint_number))
        		print('...')
        		print('Please provide an unsigned (0 <= x <= 65535) integer-type number as argument')
        		return None
        	binary_string = bin(uint_number)[2:].zfill(16)
        else:
            print('Type of argument '+ str(uint_number) +' is:')
            print('\t',type(uint_number))
            print('...')
            print('Please provide an unsigned (0 <= x <= 65535) integer-type number as argument')
            return None
        return binary_string

    # Method to convert a 16-bit signed integer data type into its binary string representation on 16 bits
    @classmethod
    def int_16_signed_to_binary(cls, sint_number):
    	# confirm data type is 'int'
        if isinstance(sint_number, int):
        	# confirm sint_number is signed (i.e. -32768 <= sint_number <= 32767), abort otherwise by returning None
        	if (sint_number < -32768) or (sint_number > 32767):
        		print('This function takes 16-bit Signed integer numbers to convert them as binary string')
        		print('The provided input value is not within the 16-bit signed boundaries: '+str(sint_number))
        		print('...')
        		print('Please provide a signed (-32768 <= x <= 32767) integer-type number as argument')
        		return None
        	else:
        		sint_bin = bin(sint_number)
        		offset_0b = 2
        		if "-" in sint_bin:
        			sint_sign_negative = True
        			offset_0b = 3
        		sint_bin = sint_bin[offset_0b:].zfill(16)
        		if sint_sign_negative:
        			# inverse the bits
        			sint_bin = ''.join(['1' if i == '0' else '0' for i in sint_bin])
        			# add 1 to the inversed bits
        			sint_bin = bin((int(sint_bin,2)+int(bin(1),2)))[2:] # use [2:] to remove the leading '0b'
        			return sint_bin
        		else:
        			return sint_bin
        else:
            print('Type of argument '+ str(sint_number) +' is:')
            print('\t',type(sint_number))
            print('...')
            print('Please provide a signed (-32768 <= x <= 32767) integer-type number as argument')

    # Method to swap bytes in a 16-bit register provided and returned as binary string; use for Big-Endian/Little-Endian conversion on 16-bit registers
    @classmethod
    def int_16_swap_bytes(cls, binary_string_16_bits):
        swapped = binary_string_16_bits[8:16] + binary_string_16_bits[0:8]
        return swapped

    # Method to swap 8-bit bytes in a 32-bit binary strings, provided and returned as binary string; use for Big-Endian/Little-Endian conversion on 32-bit float "registers"
    # [A B C D] -> [B A] [D C]
    @classmethod
    def float32_swap_bytes(cls, binary_string_32_bits):
        swapped = binary_string_32_bits[8:16] + binary_string_32_bits[0:8] + binary_string_32_bits[24:32] + binary_string_32_bits[16:24]
        return swapped

    # Method to swap 16-bit words in a 32-bit binary strings, provided and returned as binary string; use for Big-Endian/Little-Endian conversion on 32-bit float "registers"
    # [A B C D] -> [C D] [A B]
    @classmethod
    def float32_swap_words(cls, binary_string_32_bits):
        swapped = binary_string_32_bits[16:32] + binary_string_32_bits[0:16]
        return swapped

    # Method to swap both 8-bit bytes and 16-bit words in a 32-bit binary strings, provided and returned as binary string; use for Big-Endian/Little-Endian conversion on 32-bit float "registers"
    # [A B C D] -> [D C] [B A]
    @classmethod
    def float32_swap_bytes_words(cls, binary_string_32_bits):
        swapped_words =  DataHelper.float32_swap_words(binary_string_32_bits)
        swapped = DataHelper.float32_swap_bytes(swapped_words)
        return swapped

    # Method to load a .csv file and convert its content into an in-memory Python list of dictionaries (lod)
    @classmethod
    def csv_to_lod(cls, full_path_to_csv_file, header=True):
    	# first, check if the file does exist at the path provided, abort if not
    	if not os.path.isfile(full_path_to_csv_file):
    		print('\n\t'+'File "'+full_path_to_csv_file+'" not found! Unable to load to lod!'+'\n')
    		return
    	with open(full_path_to_csv_file, "r") as f:
    		if header:
    			csv_reader = csv.DictReader(f)
    			lod = list(csv_reader)
    		else:
    			lod = []
    			for line in f:
   					record = {}
   					for col, item in enumerate(line.strip().split(',')):
   						record['column_'+str(col)] = item
   					lod.append(record)
    	return lod

    # Method to export an in-memory Python list of dictionaries (lod) to a .csv file on the local file system
    @classmethod
    def lod_to_csv(cls, lod, full_path_to_csv_file):
        keys = lod[0].keys()
        with open(full_path_to_csv_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(lod)
        output_file.close()