import socket
from message import *

UDP_IP = "127.0.0.1"
UDP_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Pachetul UDP
sock.settimeout(5)

payload = create_payload(
    "CREATE",
    type="file",
    name="test",
    extension="txt",
    content="Hello World"
)

msg = Message(token=b'\x01', payload=payload)
msg.code = Code.POST
msg.type = Type.CONFIRMABLE

packet = msg.encode_message()

sock.sendto(packet, (UDP_IP, UDP_PORT))
print("Client a trimis mesaj")

try:
    data, addr = sock.recvfrom(4096)
    ack = Message.decode_message(data)
    print("Raspuns primit:", ack.payload.decode("utf-8"))
except socket.timeout:
    print("Timeout-niciun ACK")

sock.close()

