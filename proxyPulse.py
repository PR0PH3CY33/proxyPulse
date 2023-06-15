
#Written by Antoine Zayyat 15-06-2023 Licensed under the GNU General Public License

try:

    import sys

    import socket

    import threading

    import select

except ImportError as ie:

    print(ie)


def get_available_methods(nmethods, connection):

    methods = []

    for i in range(nmethods):

        methods.append(ord(connection.recv(1)))
        
    return methods


def validateCredentials(clientSocket):

        validUsername = "root"

        validPassword = "root"

        version = ord(clientSocket.recv(1))

        username_len = ord(clientSocket.recv(1))

        username = clientSocket.recv(username_len).decode('utf-8')

        password_len = ord(clientSocket.recv(1))

        password = clientSocket.recv(password_len).decode('utf-8')

        if(username == validUsername and password == validPassword):

            resp = b"\x05\x00"

            clientSocket.send(resp)

        else:

            resp = b"\x05\xff"

            clientSocket.send(resp)

            clientSocket.close()

            return False


def exchangeLoop(client, remote):

        while True:
            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break




def handle_client(clientSocket):

    protocolVersion, protocolMethods = clientSocket.recv(2)

    methods = get_available_methods(protocolMethods, clientSocket)

    if(2 in methods):

        initialResponse = b"\x05\x02"

        clientSocket.send(initialResponse)

        validation = validateCredentials(clientSocket)

        if(validation == False):

            return
        
        else:

            version, cmd, _, address_type = clientSocket.recv(4)

            if(address_type == 1):

                address = socket.inet_ntoa(clientSocket.recv(4))
                
                port = int.from_bytes(clientSocket.recv(2), 'big', signed=False)

                try:

                    if(cmd == 1):

                        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        
                        remote.connect((address, port))
                                                
                        print("* Connected to {} {}".format(address, port))

                    else:

                        clientSocket.close()

                    SOCKS_VERSION = 5

                    reply = b''.join([

                    SOCKS_VERSION.to_bytes(1, 'big'),
                    
                        int(0).to_bytes(1, 'big'),
                        
                        int(0).to_bytes(1, 'big'),
                        
                        int(1).to_bytes(1, 'big'),
                        
                        socket.inet_aton(address),
                        
                        port.to_bytes(2, 'big')
                    
                    ])

                    clientSocket.sendall(reply)

                    if(cmd == 1):

                        exchangeLoop(clientSocket, remote)

                        clientSocket.close()

                except Exception as e:

                    print(e)




def main():

    host = "0.0.0.0"

    port = 8119

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((host, port))

    s.listen(10)

    print("Listen on " + str(host) + " on port " + str(port))

    while True:

        clientSocket, clientAddress= s.accept()

        client_thread = threading.Thread(target=handle_client, args=(clientSocket,))

        client_thread.start()



main()