import esl_frame
import socket
import hexdump
import compression
from PIL import Image


UDP_IP = "127.0.0.1"
UDP_PORT = 1234


def render_image(data, width, height):
    img_data = compression.decompress(data)
    img = Image.new( 'RGB', (width,height), "black")
    pixels = img.load()
    for i in range(0,height):
        for j in range(0,width):
            if img_data[i*width + j] == 0:
                #inverted color scheme
                pixels[j,i] = (255,255,255)
            else:
                pixels[j,i] = (0,0,0)

    img.show()



if __name__ == "__main__" :
    print("Starting up")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    while True:
        data, _ = sock.recvfrom(63)
        hexdump.hexdump(data)
        try:
            frame = esl_frame.img_frame_first(data)
            #first frame of image, parse as image
            img_frames = []
            img_payload = b''
            img_frames.append(frame)
            img_payload += frame.raw_payload
            print(img_frames[-1])
            protocol_version = frame.protocol_version
            for i in range(2, frame.frame_num_final+1):
                data,_ = sock.recvfrom(63)
                #hexdump.hexdump(data)
                frame = esl_frame.img_frame(data, frame_version=protocol_version)
                if frame.frame_num != i:
                    raise ValueError("Missing Frame, Aborting")
                img_frames.append(frame)
                img_payload += frame.raw_payload
                print("New Frame:")
                print(img_frames[-1])
            #render image
            print("Rendering Image...")
            render_image(img_payload[:img_frames[0].img_header.len], img_frames[0].img_header.width+1, img_frames[0].img_header.height+1)
            print("Getting Tag Responses")
            tag_responses = []
            for i in range(0,2):
                data,_ = sock.recvfrom(63)
                hexdump.hexdump(data)
                tag_responses.append(esl_frame.tag_response(data))
                print(tag_responses[-1])
            #dump AP spam
            print("Dumping AP Spam")
            for i in range(0, 18):
                _,_ = sock.recvfrom(63)
        except ValueError as err:
            print("Detected ValueError {}".format(err))
        except IndexError as err:
            print("Detected IndexError {}".format(err))
    
    sock.close()
