__author__ = "Jian Wu"
__email__ = "jian.wu@tamu.edu"

from MotionNet import MotionNet
from watch import watchData
import numpy
import heapq
import Tkinter as tk
from UserInterFace import reg_UI
from UserInterFace import reg_UI2
from RegTable import RegTable


DEF_MACADDR = ['2VTX', '2VR7', '2ZX7', '2VN8']
import thread
WATCH_NUM = 4

if __name__ == '__main__':

    # Start smart watch server and start to receive data from all clients.

    UDP_IP = '192.168.0.109'
    UDP_PORT = 4568
    smart_watch = watchData(UDP_IP, UDP_PORT, WATCH_NUM)
    smart_watch.sock_bind()
    thread.start_new_thread(smart_watch.read, ())

    # Start to receive data from MotionNet.
    motion_sensor = MotionNet(6, 115200)
    thread.start_new_thread(motion_sensor.read, ())

    name_list = ["Jian", "William", "Peiming", "Viswam", "Bassem", "Dr.Jafari"]

    root = tk.Tk()
    my_gui = reg_UI(root, name_list)
    root.mainloop()

    table = RegTable(WATCH_NUM)
    while True:
        print table.regTable
        if(reg_UI2.pair_status == True):
            watch_gyro = smart_watch.get_data()
            for i in range(WATCH_NUM):
                if(len(watch_gyro[i]) == 100):
                    watch_data = list(watch_gyro[i])
                    if (numpy.mean(watch_data) > 10):
                        if (len(table.regTable) < WATCH_NUM):
                            table.create_table(reg_UI2.name, DEF_MACADDR[i])
                            reg_UI2.pair_status = False
                        if(len(table.regTable) == WATCH_NUM):
                            table.update_table1(reg_UI2.name)
                            reg_UI2.pair_status = False

        if (reg_UI2.pair_status == False):
            cov_array = [0 for x in range(WATCH_NUM)]
            watch_gyro = smart_watch.get_data()
            MotionNet_gyro = motion_sensor.get_data()
            for i in range(WATCH_NUM):
                if (len(watch_gyro[i]) == 100 and len(MotionNet_gyro) == 100):
                    watch_data = list(watch_gyro[i])
                    motion_data = list(MotionNet_gyro)
                    cov_array[i] = numpy.corrcoef(watch_data, motion_data)[0][1]
            max_value = max(cov_array)
            twolargest = heapq.nlargest(2, cov_array)
            if ((max_value > 0.9) and (abs(twolargest[0] - twolargest[1]) > 0.05)):
                table.unpair(DEF_MACADDR[i])
