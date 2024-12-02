#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 Steffen Robertz.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
import crcmod
import hexdump
import math
from PIL import Image, ImageOps
from PIL import *
import random


class compression:

    def decompress(payload):
        #Function returns single bit per Byte
        decompressed = b""

        i=0
        while i < len(payload):
            #print("Processing byte {}: {:2x}".format(i,payload[i]))
            #print("Decompressed: {}".format(decompressed))
            if (payload[i] & 0x80):
                #case 1
                #print("case1")
                value = (payload[i] & (1<<6))>>6
                #decompressed += value.to_bytes(1, byteorder='big')
                for j in range(6,-1,-1):
                    if payload[i] & (1<<j):
                        #decompressed += value.to_bytes(1, byteorder='big')
                        decompressed += b'\x01'
                    else:
                        decompressed += b'\x00'
                i+=1
            elif payload[i] & 0x80==0:
                #case 2,3,4
                if payload[i] & 0x3f == 1:
                    #print("Case3")
                    value = (payload[i] & (1<<6))>>6
                    decompressed += value.to_bytes(1, byteorder='big')*(payload[i+1])
                    i+=2
                elif payload[i] & 0x3f == 0:
                    #print("Case4")
                    value = (payload[i] & (1<<6))>>6
                    decompressed += value.to_bytes(1, byteorder='big')*(int.from_bytes(payload[i+1:i+3],'little'))
                    i+=3
                else:
                    #print("Case2")
                    value = (payload[i] & (1<<6))>>6
                    repeat = payload[i] & 0x3f
                    decompressed += value.to_bytes(1, byteorder='big')*repeat
                    i +=1

        return decompressed

    def compress(data):
        # data is expected to be one byte per bit
        compressed = b''
        while len(data):
            # how many bits are the same
            i = 0
            while i<len(data) and data[0] == data[i]:
                i += 1

            if i < 7 :
                # case 1
                #print("Case1")
                value = 0x80
                for j in range(0,7):
                    value |= data[j] << (6-j)
                compressed += value.to_bytes(1,'big')
                data = data[7:]
            elif i < 32:
                #case 2
                #print("Case2")
                value = 0x00
                value |= data[0] << 6 
                value |= i
                compressed += value.to_bytes(1,'big')
                data = data[i:]
            elif i < 256:
                #case 3
                #print("Case3")
            
                value = 0
                value |= data[0] << 6 
                value |= 1
                compressed += value.to_bytes(1,'big') 
                compressed += i.to_bytes(1,'big')
                data = data[i:]
            else:
                #case 4
                #print("Case4")
                value = 0
                value |= data[0] << 6 
                compressed += value.to_bytes(1,'big')
                compressed += i.to_bytes(2,'little')
                data = data[i:]
        return compressed


class esl_frame_gen:

    def __init__(self, tag_id, height, width, img_file):
        self.tag_id = tag_id
        self.height = height
        self.width = width
        self.img_file = img_file

    def wakeup(self):
        all_frames = []
        for i in range(0x0398, -1, -1):
            print("Generating: {}".format(i))
            frame = b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xd3\x91\xd3\x91\x08'
            frame += self.tag_id.to_bytes(3,'big')
            frame += b'\x00\x00'
            frame += i.to_bytes(2,'little')
            frame += b'\xa0'
            crc16 = crcmod.mkCrcFun(0x18005, 0xffff, False)
            frame += crc16(frame[12:]).to_bytes(2,'big')
            all_frames += [frame]*5
        return all_frames

    def __image_data(self):
        width_target = self.width + 1
        height_target = self.height + 1
        img = Image.open(self.img_file)
        img = ImageOps.contain(img, (width_target, height_target))
        img = ImageOps.pad(img, (width_target, height_target), color="white", centering=(0,0))
        img = ImageOps.grayscale(img)
        img = ImageOps.posterize(img, 1)

        #convert image to pixel bytes
        pixels = img.load()
        width, height = img.size
        print("width: {}, height={}".format(width,height))

        img_data = b''

        for i in range(0,height):
            for j in range(0, width):
                if pixels[j,i] > 127:
                    # pixel is white
                    pixels[j,i] = 255
                    img_data += b'\x00'
                else:
                    pixels[j,i] = 0
                    img_data += b'\x01'
        img.show()
        return img_data

    def image(self):
        # calculate how many frames are required
        # first frame can hold 33 bytes, regular frames can hold 54 bytes
        # 16 bytes required in last frame to zero out red channel
        
        #crete compressed image
        data = compression.compress(self.__image_data())

        #build full payload (add black channel header)
        black_header = b'\xfc\x00\x00\x00\x00'
        black_header += self.height.to_bytes(2,'big')
        black_header += self.width.to_bytes(2,'big')
        black_header += len(data).to_bytes(3,'big')
        data = black_header + data

        # build full payload (add zero header for red channel)
        data += b'\xfc\x80\x00\x00\x00'
        data += (self.height | 0x80).to_bytes(2,'big')
        data += self.width.to_bytes(2,'big')
        data += b'\x00\x00\x00\x03'
        compressed_zero_payload = int(((self.width+1)*(self.height+1))/8).to_bytes(3,'big')
        data += compressed_zero_payload

        frame_cnt = math.ceil((len(data)+21)/54)
        print("Requiring {} IMG Frames for completion".format(frame_cnt))


        all_frames = []

        for i in range(1, frame_cnt+1):
            frame = b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xd3\x91\xd3\x91'
            data_to_add = b''
            if i == 1:
                #Build first frame header
                if frame_cnt > 1:
                    #frame has max frame size
                    frame += b'\x3c'
                    # data to add
                    data_to_add = data[:46]
                    data = data[46:]
                else:
                    length = len(data) + 6 + 8
                    frame += length.to_bytes(1,'big')
                    data_to_add = data[:]
                    data = []
                #Add all required headers
                frame += self.tag_id.to_bytes(3,'big')
                frame += frame_cnt.to_bytes(1,'big')
                frame += i.to_bytes(1,'big')
                frame += b'\x33'
                # Add first frame special headers
                frame += b'\x07\x00' #LED
                frame += random.randbytes(2) #Batch Code
                frame += b'\x00\xed\x00\x0a' #Fixed + LED Times
            else:
                #multiple frames
                if frame_cnt != i:
                    # Frames with max size
                    frame += b'\x3c'
                    data_to_add = data[:54]
                    data = data[54:]
                else:
                    frame += (len(data)+6).to_bytes(1,'big')
                    data_to_add = data[:]
                    data = []
                # Add generic header
                frame += self.tag_id.to_bytes(3,'big')
                frame += frame_cnt.to_bytes(1,'big')
                frame += i.to_bytes(1,'big')
                frame += b'\x33'
            #Add img data
            frame +=  data_to_add
            #Calc CRC
            crc16 = crcmod.mkCrcFun(0x18005, 0xffff, False)
            frame += crc16(frame[12:]).to_bytes(2,'big')
            #frame += b'\xff'*8
            print("Frame {}".format(i))
            hexdump.hexdump(frame)
            all_frames.append(frame)
        return all_frames




