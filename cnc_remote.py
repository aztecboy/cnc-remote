

# work of valve-core
from PyQt5 import *
from PyQt5 import QtWidgets,uic

import sys
import os
import bluetooth
import threading
import time
import keyboard
global exit_event
global off_event
global cnc_controller_active_event



class key: # contains the current key value
    pressed_key=""
controller_off_event=threading.Event()
exit_event=threading.Event()
cnc_controller_active_event=threading.Event()


#----gui data

 
class connecting_gui(QtWidgets.QMainWindow): #spawns the connecting window
    def __init__(self):
        super(connecting_gui, self).__init__()
        uic.loadUi("connecting_window.ui",self)
        self.show()
class connecting_error(QtWidgets.QMainWindow): #spawns the connecting error window
    def __init__(self):
        super(connecting_error,self).__init__()
        uic.loadUi("connect_error_window.ui",self)
        self.show()
class timed_out_error(QtWidgets.QMainWindow):
    def __init__(self):
        super(timed_out_error,self).__init__()
        uic.loadUi("timed_out_window.ui",self)
        
class main_gui(QtWidgets.QMainWindow): #spawns the main gui
    def __init__(self):
        super(main_gui,self).__init__()
        uic.loadUi("main_window.ui",self)
        self.on_off_check=self.findChild(QtWidgets.QRadioButton,"on_off")
        self.on_button=self.findChild(QtWidgets.QPushButton,"on")
        self.off_button=self.findChild(QtWidgets.QPushButton,"off")
        self.forward_check=self.findChild(QtWidgets.QRadioButton,"forward")
        self.back_check=self.findChild(QtWidgets.QRadioButton,"back")
        self.spindle_up_check=self.findChild(QtWidgets.QRadioButton,"spindle_up")
        self.spindle_down_check=self.findChild(QtWidgets.QRadioButton,"spindle_down")
        self.spindle_left_check=self.findChild(QtWidgets.QRadioButton,"spindle_left")
        self.spindle_right_check=self.findChild(QtWidgets.QRadioButton,"spindle_right")
        
        
        self.off_button.clicked.connect(controller_off_event.set) 
        
        self.on_button.clicked.connect(lambda:start_cnc_controller_runtime(self,self.socket,self.timed_out_window,self.timed_out_app))
        
        self.socket=None
        self.timed_out_window=None
        self.timed_out_app=None
        self.show()
#----


