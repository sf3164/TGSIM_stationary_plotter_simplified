#simplified version
import pandas as pd
import plotly.graph_objects as go
import os
import matplotlib.colors as mcolors
import tkinter as tk
from tkinter import ttk, messagebox

# File Paths
TRAJECTORY_FILE = "TGSIM_Stationary.csv"
CENTERLINE_FOLDER = "Centerline"

# Load trajectory data
traj_df = pd.read_csv(TRAJECTORY_FILE)

# Initialize main window
root = tk.Tk()
root.title("Simplified Vehicle Plotter")

selected_run = tk.StringVar()

# ---- Plotting Function ----
def plot_selected_vehicles():
    try:
        run_index = int(selected_run.get())
        input_text = vehicle_entry.get().strip()

        if not input_text:
            raise ValueError("No vehicle IDs provided.")
        
        # Get data for selected run
        run_data = traj_df[traj_df["run_index"] == run_index]
        if run_data.empty:
            raise ValueError(f"No data for Run {run_index}.")

        # Compute the max ranges
        max_x = traj_df[(traj_df["run_index"] == run_index)]['xloc_kf'].max()
        max_y = traj_df[(traj_df["run_index"] == run_index)]['yloc_kf'].max()

        # Parse and validate vehicle IDs
        input_ids = input_text.split(",")
        vehicle_ids = []
        invalid_format = []
        not_found = []

        for vid in input_ids:
            vid = vid.strip()
            if not vid.isdigit():
                invalid_format.append(vid)
            else:
                vid_int = int(vid)
                if vid_int not in run_data["id"].unique():
                    not_found.append(vid)
                else:
                    vehicle_ids.append(vid_int)

        # Raise combined error if any problems
        if invalid_format or not_found:
            error_msg = ""
            if invalid_format:
                error_msg += f"❌ Invalid format (not numeric): {', '.join(invalid_format)}\n"
            if not_found:
                error_msg += f"❌ Not found in Run {run_index}: {', '.join(not_found)}"
            raise ValueError(error_msg)

        # Filter trajectory
        filtered_traj = run_data[run_data["id"].isin(vehicle_ids)]

        # Load centerline
        centerline_file = os.path.join(CENTERLINE_FOLDER, f"I-90-stationary-Run_{run_index}-geometry-with-ramps.csv")
        if not os.path.exists(centerline_file):
            raise FileNotFoundError(f"Missing centerline: {centerline_file}")
        
        centerline_df = pd.read_csv(centerline_file)

        # Plotting
        color_list = list(mcolors.TABLEAU_COLORS.values())
        fig = go.Figure()

        # Plot all lane centerlines
        # Plot all lane centerlines
        for lane in centerline_df.columns:
            if lane.startswith("x_"):  # Identify lane columns
                lane_number = lane.split("_")[1]  # Extract lane ID
                lane_centerline_column_x = f"x_{lane_number}"
                lane_centerline_column_y = f"y_{lane_number}"
                
                if lane_centerline_column_x in centerline_df.columns and lane_centerline_column_y in centerline_df.columns:
                    lane_centerline = centerline_df[[lane_centerline_column_x, lane_centerline_column_y]].dropna()
        
                    fig.add_trace(go.Scatter(
                        x=lane_centerline.iloc[:, 0], 
                        y=lane_centerline.iloc[:, 1], 
                        mode="lines", 
                        line=dict(color="#D3D3D3", width=1.5),
                        name=f"Lane {lane_number}"
                    ))
        
                    # Add lane ID label at the end of the centerline
                    end_x, end_y = lane_centerline.iloc[-1, 0], lane_centerline.iloc[-1, 1]
                    fig.add_trace(go.Scatter(
                        x=[end_x], 
                        y=[end_y], 
                        mode="text", 
                        text=[f"Lane {lane_number}"], 
                        textposition="top center",
                        textfont=dict(color="black", size=10),
                        showlegend=False
                    ))

        # Plot each vehicle
        for i, vid in enumerate(vehicle_ids):
            veh_data = filtered_traj[filtered_traj["id"] == vid]
            hover = [
                f"ID: {vid}<br>Time: {t}s<br>Lane: {int(l)}<br>Speed: {s:.2f} m/s<br>Accel: {a:.2f} m/s²"
                for t, l, s, a in zip(veh_data["time"], veh_data["lane_kf"], veh_data["speed_kf"], veh_data["acceleration_kf"])
            ]
            fig.add_trace(go.Scatter(
                x=veh_data["xloc_kf"],
                y=veh_data["yloc_kf"],
                mode="markers",
                name=f"Vehicle {vid}",
                marker=dict(size=5),
                text=hover,
                hoverinfo="text",
                line=dict(color=color_list[i % len(color_list)], width=2)
            ))

        fig.update_layout(
            title=f"Run {run_index} Trajectories",
            xaxis=dict(range=[0, max_x]),
            yaxis=dict(range=[0, max_y]),
            xaxis_title="X",
            yaxis_title="Y",
            template="plotly_white"
        )

        fig.write_html("Stationary_Simplified_plot.html")
        fig.show()

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---- UI Elements ----
tk.Label(root, text="Select Run Index:").grid(row=0, column=0)
run_menu = ttk.Combobox(root, textvariable=selected_run, values=[str(r) for r in sorted(traj_df["run_index"].unique())], state="readonly")
run_menu.grid(row=0, column=1)

tk.Label(root, text="Enter Vehicle IDs (comma-separated):").grid(row=1, column=0)
vehicle_entry = tk.Entry(root, width=40)
vehicle_entry.grid(row=1, column=1)

tk.Button(root, text="Plot", command=plot_selected_vehicles).grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
