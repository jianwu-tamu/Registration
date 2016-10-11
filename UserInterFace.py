___author___ = "Jian Wu"
___email___ = "jian.wu@tamu.edu"

from functools import partial
import Tkinter as tk
from RegTable import RegTable
import numpy
import heapq
import collections
import thread
import socket
import math
import serial
import Queue
import struct

WATCH_NUM = 4
DEF_MACADDR = ['2VTX', '2VR7', '2ZX7', '2VN8']

class reg_UI:

    def __init__(self, master, name_list, motion_queue, watch_queue):
        self.master = master
        self.motion_queue = motion_queue
        self.watch_queue = watch_queue
        master.title("TerraSwarm Registration")
        self.name_list = name_list
        self.menubar = tk.Menu(master)
        self.master.config(menu=self.menubar, height=100, width=400)
        self.name_menu = tk.Menu(self.menubar, tearoff=0)
        for item in self.name_list:
            self.name_menu.add_command(label=item, command=partial(self.pop_window, item))
        self.menubar.add_cascade(label="Presenter Name Select", menu=self.name_menu)
        self.table = RegTable(WATCH_NUM)
        self.lock = thread.allocate_lock()

    def processIncoming(self):
        if (reg_UI2.pair_status == True):
            for i in range(WATCH_NUM):
                self.lock.acquire()
                if (len(self.watch_queue[i]) == 100):
                    watch_data = list(self.watch_queue[i])
                    self.lock.release()
                    if (numpy.mean(watch_data) > 10):
                        if (len(self.table.regTable) < WATCH_NUM):
                            self.table.create_table(reg_UI2.name, DEF_MACADDR[i])
                            reg_UI2.pair_status = False
                        elif (len(self.table.regTable) == WATCH_NUM):
                            self.table.update_table1(reg_UI2.name)
                            reg_UI2.pair_status = False


        if (reg_UI2.pair_status == False):
            cov_array = [0 for x in range(WATCH_NUM)]
            self.lock.acquire()
            watch_gyro = self.watch_queue
            MotionNet_gyro = self.motion_queue
            self.lock.release()
            for i in range(WATCH_NUM):
                if (len(watch_gyro[i]) == 100 and len(MotionNet_gyro) == 100):
                    watch_data = list(watch_gyro[i])
                    motion_data = list(MotionNet_gyro)
                    cov_array[i] = numpy.corrcoef(watch_data, motion_data)[0][1]
            max_value = max(cov_array)
            max_index = cov_array.index(max_value)
            twolargest = heapq.nlargest(2, cov_array)
            if ((max_value > 0.9) and (abs(twolargest[0] - twolargest[1]) > 0.05)):
                self.table.unpair(DEF_MACADDR[max_index])

    def pop_window(self, name):
        self.window = tk.Toplevel(self.master)
        self.app = reg_UI2(self.window, name)

class reg_UI2:

    pair_status = False
    name = " "

    def __init__(self, master, name):
        reg_UI2.name = name
        self.master = master
        var = "You are registrating as " + name
        self.text = tk.Message(self.master, text=var)
        self.text.pack()
        self.confirm_button = tk.Button(self.master, text="confirm")
        self.confirm_button.pack()
        self.confirm_button.bind('<Button-1>', self.update_table)
        self.cancel_button = tk.Button(self.master, text="cancel", command=self.close_windows)
        self.cancel_button.pack()

    def close_windows(self):
        self.master.destroy()
        return

    def update_table(self, event):
        reg_UI2.pair_status = True
        self.master.destroy()
        return


class ThreadedClient:

    def __init__(self, master):
        self.name_list = ["Jian", "William", "Peiming", "Viswam", "Bassem", "Dr.Jafari"]
        self.master = master
        self.watch_queue = [collections.deque(maxlen=100) for x in range(WATCH_NUM)]
        self.motion_queue = collections.deque(maxlen=100)
        self.gui = reg_UI(master, self.name_list, self.motion_queue, self.watch_queue)

        # Start smart watch server and start to receive data from all clients.
        UDP_IP = '192.168.0.109'
        UDP_PORT = 4568
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        thread.start_new_thread(self.read_watch, ())

        # Start to receive data from MotionNet.
        self.serial = serial.Serial("COM6", 115200, timeout=5)
        self.data = [0 for x in range(50)]
        self.data_package = Queue.Queue(maxsize=50)
        self.parsed_data = [0 for x in range(6)]
        thread.start_new_thread(self.read_motion, ())
        self.lock = thread.allocate_lock()
        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming()
        self.master.after(50, self.periodicCall)

    def read_watch(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            parsed_data = data.split(' ')
            if (parsed_data[2] == '3'):
                gyro_x = float(parsed_data[3])
                gyro_y = float(parsed_data[4])
                gyro_z = float(parsed_data[5])
                gyro_mag = math.sqrt(gyro_x * gyro_x + gyro_y * gyro_y + gyro_z * gyro_z) * 57.3
                for i in range(WATCH_NUM):
                    if (parsed_data[0] == DEF_MACADDR[i]):
                        self.lock.acquire()
                        self.watch_queue[i].append(gyro_mag)
                        self.lock.release()

    def read_motion(self):
        while True:
            while (self.data_package.qsize() < 50):
                self.data_package.put(self.serial.read(1))
            i = 1
            while (i == 1):
                self.data[0] = self.data_package.get()
                if (ord(self.data[0]) == 16):
                    self.data[1] = self.data_package.get()
                    if (ord(self.data[1]) == 1):
                         j = 1
                         k = 2
                         while (j == 1):
                            self.data[k] = self.data_package.get()
                            if (ord(self.data[k]) == 16):
                                self.data[k + 1] = self.data_package.get()
                                if (ord(self.data[k + 1]) == 4):
                                    j = 0
                                    i = 0
                            k = k + 1
            for l in range(1, 7):
                datastr = self.data[l*2] + self.data[l*2 + 1]
                self.parsed_data[l-1] = struct.unpack(">h", datastr)[0]
            gyro_x = self.parsed_data[3]/32.75
            gyro_y = self.parsed_data[4]/32.75
            gyro_z = self.parsed_data[5]/32.75

            gyro_mag = math.sqrt(gyro_x*gyro_x + gyro_y*gyro_y + gyro_z*gyro_z)
            self.lock.acquire()
            self.motion_queue.append(gyro_mag)
            self.lock.release()

if __name__ == "__main__":
    root = tk.Tk()
    client = ThreadedClient(root)
    root.mainloop()