# a class containing all the methods/functions for handling the connection with the cnc remote
class bluetooth_connection_handler:
       
    class thread_pipe:
        thread_data=[None]*1
        connecting_done=threading.Event()
    class trigger_types: #a class containing all of the trigger types
        button_unpressed_value=0
        button_pressed_value=1
        no_joystick_value=0
        joystick_left_x_value=1
        joystick_left_y_value=2
        joystick_right_x_value=3
        joystick_right_y_value=4
        ping=2
        ping_response=1
    
    class remote_data: #contains data related to the cnc remote
        remote_name="cnc_remote"
    def find_and_connect(connecting_app): # finds the remote address and connects to it, returns a bluetooth socket object into the thread pipe and closes the connecting window
        address=bluetooth_connection_handler.check_if_address_saved()
        if address:
        
            
            #address=bluetooth_connection_handler.find_remote_address()
            socket=bluetooth_connection_handler.connect_to_remote(address)
            if exit_event.is_set():
                quit()
            if socket!=2:
                bluetooth_connection_handler.thread_pipe.thread_data[0]=socket
                bluetooth_connection_handler.thread_pipe.connecting_done.set()
                connecting_app.quit()
                return
            
        address=bluetooth_connection_handler.find_remote_address()
        if exit_event.is_set():
            quit()
        if address=="":
            
            socket=1
            
            bluetooth_connection_handler.thread_pipe.thread_data[0]=socket
            bluetooth_connection_handler.thread_pipe.connecting_done.set()
            connecting_app.quit()
            return 
        
        socket=bluetooth_connection_handler.connect_to_remote(address)
        
        bluetooth_connection_handler.thread_pipe.thread_data[0]=socket
        if socket!=2:
            bluetooth_connection_handler.put_address_into_file(address)
        bluetooth_connection_handler.thread_pipe.connecting_done.set()
        connecting_app.quit()
    def find_remote_address(): # finds the mac address of the cnc remote from its name, returns address
        
        devices = bluetooth.discover_devices(lookup_names = True, lookup_class = True)
       
        address=""
        address_found=False
       
        for mac_address,name,device_class in devices:
            if exit_event.is_set():
                quit()
            if name==bluetooth_connection_handler.remote_data.remote_name:
                address=mac_address
                break
        
        return address
    def connect_to_remote(address): # connects to the remote,returns bluetooth socket
        try:
            socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            socket.connect((address,1))
            socket.settimeout(0.1)
        except bluetooth.btcommon.BluetoothError:
            return 2
        except OSError:
            return 2
        return socket

    def receive_data_from_cnc_remote(socket): #gets the joystick and button data from the cnc remote, returns button state and joystick state
        socket.send(0x01)
        return socket.recv(2)
    
    def connecting_runtime(connecting_app): # starts the connecting window thread
        threading.Thread(target=bluetooth_connection_handler.find_and_connect,args=[connecting_app]).start()
        
    def get_socket(): # gets the socket object out of the thread pipe
        return bluetooth_connection_handler.thread_pipe.thread_data[0]
    # def check_if_connection_thread_done(thread): # returns true if the connection thread is done
    def check_if_address_saved(): # returns the cnc remote address in address.txt, returns False if address.txt doesnt exist
        if os.path.exists("address.txt")!=True:
            return False
        with open("address.txt","r") as file:
            return file.read()
    def put_address_into_file(address): # takes a string and puts it into the address.txt file to be checked before searching for an address
        with open("address.txt","w") as file:
            file.write(address)
   
    def get_and_parse_data(socket,main_window,timed_out_window,timed_out_app):# returns axis and button state from the cnc remote, both are ints

        

        try:
            
            while True:
                data=socket.recv(1)
                if data[0]==1:
                    break
            button_state=socket.recv(1)
            axis=socket.recv(1)
            axis=int.from_bytes(axis,"big")
            if int.from_bytes(button_state,"big")==1:
                button_state=True
            elif int.from_bytes(button_state,"big")==0:
                button_state=False
        
            return button_state,axis
        except OSError: 
            main_window.on_off_check.setChecked(False)
            bluetooth_connection_handler.open_timeout_window(timed_out_window,timed_out_app)
         
            
    def open_timeout_window(timed_out_window,timed_out_app):
        timed_out_window.show()
        timed_out_app.exec()
        quit()


def start_cnc_controller_runtime(main_window,socket,timed_out_window,timed_out_app): #starts the cnc controller thread, takes a qt window object 
    controller_off_event.clear()
    threading.Thread(target=cnc_controller,args=[main_window,socket,timed_out_window,timed_out_app]).start()
    
    main_window.on_off_check.setChecked(True)
    
def all_spindle_checks_off(main_window): # takes the main_window variable, unchecks all spindle directions
    main_window.spindle_left_check.setChecked(False)
    main_window.spindle_right_check.setChecked(False)
    main_window.spindle_down_check.setChecked(False)
    main_window.spindle_up_check.setChecked(False)
    
def all_y_axis_checks_off(main_window): # takes the main_window variable, unchecks all y axis directions
    main_window.forward_check.setChecked(False)
    main_window.back_check.setChecked(False)
def unpress_current_key(): #unpresses the current key
    if key.pressed_key=="forward":
        keyboard.release("up")
        key.pressed_key=""
    elif key.pressed_key=="back":
        keyboard.release("down")
        key.pressed_key=""
    elif key.pressed_key=="spindle_down":
        keyboard.release("page down")
        key.pressed_key=""
    elif key.pressed_key=="spindle_up":
        keyboard.release("page up")
        key.pressed_key=""
    elif key.pressed_key=="spindle_left":
        keyboard.release("left")
        key.pressed_key=""
    elif key.pressed_key=="spindle_right":
        keyboard.release("right")
        key.pressed_key=""
def press_up(): #presses the up key
    if key.pressed_key=="":
        keyboard.press("up")
        key.pressed_key="forward"   
def press_down(): #presses the down key
    if key.pressed_key=="":
        keyboard.press("down")
        key.pressed_key="back" 
def press_page_down(): #presses the page down key
    if key.pressed_key=="":
        keyboard.press("page down")
        key.pressed_key="spindle_down" 
def press_page_up(): #presses the page up key
    if key.pressed_key=="":
        keyboard.press("page up")
        key.pressed_key="spindle_up"
def press_left(): #presses the left key
    if key.pressed_key=="":
        keyboard.press("left")
        key.pressed_key="spindle_left"