class img_source(gr.sync_block):
    """
    docstring for block img_source
    """
    def __init__(self, file_path='/home/srb/workspace/hackrf-tests/python_final/sec.png', tag_id=0x065302, height=103, width=215, samp_rate=1750000):
        gr.sync_block.__init__(self,
            name="img_source",
            in_sig=None,
            out_sig=[numpy.float32])
        
        #self.tag_id = tag_id
        #self.filename = file_path
        self.samp_rate = samp_rate
        #self.f = open(self.filename, "rb")
        self.generator = esl_frame_gen(tag_id, height, width, file_path)
        repeat = int(self.samp_rate/175000)
        silence = int(0.001*self.samp_rate)
        print("Silence Samples: {}".format(silence))
        print("Repeat {}".format(repeat))
        self.wakeup = numpy.empty(921*5*(23*8*repeat+silence))
        print("going to assemble wakeup")
        frames = self.generator.wakeup()
        print(len(frames))
        index = 0
        for frame in frames:
            for mybyte in frame:
                for i in range(0,8):
                    bit = ((mybyte & (1<<(7-i)))>>(7-i))*2-1
                    self.wakeup[index:index+repeat] = numpy.full(repeat, bit)[:]
                    #print("Appending from {} to {} bit {} from byte {:02x}".format(index, index+repeat, bit, mybyte))
                    #print(self.wakeup[index:index+repeat])
                    index += repeat
            self.wakeup[index:index+silence] = numpy.zeros(silence)
            index += silence
        #hexdump.hexdump(self.wakeup)
        print("Finished building wakeup")
        

        print("going to assemble img frames")
        repeat = int(self.samp_rate/100000)
        frames = self.generator.image()
        silence = int(0.0065*self.samp_rate)
        #evaluate length
        size = 0
        for frame in frames:
            size += len(frame)
        initial_silence = int(0.220*self.samp_rate)
        end_silence = int(0.100*self.samp_rate)
        self.image = numpy.empty(size*8*repeat+len(frames)*silence+initial_silence+end_silence)
        self.image[:initial_silence] = numpy.zeros(initial_silence)
        self.image[-end_silence:] = numpy.zeros(end_silence)
        index = initial_silence
        for frame in frames:
            #print("Handling frame: {}".format(frames.index(frame)))
            for mybyte in frame:
                for i in range(0,8):
                    bit = ((mybyte & (1<<(7-i)))>>(7-i))*2-1
                    self.image[index:index+repeat] = numpy.full(repeat, bit)[:]
                    #print("Appending from {} to {} bit {} from byte {:02x}".format(index, index+repeat, bit, mybyte))
                    #print(self.image[index:index+repeat])
                    index += repeat
            self.image[index:index+silence] = numpy.zeros(silence)
            index += silence

        print("Finished building img frames2")
        self.send_wakeup = True
        self.image_sent = 0

    def work(self, input_items, output_items):
        if len(self.wakeup)-self.nitems_written(0) > 0:
            #print("Send wakup")
            data_to_transmit = min(len(output_items[0]), len(self.wakeup)-self.nitems_written(0))
            output_items[0][:data_to_transmit] = self.wakeup[self.nitems_written(0):self.nitems_written(0)+data_to_transmit]
            return data_to_transmit
        else:
            #return 0
            #print("Going to send data")
            data_to_transmit = min(len(output_items[0]), len(self.image)-self.image_sent)
            #print("len out: {} 2nd option: {}".format(len(output_items[0]), len(self.image)-self.image_sent))
            #print("out buffer: {}, sending: {}".format(len(output_items[0]), data_to_transmit))
            output_items[0][:data_to_transmit] = self.image[self.image_sent:self.image_sent+data_to_transmit]
            self.image_sent += data_to_transmit
            return data_to_transmit
        return 0
