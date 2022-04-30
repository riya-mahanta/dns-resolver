import json
import socket
import argparse
import datetime
import sys
import time
import threading
import traceback
import socketserver
import struct
import glob
import json
import byte as byte
import dns.query
import dns.message

port = 53
ip = '127.0.0.1'
# socket.SOCK_GRAM - tells python we are using UDP instead of TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# since socket.bin() takes only one argument, we create a tuple - one parameter consisting of 2 param inside
sock.bind((ip, port))


def loadZone():
    jsonZone = {}
    zoneFiles = glob.glob('zones/*.zone')
    for zone in zoneFiles:
        with open(zone) as zoneData:
            data = json.load(zoneData)
            zoneName = data["$origin"]
            jsonZone[zoneName] = data
    return jsonZone


zonedata = loadZone()


def getflags(flags):
    byte1 = byte(flags[:1])
    byte2 = byte(flags[1:2])
    # response flag
    QR = '1'
    OPCODE = ''
    for bit in range(1, 5):
        OPCODE += str(ord(byte1) & (1 << bit))
    AA = '1'
    TC = '0'
    RD = '0'
    RA = '0'
    Z = '000'
    RCODE = '0000'
    return int(QR + OPCODE + AA + TC + RD, 2).to_bytes(1, byteorder="big") + int(RA + Z + RCODE, 2).to_bytes(1,
                                                                                                             byteorder='big')


def getQuestionDomain(data):
    state = 0
    expectedLength = 0
    domainString = ''
    domainParts = []
    x = 0
    y = 0
    for byte in data:
        if state == 1:
            if byte != 0:
                domainString = chr(byte)
            x += 1
            if x == expectedLength:
                domainParts.append(domainString)
                domainString = ''
                state = 0
                x = 0
            if byte == 0:
                domainParts.append(domainString)
                break
        else:
            state = 1
            expectedLength = byte
        y += 1

    questionType = data[y:y + 2]
    return (domainParts, questionType)


def getZone(domain):
    global zonedata
    zone_name = '.'.join(domain)
    return zonedata[zone_name]


def getrecs(data):
    domain, questionType = getQuestionDomain(data)
    qt = ''
    if questionType == b'\x00\x01':
        qt = 'a'

    zone = getZone(domain)
    return (zone[qt], qt, domain)


def buildquestion(domainName, recType):
    qbytes = b''
    for part in domainName:
        length = len(part)
        qbytes += bytes([length])
        for char in part:
            qbytes += ord(char).to_bytes(1, byteorder='big')
    if recType == 'a':
        qbytes += (1).to_bytes(2, byteorder='big')
    qbytes += (1).to_bytes(2, byteorder='big')
    return qbytes


def recToBytes(domainName, recType, recTTL, recValue):
    rbytes = b'\xc0\x0c'
    if recType == 'a':
        rbytes = rbytes + bytes([0]) + bytes([1])
    rbytes = rbytes + bytes([0]) + bytes([1])
    rbytes += int(recTTL).to_bytes(4, byteorder='big')
    if recType == 'a':
        rbytes = rbytes + bytes([0]) + bytes([4])
        for part in recValue.split('.'):
            rbytes += bytes([int(part)])
    return rbytes


def buildresponse(data):
    # Transaction ID
    TransactionID = data[:2]  # recieveing first two bytes

    print(data)

    # Get flags
    Flags = getflags(data[2:4])

    # Question Count
    QDCOUNT = b'\x00\x01'

    # Answer Count
    # getQuestionDomain(data[12:])

    answerCount = (len(getrecs(data[12:])[0])).to_bytes(2, byteorder='big')

    # Name Server Count
    nameServerCount = (0).to_bytes(2, byteorder='big')

    # Additional Count
    additionalCount = (0).to_bytes(2, byteorder='big')

    DNSHeader = TransactionID + Flags + QDCOUNT + answerCount + nameServerCount + additionalCount

    # Create DNS body
    DNSBody = b''

    # Get Answer for query
    records, recType, domainName = getrecs(data[12:])

    DNSQuestion = buildquestion(domainName, recType)

    for record in records:
        DNSBody += recToBytes(domainName, recType, record["ttl"], record["value"])

    return DNSHeader + DNSQuestion + DNSBody


def main():
    #data, addr = sock.recvfrom(512)
    #print(data)
    data = input('Enter domin: ')
    r = buildresponse(data)
    #sock.sendto(b'Hello World', addr)



main()