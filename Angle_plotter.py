import dearpygui.dearpygui as dpg
import serial
import serial.tools.list_ports
from collections import deque
import math

serial_connection = None
angle_data = deque(maxlen=2000)
time_data = deque(maxlen=2000)
angle_derivative_data = deque(maxlen=2000)
current_ch1_data = deque(maxlen=2000)
current_ch2_data = deque(maxlen=2000)
raw_current_ch1_data = deque(maxlen=2000)  # Store raw values for RMS calculation
raw_current_ch2_data = deque(maxlen=2000)  # Store raw values for RMS calculation
angle_offset = 0
rms_window_size = 100  # Number of samples for RMS calculation

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
        dpg.add_slider_int(label="Data points", tag="data_points_slider", min_value=100, max_value=10000, default_value=2000, callback=data_points_slider_callback)

        # Angle Offset slider for zeroing the angle
        dpg.add_text("Angle Offset:")
        dpg.add_button(label="Zero Angle", callback=zero_angle_button_callback)

    """
    Console window
    """
    with dpg.window(label="Console", height=499, width=400, pos=(0, 301)):
        dpg.add_child_window(tag="console_window", width=-1, height=564, autosize_x=True, horizontal_scrollbar=False)

    """
    Plot window
    """
    with dpg.window(label="Plots", height=800, width=782, pos=(401, 0)):
        # Angle plot
        with dpg.plot(label="Angle (deg)", height=200, width=755):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_angle")
            dpg.add_plot_axis(dpg.mvYAxis, label="Angle", tag="y_angle")
            dpg.add_line_series([], [], label="Angle", parent="y_angle", tag="angle_series")

        # dAngle/dt plot
        with dpg.plot(label="Angle Derivative", height=200, width=755):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_dangle")
            dpg.add_plot_axis(dpg.mvYAxis, label="dAngle/dt", tag="y_dangle")
            dpg.add_line_series([], [], label="dAngle/dt", parent="y_dangle", tag="deriv_series")

        # Channel 1
        with dpg.plot(label="Channel 1 Current RMS", height=200, width=755):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_ch1")
            dpg.add_plot_axis(dpg.mvYAxis, label="RMS Current (A)", tag="y_ch1")
            dpg.add_line_series([], [], label="Ch1 RMS", parent="y_ch1", tag="ch1_series")

        # Channel 2
        with dpg.plot(label="Channel 2 Current RMS", height=200, width=755):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_ch2")
            dpg.add_plot_axis(dpg.mvYAxis, label="RMS Current (A)", tag="y_ch2")
            dpg.add_line_series([], [], label="Ch2 RMS", parent="y_ch2", tag="ch2_series")

            

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
                        # Decode the serial data
                        time_data.append(float(read_line.split(",")[0]))
                        angle_data.append((float(read_line.split(",")[1]) - angle_offset) % 360)
                        raw_ch1 = float(read_line.split(",")[2])
                        raw_ch2 = float(read_line.split(",")[3])
                        
                        # Store raw current values
                        raw_current_ch1_data.append(raw_ch1)
                        raw_current_ch2_data.append(raw_ch2)
                        
                        # Calculate RMS current over the window
                        rms_ch1 = calculate_rms(raw_current_ch1_data, rms_window_size)
                        rms_ch2 = calculate_rms(raw_current_ch2_data, rms_window_size)

                        print(f"RMS Ch1: {rms_ch1}, RMS Ch2: {rms_ch2}")
                        
                        current_ch1_data.append(rms_ch1)
                        current_ch2_data.append(rms_ch2)
                        
                        dpg.set_value("ch1_series", [list(time_data), list(current_ch1_data)])
                        dpg.set_value("ch2_series", [list(time_data), list(current_ch2_data)])
                        
                        prev_angle = angle_data[-2] if len(angle_data) > 1 else angle_data[-1]
                        prev_time = time_data[-2] if len(time_data) > 1 else time_data[-1]
                        dt = time_data[-1] - prev_time if time_data[-1] != prev_time else 1e-6
                        d_angle = (angle_data[-1] - prev_angle) / dt
                        angle_derivative_data.append(d_angle)
                        dpg.set_value("deriv_series", [list(time_data), list(angle_derivative_data)])   
                    except Exception as e:
                        print(e)
                        continue
                    
                    # If follow newest is enabled, set the x-axis limits to the min and max of the time data
                    follow_toggle = dpg.get_value("follow_newest_toggle")
                    if follow_toggle:
                        if time_data:
                            min_time = min(time_data)
                            max_time = max(time_data)
                            if min_time == max_time:
                                max_time += 1e-3
                            for axis_tag in ("x_angle", "x_dangle", "x_ch1", "x_ch2"):
                                dpg.set_axis_limits(axis_tag, min_time, max_time)
                    else:   # If follow newest is disabled, set the axis limits to auto
                        for axis_tag in ("x_angle", "x_dangle", "x_ch1", "x_ch2"):
                            dpg.set_axis_limits_auto(axis_tag)
                        for axis_tag in ("y_angle", "y_dangle", "y_ch1", "y_ch2"):
                            dpg.set_axis_limits_auto(axis_tag)

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
    global angle_data, time_data, angle_derivative_data, current_ch1_data, current_ch2_data, raw_current_ch1_data, raw_current_ch2_data
    data_points = dpg.get_value("data_points_slider")
    angle_data = deque(maxlen=data_points)
    time_data = deque(maxlen=data_points)
    angle_derivative_data = deque(maxlen=data_points)
    current_ch1_data = deque(maxlen=data_points)
    current_ch2_data = deque(maxlen=data_points)
    raw_current_ch1_data = deque(maxlen=data_points)
    raw_current_ch2_data = deque(maxlen=data_points)

def calculate_rms(data_deque, window_size):
    """Calculate RMS (Root Mean Square) over the last window_size samples"""
    if len(data_deque) == 0:
        return 0.0
    
    # Use the last min(window_size, len(data_deque)) samples
    samples = list(data_deque)[-window_size:]
    
    if len(samples) == 0:
        return 0.0
    
    # Calculate RMS: sqrt(mean(squared values))
    sum_squares = sum(x * x for x in samples)
    mean_square = sum_squares / len(samples)
    rms = math.sqrt(mean_square)
    
    return rms

def zero_angle_button_callback():
    global angle_offset
    raw = serial_connection.readline()
    read_line = raw.decode('utf-8', errors='replace').rstrip("\r\n")
    angle_offset = float(read_line.split(",")[1])
    print(f"Angle offset set to {angle_offset}")

if __name__ == "__main__":
    main()
