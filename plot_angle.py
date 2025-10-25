import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import re
import csv
from datetime import datetime
import time

class ESP32SerialReader:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-C3 Angle Encoder Monitor")

        self.serial_connection = None
        self.running = False
        
        # Data storage for plotting
        self.time_data = []
        self.angle_data = []
        self.max_points = 1000  # Maximum points to keep in memory
        
        # --- GUI Layout ---
        # Create main container
        main_container = ttk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control frame
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill="x", pady=(0, 10))

        # Port selection
        ttk.Label(frame, text="Serial Port:").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=30)
        self.port_combo.grid(row=0, column=1, padx=5)
        self.refresh_ports()

        ttk.Button(frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)

        # Baud rate
        ttk.Label(frame, text="Baud Rate:").grid(row=1, column=0, sticky="w")
        self.baud_var = tk.StringVar(value="115200")
        ttk.Entry(frame, textvariable=self.baud_var, width=10).grid(row=1, column=1, sticky="w")

        # Connect button
        self.connect_button = ttk.Button(frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=2, column=0, columnspan=3, pady=5)

        # Output box
        self.output_box = tk.Text(frame, height=20, width=70, wrap="word")
        self.output_box.grid(row=3, column=0, columnspan=3, pady=5)
        self.output_box.config(state="disabled")

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        if self.serial_connection:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        baud = self.baud_var.get()

        if not port:
            messagebox.showerror("Error", "Please select a serial port.")
            return

        try:
            self.serial_connection = serial.Serial(port, baudrate=int(baud), timeout=1)
            self.running = True
            threading.Thread(target=self.read_serial, daemon=True).start()
            self.connect_button.config(text="Disconnect")
            self.log(f"Connected to {port} at {baud} baud\n")
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))

    def disconnect(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        self.connect_button.config(text="Connect")
        self.log("Disconnected.\n")

    def read_serial(self):
        while self.running and self.serial_connection:
            try:
                line = self.serial_connection.readline().decode(errors="ignore")
                if line:
                    self.log(line)
            except Exception as e:
                self.log(f"Error: {e}\n")
                break

    def log(self, message):
        self.output_box.config(state="normal")
        self.output_box.insert("end", message)
        self.output_box.see("end")
        self.output_box.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32SerialReader(root)
    root.mainloop()
