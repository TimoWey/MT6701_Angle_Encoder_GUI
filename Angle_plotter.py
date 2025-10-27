import dearpygui.dearpygui as dpg
import serial
import serial.tools.list_ports

serial_connection = None

def main():
    global serial_connection

    dpg.create_context()
    dpg.create_viewport(title='A Million Times Clock - Angle Plotter', width=1200, height=840)
    dpg.setup_dearpygui()

    """ 
    Connection window
    """
    with dpg.window(label="Connection", height=200, width=400, pos=(0, 0)):
        dpg.add_text("Serial Port:")
        ports = [p.device for p in serial.tools.list_ports.comports()]
        dpg.add_combo(items=ports, width=100, tag="COM_port", default_value="COM5")

        dpg.add_text("Baud Rate:")
        dpg.add_combo(items=[115200, 9600, 19200, 38400, 57600, 115200], width=100, tag="baud_rate", default_value="115200")

        dpg.add_button(label="Connected", width=100, callback=connection_button_callback, tag="connection_button")

    """
    Console window
    """
    with dpg.window(label="Console", height=600, width=400, pos=(0, 200)):
        dpg.add_child_window(tag="console_window", width=-1, height=565, autosize_x=True, horizontal_scrollbar=False)

    """
    Plot window
    """
    with dpg.window(label="Plot", height=600, width=400, pos=(400, 0)):
        pass
    
    """
    Main loop
    """
    dpg.show_viewport()
    while dpg.is_dearpygui_running():
        if serial_connection and serial_connection.is_open:
            if serial_connection.in_waiting:
                raw = serial_connection.readline()
                read_line = raw.decode('utf-8', errors='replace').rstrip("\r\n")
                if read_line:
                    dpg.add_text(read_line, parent="console_window")
                    dpg.set_y_scroll("console_window", dpg.get_y_scroll_max("console_window"))
        dpg.render_dearpygui_frame()

    dpg.destroy_context()

def connection_button_callback():
    global serial_connection

    if dpg.get_item_label("connection_button") == "Connected":
        serial_connection = serial.Serial(dpg.get_value("COM_port"), baudrate=int(dpg.get_value("baud_rate")), timeout=1)
        dpg.set_item_label("connection_button", "Disconnected")
        print(f"Connected to {dpg.get_value('COM_port')} at {dpg.get_value('baud_rate')} baud")
    elif dpg.get_item_label("connection_button") == "Disconnected":
        serial_connection.close()
        serial_connection = None
        dpg.set_item_label("connection_button", "Connected")
        print("Disconnecting from serial port")

if __name__ == "__main__":
    main()
