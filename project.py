import socket
import os
import hashlib
import time
import threading


class KeepAliveSender(threading.Thread):
    def __init__(self, s, info):
        threading.Thread.__init__(self)
        self.s = s
        self.info = info
        self._stop = threading.Event()

    def stop(self): 
        self._stop.set() 
  
    def stopped(self): 
        return self._stop.isSet() 

    def run(self):
        counter = 0
        while True:
            try:
                if self.stopped():
                    print('stop!')
                    return
                if counter == 50:
                    counter = 0    

                    self.s.sendto(createInfoHeader(16), self.info)
                    print('send!', self.info)

                    self.s.recv(1500)
                time.sleep(0.1)
                counter += 1
            except socket.timeout:
                exit()


def toBytes(var, size):
    return var.to_bytes(size, 'big')

def fromBytes(var):
    return int.from_bytes(var, 'big')

def createInfoHeader(flag, fileSize = 0, fragmentSize = 0, fragmentNumber = 0, fileName = ''):
    return toBytes(flag, 1) + toBytes(fileSize, 4) + toBytes(fragmentSize, 2) + toBytes(fragmentNumber, 4) + bytes(fileName, 'latin-1')

def createDataHeader(flag, fragmentNumber, data):
    crc = hashlib.md5(toBytes(flag, 1) + toBytes(fragmentNumber, 4) + data)

    return toBytes(flag, 1) + toBytes(fragmentNumber, 4) + crc.digest() + data



def receive(s, message, senderInfo, fakeMessage = -1):

    s.sendto(createInfoHeader(2), senderInfo)
    newFile = open(f'./received/{message[11:].decode("latin-1")}', 'wb')

    print('---while---')
    while True:
        message = s.recv(1500)
        if message[0] == 8:
            print('prijatý!')
            break

        if fromBytes(message[1:5]) == fakeMessage:
            message += b'\x01'


        while (hashlib.md5(message[:5] + message[21:]).digest() != message[5:21]):
            s.sendto(createInfoHeader(4, fragmentNumber=fromBytes(message[1:5])), senderInfo)
            message = s.recv(1500)
            print(message)

        newFile.write(message[21:])
        s.sendto(createInfoHeader(2, fragmentNumber=fromBytes(message[1:5])), senderInfo)
        print(message)

    return senderInfo

def send(s, ipAddress, port, path, fragmentSize):

    f = open(path, 'rb')
    
    s.sendto(createInfoHeader(1, os.stat(path).st_size, fragmentSize, 0, os.path.basename(f.name)), (ipAddress, port))
    res = s.recv(1500)
    print(res)

    i = 1
    while d := f.read(fragmentSize):
        while True:
            s.sendto(createDataHeader(2, i, d), (ipAddress, port))
            res = s.recv(1500)
            print(res)

            if res[0] == 2:
                break

        i += 1

    f.close()

    s.sendto(createInfoHeader(8), (ipAddress, port))

def getFileInfo():
    return input('Zadajte cestu k súboru: '), int(input('Zadajte fragmentáciu: '))

def getServerInfo():
    return input('Zadajte IP adresu servera: '), int(input('Zadajte port servera: '))


def createSender():
    choice = 0
    serverInfo = tuple()
    fileInfo = tuple()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(60)
    while True:
        if choice == 0:
            serverInfo = getServerInfo()
            fileInfo = getFileInfo()
        send(s, *serverInfo, *fileInfo)


        choice = input()
        if choice == '1':
            keepAlive = KeepAliveSender(s, serverInfo)
            keepAlive.start()
            fileInfo = getFileInfo()
            keepAlive.stop()
            continue
        else:
            s.sendto(createInfoHeader(8), serverInfo)
            choice = input()
            if choice == '1':
                return createReceiver
            if choice == '2':
                exit()
        

def createReceiver():
    port = int(input('Zadajte port, na ktorom bude server počúvať: '))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))
    s.settimeout(60)

    keepAliveBool = False

    while True:

        msg, info = s.recvfrom(1500)

        if msg[0] == 1:
            keepAliveBool = False

            receive(s, msg, info)
            print('tu')

        if msg[0] == 16:
            s.sendto(createInfoHeader(2), info)

            if not keepAliveBool:
                keepAliveBool = True
                
                print('Klient spustil keep alive')

        
        if msg[0] == 8:

            choice = input()
            if choice == '1':
                continue
            if choice == '2':
                port = int(input('Zadajte port, na ktorom bude server počúvať: '))
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(('', port))
                s.settimeout(60)
            if choice == '3':
                return createSender
            if choice == '4':
                exit()
inp = input()


if inp == '1':
    f = createSender
if inp == '2':
    f = createReceiver

while True:
    f = f()





    ##### TODO TODO!!!!
    # - aby sa sender mohol prepnúť na receiver
    # - texty
    # - testy
    # - GUI??? (len ak UI bude neskutočne jednoduché)