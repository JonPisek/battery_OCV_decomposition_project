import tkinter as tk
from tkinter import Label, Entry, filedialog, IntVar, Checkbutton, Scale, Button  # noqa: E501
from PIL import Image, ImageTk
from optimization_functions import perform_full_optimization_parallel_to_json_GUI  # noqa: E501
from optimization_functions import perform_full_optimization_parallel
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OCVBatteryDecompositionGUI:
    def __init__(self, master):
        self.master = master
        master.title("OCV Battery Decomposition")
        master.geometry("1400x800")
        self.default_cathode_loc = "data/cathode_data"
        self.default_anode_loc = "data/anode_data"
        self.default_battery_loc = "data/battery_data.txt"
        self.cathode_loc = self.default_cathode_loc
        self.anode_loc = self.default_anode_loc
        self.battery_loc = self.default_battery_loc
        self.interpolated_cathodes = add_half_cell_data(self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(self.anode_loc)
        self.SOC_battery = None
        self.OCV_battery = None
        self.left_frame = tk.Frame(master, width=400)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.create_file_location_entries()
        self.create_input_widgets()
        self.run_button = tk.Button(
            self.left_frame, text="Run Optimization",
            command=self.run_optimization, width=20)
        self.run_button.pack(pady=10)
        self.download_button = Button(
            self.left_frame, text="Download Result",
            command=self.download_result, width=20)
        self.result_label = None
        self.plot = self.create_empty_plot()
        self.plot.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH, expand=True)
        self.add_image()

    def create_file_location_entries(self):
        self.label_cathode_loc = Label(
            self.left_frame, text="Cathode Folder Location:",
            font=("Arial", 12))
        self.label_cathode_loc.pack()
        self.entry_cathode_loc = Entry(self.left_frame, width=50,
                                       font=("Arial", 12))
        self.entry_cathode_loc.insert(0, self.default_cathode_loc)
        self.entry_cathode_loc.pack()
        self.label_anode_loc = Label(
            self.left_frame, text="Anode Folder Location:",
            font=("Arial", 12))
        self.label_anode_loc.pack()
        self.entry_anode_loc = Entry(self.left_frame, width=50,
                                     font=("Arial", 12))
        self.entry_anode_loc.insert(0, self.default_anode_loc)
        self.entry_anode_loc.pack()
        self.label_battery_loc = Label(
            self.left_frame, text="Battery File Location:",
            font=("Arial", 12))
        self.label_battery_loc.pack()
        self.entry_battery_loc = Entry(self.left_frame, width=50,
                                       font=("Arial", 12))
        self.entry_battery_loc.insert(0, self.default_battery_loc)
        self.entry_battery_loc.pack()
        self.browse_button = tk.Button(
            self.left_frame, text="Browse", command=self.browse_files,
            font=("Arial", 12))
        self.browse_button.pack()

    def create_input_widgets(self):
        self.label_iterations = Label(
            self.left_frame, text="Iterations:",
            font=("Arial", 12))
        self.label_iterations.pack()
        self.iterations_var = IntVar()
        self.scale_iterations = Scale(
            self.left_frame, from_=1, to=5, orient=tk.HORIZONTAL,
            variable=self.iterations_var, length=200)
        self.scale_iterations.set(5)
        self.scale_iterations.pack()
        self.label_binary_params = Label(
            self.left_frame, text="Binary Optimization Parameters:",
            font=("Arial", 12))
        self.label_binary_params.pack()
        self.battery_var = IntVar(value=1)
        self.check_battery = Checkbutton(
            self.left_frame, text="Battery", variable=self.battery_var)
        self.check_battery.pack()
        self.anode_var = IntVar(value=0)
        self.check_anode = Checkbutton(
            self.left_frame, text="Anode", variable=self.anode_var)
        self.check_anode.pack()
        self.cathode_var = IntVar(value=0)
        self.check_cathode = Checkbutton(
            self.left_frame, text="Cathode", variable=self.cathode_var)
        self.check_cathode.pack()
        self.derivative_var = IntVar(value=0)
        self.check_derivative = Checkbutton(
            self.left_frame, text="Derivative Inverse",
            variable=self.derivative_var)
        self.check_derivative.pack()

    def browse_files(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")])
        if file_path:
            current_entry = self.entry_battery_loc
            current_entry.delete(0, tk.END)
            current_entry.insert(0, file_path)

    def run_optimization(self):
        iterations = self.iterations_var.get()
        battery = self.battery_var.get()
        anode = self.anode_var.get()
        cathode = self.cathode_var.get()
        derivative_inverse = self.derivative_var.get()
        self.cathode_loc = self.entry_cathode_loc.get(
        ) or self.default_cathode_loc
        self.anode_loc = self.entry_anode_loc.get(
        ) or self.default_anode_loc
        self.battery_loc = self.entry_battery_loc.get(
        ) or self.default_battery_loc
        self.interpolated_cathodes = add_half_cell_data(
            self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(
            self.anode_loc)
        self.SOC_battery, self.OCV_battery = load_soc_ocv_data(
            self.battery_loc)
        result = perform_full_optimization_parallel(
            self.SOC_battery, self.OCV_battery,
            self.interpolated_cathodes, self.interpolated_anodes,
            iterations=iterations, battery=battery, anode=anode,
            cathode=cathode, derivative_inverse=derivative_inverse
        )

        if result['calculated_battery_OCV_opt'] is not None:
            self.plot_results(result)
            data_label_text = (
                f"Best Cathode Data ID: {result['Best Cathode Data ID']}\n"
                f"Best Anode Data ID: {result['Best Anode Data ID']}\n"
                f"Best Parameters: {result['Best Parameters']}\n"
                f"Lowest RMSD: {result['Lowest RMSD']}"
            )
            if self.result_label:
                self.result_label.destroy()
            self.result_label = Label(self.left_frame, text=data_label_text,
                                      font=("Arial", 12))
            self.result_label.pack(pady=10)
            self.download_button.pack_forget()
            self.download_button.pack(pady=10)
        else:
            print("Interpolation for the best cathode or anode failed.")

    def download_result(self):
        result_filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if result_filename:
            perform_full_optimization_parallel_to_json_GUI(
                result_filename, self.SOC_battery, self.OCV_battery,
                self.interpolated_cathodes, self.interpolated_anodes,
                iterations=self.iterations_var.get(),
                battery=self.battery_var.get(),
                anode=self.anode_var.get(),
                cathode=self.cathode_var.get(),
                derivative_inverse=self.derivative_var.get()
            )
            print("Result downloaded successfully.")
            self.download_button.pack_forget()

    def plot_results(self, result):
        if self.plot is None:
            self.plot = FigureCanvasTkAgg(
                plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(
                side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.plot.get_tk_widget().destroy()
            self.plot = FigureCanvasTkAgg(
                plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(
                side=tk.TOP, fill=tk.BOTH, expand=True)

        plt.plot(
            self.SOC_battery, self.OCV_battery,
            'r-', label='Measured battery OCV')
        plt.plot(
            self.SOC_battery, result['calculated_battery_OCV_opt'],
            'b-', label='Optimized Battery OCV')
        plt.plot(
            result['c_SOC_full'], result['r1_ns_x_c1_ns'], 'r--')
        plt.plot(
            result['c_SOC'], result['r1_x_c1'],
            'g-', label='Optimized Cathode OCP')
        plt.plot(result['a_SOC_full'], result['w1_ns_x_a1_ns'], 'r--')
        plt.plot(
            result['a_SOC'], result['w1_x_a1'],
            'k-', label='Optimized Anode OCP')
        plt.title("Optimization")
        plt.xlabel('SOC (% / 100)')
        plt.ylabel('OCV (V)')
        plt.grid(True)
        plt.legend()

    def create_empty_plot(self):
        empty_fig = plt.figure(figsize=(8, 6))
        empty_plot = FigureCanvasTkAgg(empty_fig, master=self.right_frame)
        return empty_plot

    def add_image(self):
        img = Image.open("LICEM/logo.jpg")
        photo = ImageTk.PhotoImage(img)
        img_label = Label(self.left_frame, image=photo)
        img_label.image = photo
        img_label.pack(side=tk.BOTTOM, padx=10, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    gui = OCVBatteryDecompositionGUI(root)
    root.mainloop()
