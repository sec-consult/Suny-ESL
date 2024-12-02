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


