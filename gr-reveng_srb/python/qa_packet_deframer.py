#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Steffen Robertz.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import pmt
import numpy
try:
    from reveng_srb import packet_deframer
except ImportError:
    import os
    import sys
    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append(os.path.join(dirname, "bindings"))
    from reveng_srb import packet_deframer

class qa_packet_deframer(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        instance = packet_deframer('test', [b"\x01",b"\x00",b"\x01",b"\x00",b"\x01",b"\x00",b"\x01",b"\x00"], True, 23, 0, 0, 0, False)
    
    def test_001_t (self):
        ''' Test fixed length packet '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        stream = ([0] * 30) + sync + data + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, True, len(data), 0, 0, 0, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        self.assertTrue(sink.num_messages() >=1 )
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bits) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == data)

    def test_002_t (self):
        '''
        Test variable length packet. Length byte straight after sync, no
        additional bytes.
        '''
        # set up fg
        sync = list(map(int,bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))

        pkt = plen + data
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 0, 0, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        self.assertTrue(sink.num_messages() >=1 )

        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bits) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(meta.get('name') == "boop")

        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_003_t (self):
        '''
        Test variable length packet. Two additional bytes for checksum
        after data packet
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = plen + data + csum
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 0, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bits) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_004_t (self):
        '''
        Test variable length packet. Length is indexed two bytes after
        sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + plen + data + csum
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 2, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bits) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_005_t (self):
        '''
        Test two back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + plen + data + csum
        stream = ([0] * 30) + sync + pkt + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 2, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        for idx in range(2):
            rec_msg = pmt.to_python(sink.get_message(idx))

            self.assertTrue(isinstance(rec_msg, tuple))
            self.assertTrue(len(rec_msg) == 2)

            (meta, bits) = rec_msg
            self.assertTrue(isinstance(meta, dict))
            self.assertTrue(isinstance(bits, numpy.ndarray))
            self.assertTrue(list(bits) == pkt)

    def test_006_t (self):
        ''' Test fixed length packet '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        stream = ([0] * 30) + sync + data + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, True, len(data), 0, 0, 0, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bytez) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0xde, 0xad, 0xbe, 0xef])

    def test_007_t (self):
        '''
        Test variable length packet. Length byte straight after sync, no
        additional bytes.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))

        pkt = plen + data
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 0, 0, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bytez) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(meta.get('name') == "boop")

        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x04, 0xde, 0xad, 0xbe, 0xef])

    def test_008_t (self):
        '''
        Test variable length packet. Two additional bytes for checksum
        after data packet
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = plen + data + csum
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 0, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bytez) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_009_t (self):
        '''
        Test variable length packet. Length is indexed two bytes after
        sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + plen + data + csum
        stream = ([0] * 30) + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bytez) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_010_t (self):
        '''
        Test two back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + plen + data + csum
        stream = ([0] * 30) + sync + pkt + sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 0, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        for idx in range(2):
            rec_msg = pmt.to_python(sink.get_message(idx))

            self.assertTrue(isinstance(rec_msg, tuple))
            self.assertTrue(len(rec_msg) == 2)

            (meta, bytez) = rec_msg
            self.assertTrue(isinstance(meta, dict))
            self.assertTrue(isinstance(bytez, numpy.ndarray))
            self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_011_t (self):
        '''
        Test that max length drops packet with corrupted length byte. Send
        back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        p_bad_len = list(map(int, bin(99)[2:].zfill(8)))
        plen = list(map(int, bin(4)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt1 = txid + p_bad_len + data + csum
        pkt2 = txid + plen + data + csum

        stream = ([0] * 30) + sync + pkt1 + sync + pkt2 + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, False, 0, 4, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, bytez) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

        try:
            rec_msg = pmt.to_python(sink.get_message(1))
            self.assertTrue(False)
        except RuntimeError:
            pass

    def test_12_t(self):
        ''' Test fixed length packet ESL'''
        # set up fg
        sync = list(map(int, bin(0xaaaaaaaaaaaaaaaa)[2:].zfill(64)))
        sync_string = [x.to_bytes(1,'big') for x in sync]
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        stream = ([0] * 30) + sync + data + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = packet_deframer('boop', sync_string, True, len(data), 0, 0, 0, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        self.assertTrue(sink.num_messages() >=1 )
        rec_msg = pmt.to_python(sink.get_message(0))

        self.assertTrue(isinstance(rec_msg, tuple))
        self.assertTrue(len(rec_msg) == 2)

        (meta, byte) = rec_msg
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(byte, numpy.ndarray))
        self.assertTrue(list(byte) == [0xde,0xad,0xbe,0xef])



if __name__ == '__main__':
    gr_unittest.run(qa_packet_deframer)
