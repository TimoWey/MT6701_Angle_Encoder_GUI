import dearpygui.dearpygui as dpg
import serial
import serial.tools.list_ports
from collections import deque

serial_connection = None
angle_data = deque(maxlen=100)
time_data = deque(maxlen=100)

def main():
    global serial_connection

    dpg.create_context()
    dpg.create_viewport(title='A Million Times Clock - Angle Plotter', width=1200, height=840)
    dpg.setup_dearpygui()

    """ 
    Configuration window
    """
    with dpg.window(label="Configuration", height=300, width=400, pos=(0, 0)):
        dpg.add_text("Serial Port:")
        ports = [p.device for p in serial.tools.list_ports.comports()]
        dpg.add_combo(items=ports, width=100, tag="COM_port", default_value="COM5")

        dpg.add_text("Baud Rate:")
        dpg.add_combo(items=[115200, 9600, 19200, 38400, 57600, 115200], width=100, tag="baud_rate", default_value="115200")

        dpg.add_button(label="Connected", width=100, callback=connection_button_callback, tag="connection_button")
        
        # Follow newest toggle
        dpg.add_text("Plot Settings:")
        dpg.add_checkbox(label="Follow newest", tag="follow_newest_toggle", default_value=True)
        dpg.add_slider_int(label="Data points", tag="data_points_slider", min_value=10, max_value=10000, default_value=1000, callback=data_points_slider_callback)

    """
    Console window
    """
    with dpg.window(label="Console", height=499, width=400, pos=(0, 301)):
        dpg.add_child_window(tag="console_window", width=-1, height=564, autosize_x=True, horizontal_scrollbar=False)

    """
    Plot window
    """
    with dpg.window(label="Plot", height=800, width=782, pos=(401, 0)):
        with dpg.plot(label="Angle Plot", height=765, width=755):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Angle", tag="y_axis")
            dpg.set_axis_limits(dpg.last_item(), -10, 370)
            dpg.add_line_series(list(time_data), list(angle_data), label="Angle", parent="y_axis", tag="angle_series")
            dpg.add_plot_legend()
    
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
                    try:
                        angle_data.append(float(read_line.split(",")[1]))
                        time_data.append(float(read_line.split(",")[0]))
                    except Exception as e:
                        print(e)
                        continue
                    
                    # If follow newest is enabled, set the x-axis limits to the min and max of the time data
                    follow_toggle = dpg.get_value("follow_newest_toggle")
                    if follow_toggle:
                        dpg.set_axis_limits("x_axis", min(time_data), max(time_data))
                    else:   # If follow newest is disabled, set the x-axis limits to auto
                        dpg.set_axis_limits_auto("x_axis")
                        dpg.set_axis_limits_auto("y_axis")

                    dpg.set_value("angle_series", [list(time_data), list(angle_data)])
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

def data_points_slider_callback():
    global angle_data, time_data
    data_points = dpg.get_value("data_points_slider")
    angle_data = deque(maxlen=data_points)
    time_data = deque(maxlen=data_points)

if __name__ == "__main__":
    main()
