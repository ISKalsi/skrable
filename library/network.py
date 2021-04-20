import socket
import struct
from threading import Thread, Lock
import json
import traceback
from abc import abstractmethod


class Network:
    header = 4096
    format = 'utf-8'
    interval = 0.1

    SUCCESS = 200
    FAIL = 400
    EXIT = 600
    DISCONNECT = 800
    WAIT = 1000
    ABORT = 1200

    def __init__(self):
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 8420

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = Lock()

        self.__exitCode = self.DISCONNECT

    @property
    def address(self):
        return self.host, self.port

    @address.setter
    def address(self, new: tuple):
        self.host, self.port = new

    @staticmethod
    def __recvall(sock, count):
        buf = b''
        while count:
            newBuf = sock.recv(count)
            if not newBuf:
                return None
            buf += newBuf
            count -= len(newBuf)
        return buf

    @staticmethod
    def _recv_one_message(sock):
        lengthBuf = Network.__recvall(sock, 4)
        length, = struct.unpack('!I', lengthBuf)
        return Network.__recvall(sock, length)

    @staticmethod
    def _send_one_message(sock, data):
        length = len(data)
        sock.sendall(struct.pack('!I', length))
        sock.sendall(data)


class Server(Network):
    def __init__(self):
        super(Server, self).__init__()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.address)

        self.clientN = 0
        self.clientLocks = {}

    @abstractmethod
    def processData(self, data, conn, addr):
        """
        override this function in the child class.

        :param data: msg received from client
        :type data: Any
        :param conn: socket object
        :type conn: socket.socket
        :param addr: (host, port)
        :type addr: tuple[str, int]
        :return: do anything you like with this data
        :rtype: Any
        """
        return data

    def __handleClient(self, conn, addr):
        print("\n[NEW CONNECTION]", addr)

        while True:
            byteData = None
            data = None
            # obj = None
            # msg = None
            # raised = True

            # noinspection PyBroadException
            try:
                with self.clientLocks[addr]:
                    byteData = Network._recv_one_message(conn)
                data = byteData.decode(self.format)

                obj = json.loads(data) if data is not None else None
                msg = self.processData(obj, conn, addr)

                if msg == self.ABORT:
                    continue

                if msg is not None:
                    jsonObject = json.dumps(msg)
                    byteObject = jsonObject.encode(self.format)
                    with self.clientLocks[addr]:
                        Network._send_one_message(conn, byteObject)
                else:
                    msg = ""
                    jsonObject = json.dumps(msg)
                    byteObject = jsonObject.encode(self.format)
                    with self.clientLocks[addr]:
                        Network._send_one_message(conn, byteObject)
                # raised = False
            except KeyboardInterrupt:
                print("Closing server...")
                break
            except json.JSONDecodeError:
                print("\n")
                print("byteData:", byteData)
                print("data:", data)

                print("error:", traceback.print_exc())
                break
            # except Exception:
            #     print("\n")
            #     print("obj:", obj)
            #     print("msg:", msg)
            #     print("error:", traceback.print_exc(-1))
            # finally:
            #     if raised:
            #         break

        conn.close()
        self.clientN -= 1
        print("[CONNECTION CLOSED]", addr, end='\n\n')

    def _requestClient(self, conn):
        byteData = None
        data = None

        try:
            byteData = Network._recv_one_message(conn)
            data = byteData.decode(self.format)
            msg = json.loads(data)

            if msg == self.FAIL:
                raise Exception("Failure triggered from server")

            return msg
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        except UnicodeDecodeError:
            print("\n")
            print("byteData:", byteData)

            print("error:", traceback.print_exc())
        except json.JSONDecodeError:
            print("\n")
            print("byteData:", byteData)
            print("data:", data)

            print("error:", traceback.print_exc())
        # except Exception as e:
        #     print(e)

    def _sendToClient(self, conn, msg):
        try:
            jsonObject = json.dumps(msg)
            byteObject = jsonObject.encode(self.format)
            Network._send_one_message(conn, byteObject)
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        # except Exception as e:
        #     print(e)

    def run(self):
        self.sock.listen()
        print("[SERVER STARTED] ", self.address, end='\n\n')

        try:
            while True:
                conn, addr = self.sock.accept()
                self.clientN += 1
                self.clientLocks[addr] = Lock()

                Thread(
                    name=f"[{conn}, {addr}]",
                    target=self.__handleClient,
                    args=(conn, addr),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            print("\nClosing server...")

    def __del__(self):
        self.sock.close()
        print("[SERVER CLOSED]")


class Client(Thread, Network):
    def __init__(self):
        Thread.__init__(self, daemon=True)
        Network.__init__(self)

        self.__sendMsg = None
        self.__msgReceived = None

    def __requestServer(self):
        try:
            data = Network._recv_one_message(self.sock)
            msg = json.loads(data.decode(self.format))

            if msg == self.FAIL:
                raise Exception("Failure triggered from server")

            self.__msgReceived = msg
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        # except Exception as e:
        #     print(e)

    def __sendToServer(self):
        try:
            jsonObject = json.dumps(self.__sendMsg)
            byteObject = jsonObject.encode(self.format)
            Network._send_one_message(self.sock, byteObject)
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        # except Exception as e:
        #     print(e)

    def _sendMsg(self, msg):
        self.__sendMsg = msg
        self.__sendToServer()

    def _receiveMsg(self):
        self.__requestServer()
        return self.__msgReceived

    def _establishConnection(self):
        self.sock.connect(self.address)

    def _disconnect(self):
        self.__exitCode = self.DISCONNECT

    def _exit(self):
        self.__exitCode = self.EXIT

    def __del__(self):
        self.sock.close()
        print("[CLIENT EXITED]")
