import crcmod

class base_frame:
    def __init__(self,raw_frame):
        self.broke = False
        #check CRC
        crc16 = crcmod.mkCrcFun(0x18005, 0xffff, False)
        if crc16(raw_frame[:-2]).to_bytes(2,'big') != raw_frame[-2:]:
            self.broken = True
            raise ValueError("Invalid CRC!")
        self.crc = raw_frame[-2:]
        self.frame_len = raw_frame[0]
        self.tag_id = raw_frame[1:4]
        self.raw_payload = raw_frame[4:-2]

    def __str__(self):
        result = "******************************************\n"
        result += "Tag ID: {:06X}\n".format(int.from_bytes(self.tag_id,'big'))
        return result

class img_header():
    def __init__(self, data):
        if data[0:1] != b'\xfc':
            raise ValueError("Not a valid IMG header")
        self.loc_x = data[1:3]
        self.loc_y = data[3:5]
        self.height = int.from_bytes(data[5:7],'big')
        self.width = int.from_bytes(data[7:9],'big')
        self.len = int.from_bytes(data[9:13], 'big')

class img_frame(base_frame):
    def __init__(self, raw_frame, frame_version=None):
        super().__init__(raw_frame)
        if frame_version == None:
            self.protocol_version = self.raw_payload[2]
        else:
            self.protocol_version = frame_version
        if self.protocol_version == 0xfb:
            #Large display
            if type(self) == img_frame_first:
                #Field contains final frame num
                self.frame_num = 1
                self.frame_num_final = int.from_bytes(self.raw_payload[0:2],'big')
            else:
                # Field contains current frame num
                self.frame_num_final = 0
                self.frame_num = int.from_bytes(self.raw_payload[0:2],'big')
        else:
            self.frame_num = self.raw_payload[1]
            self.frame_num_final = self.raw_payload[0]
        self.raw_payload = self.raw_payload[3:]
    
    def __str__(self):
        result = super().__str__()
        if self.protocol_version == 0xfb:
            #Large display
            if type(self) == img_frame_first:
                result += "Expected Frames: {}\n".format(self.frame_num_final)
            else:
                result += "Frame: {}\n".format(self.frame_num)
        else:
            result += "Frame {}/{}\n".format(self.frame_num, self.frame_num_final)
        return result

class img_frame_first(img_frame):
    def __init__(self, raw_frame):
        super().__init__(raw_frame)
        self.LED = self.raw_payload[0:2]
        self.batch_code = self.raw_payload[2:4]
        self.unknown_pattern3 = self.raw_payload[4:6]
        self.LED_times = self.raw_payload[6:8]
        self.img_header = img_header(self.raw_payload[8:])
        self.raw_payload = self.raw_payload[21:]

    def __str__(self):
        result = super().__str__()
        result += "LED Status: {}\n".format(self.LED)
        result += "Batch Code: {}\n".format(int.from_bytes(self.batch_code, 'big'))
        result += "Image dimensions: {} x {}\n".format(self.img_header.width+1, self.img_header.height+1)
        return result

class tag_response(base_frame):
    def __init__(self, data):
        super().__init__(data)
        self.power = self.raw_payload[0]/10
        self.temperature = self.raw_payload[3]
        self.raw_rssi = self.raw_payload[1:3]

    def __str__(self):
        result = super().__str__()
        result += "Power: {}\n".format(self.power)
        result += "Temperature: {}\n".format(self.temperature)
        return result