def press_right(): #presses the right key
    if key.pressed_key=="":
        keyboard.press("right")
        key.pressed_key="spindle_right"

# the main cnc controller, takes the signals from the remote and sends them to the cnc controller through pyautgui
def cnc_controller(main_window,socket,timed_out_window,timed_out_app):
     
     while True:
        
        if exit_event.is_set():
            unpress_current_key()
            quit()
        if controller_off_event.is_set():
            
            main_window.on_off_check.setChecked(False)
            unpress_current_key()
            quit()
        
        try:
          
            button_state,axis=bluetooth_connection_handler.get_and_parse_data(socket,main_window,timed_out_window,timed_out_app)  
            
            
        except bluetooth.btcommon.BluetoothError:
            
            main_window.on_off_check.setChecked(False)
            
            bluetooth_connection_handler.open_timeout_window(timed_out_window,timed_out_app)
            quit()
        except IndexError:
            continue
        if button_state:
        
            
            all_y_axis_checks_off(main_window)
            if axis==bluetooth_connection_handler.trigger_types.joystick_left_x_value:
                main_window.spindle_down_check.setChecked(True)
                main_window.spindle_up_check.setChecked(False)
                main_window.spindle_left_check.setChecked(False)
                main_window.spindle_right_check.setChecked(False)
                
                press_page_down()
            elif axis==bluetooth_connection_handler.trigger_types.joystick_right_x_value:
                main_window.spindle_down_check.setChecked(False)
                main_window.spindle_up_check.setChecked(True)
                main_window.spindle_left_check.setChecked(False)
                main_window.spindle_right_check.setChecked(False)
                press_page_up()
            
                
            elif axis==bluetooth_connection_handler.trigger_types.joystick_left_y_value:
                main_window.spindle_down_check.setChecked(False)
                main_window.spindle_up_check.setChecked(False)
                main_window.spindle_left_check.setChecked(True)
                main_window.spindle_right_check.setChecked(False)
                press_left()
                
                
                
            elif axis==bluetooth_connection_handler.trigger_types.joystick_right_y_value:
                main_window.spindle_down_check.setChecked(False)
                main_window.spindle_up_check.setChecked(False)
                main_window.spindle_left_check.setChecked(False)
                main_window.spindle_right_check.setChecked(True)
               
                press_right()
            elif axis==bluetooth_connection_handler.trigger_types.no_joystick_value:
                main_window.spindle_down_check.setChecked(False)
                main_window.spindle_up_check.setChecked(False)
                main_window.spindle_left_check.setChecked(False)
                main_window.spindle_right_check.setChecked(False)
                
                unpress_current_key()
                
            
            continue
        else:
            
            all_spindle_checks_off(main_window)
        
        if axis==bluetooth_connection_handler.trigger_types.joystick_left_x_value:
            main_window.back_check.setChecked(True)
            main_window.forward_check.setChecked(False)
            
            press_down()
        
            
        elif axis==bluetooth_connection_handler.trigger_types.joystick_right_x_value:
            main_window.forward_check.setChecked(True)
            main_window.back_check.setChecked(False)
            
            press_up()    
            
        elif axis==bluetooth_connection_handler.trigger_types.no_joystick_value:
            main_window.forward_check.setChecked(False)
            main_window.back_check.setChecked(False)
        
            unpress_current_key()
        
            
        

# the main runtime
def runtime():
    
    connecting_app=QtWidgets.QApplication([])
    connecting_window=connecting_gui()
    bluetooth_connection_handler.connecting_runtime(connecting_app)
    connecting_app.exec()
    connecting_window.close()
    if bluetooth_connection_handler.thread_pipe.connecting_done.is_set()!=True:
        exit_event.set()
        quit()
    socket=bluetooth_connection_handler.get_socket()
    if type(socket)==int:
        error_app=QtWidgets.QApplication([])
        error_window=connecting_error()
        error_app.exec()
        error_window.close()
        error_app.exit()
        
        sys.exit(1)
    main_app=QtWidgets.QApplication([])
    main_window=main_gui()
    main_window.socket=socket
    main_window.timed_out_app=QtWidgets.QApplication([])
    main_window.timed_out_window=timed_out_error()
    
    main_app.exec()
    exit_event.set()
    quit()

    
    
   
    
# executes the main runtime
if __name__=="__main__":
    runtime()


# work of valve-core
