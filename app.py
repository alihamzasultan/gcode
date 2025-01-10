import streamlit as st
import svgpathtools
import os
import base64
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Function to generate G-code (same as earlier)
def svg_to_gcode_with_3d_depth_and_colors(svg_file, gcode_file, bit_diameter=0.5, recess_depth=1.75, extrusion_depth=0.1, scale_factor=0.05):



    paths, attributes = svgpathtools.svg2paths(svg_file)
    z_height = 0  # Starting Z height (same for both colors)
    layer_height = 0.2  # Height of each layer (extrusion per pass)
    bit_radius = bit_diameter / 2

    # Find the bounding box (min and max X, Y values)
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for path in paths:
        for segment in path:
            min_x = min(min_x, segment.start.real, segment.end.real)
            min_y = min(min_y, segment.start.imag, segment.end.imag)
            max_x = max(max_x, segment.start.real, segment.end.real)
            max_y = max(max_y, segment.start.imag, segment.end.imag)

    # Calculate center of the bounding box
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Calculate the offset required to center the figure
    offset_x = 0
    offset_y = 0

    with open(gcode_file, 'w') as gcode:
        gcode.write('; Generated G-code for 3D cutting\n')
        gcode.write('G21 ; Set units to mm\n')
        gcode.write('G90 ; Use absolute positioning\n')
        gcode.write('G28 ; Home all axes\n')

        # Loop through each path and color
        for path, attr in zip(paths, attributes):
            color_class = attr.get('class', '')

            # Apply Z offset based on color class (both start from Z=0, but extrusion depth differs)
            if 'cls-1' in color_class:  # Dark Blue: non-recessed
                extrusion_depth = extrusion_depth_cls_1  # Small extrusion depth for non-recessed
            elif 'cls-2' in color_class:  # Light Blue: recessed
                extrusion_depth = extrusion_depth_cls_2  # Larger extrusion depth for recessed color
            else:
                extrusion_depth = 0.1  # Default extrusion depth

            # Loop over each segment to add extrusion
            for layer in range(10):  # Adjust the range for how many layers to cut
                for segment in path:
                    # Apply scaling and centering to each point
                    start_x = (segment.start.real + offset_x) * scale_factor
                    start_y = (segment.start.imag + offset_y) * scale_factor
                    end_x = (segment.end.real + offset_x) * scale_factor
                    end_y = (segment.end.imag + offset_y) * scale_factor

                    # Move to the start of the path at the current Z height
                    gcode.write(f'G1 X{start_x:.3f} Y{start_y:.3f} Z{z_height:.3f} F1500\n')

                    # Extrusion at current layer depth
                    gcode.write(f'G1 X{end_x:.3f} Y{end_y:.3f} Z{z_height + extrusion_depth:.3f} F1500\n')

                # After each layer, decrease Z height for the next layer (the actual cutting happens here)
                z_height -= extrusion_depth  # Move down by extrusion depth for the next pass

        # End of G-code, move to home position and turn off extruder and motors
        gcode.write('G28 ; Home all axes\n')
        gcode.write('M104 S0 ; Turn off extruder\n')
        gcode.write('M140 S0 ; Turn off bed\n')
        gcode.write('M84 ; Disable motors\n')

# Function to generate .isi file
def svg_to_isi_with_3d_depth_and_colors(svg_file, isi_file, bit_diameter=0.5, recess_depth=1.75, extrusion_depth=0.1, scale_factor=0.05):
    paths, attributes = svgpathtools.svg2paths(svg_file)
    z_height = 0  # Starting Z height (same for both colors)
    layer_height = 0.2  # Height of each layer (extrusion per pass)
    bit_radius = bit_diameter / 2

    # Find the bounding box (min and max X, Y values)
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for path in paths:
        for segment in path:
            min_x = min(min_x, segment.start.real, segment.end.real)
            min_y = min(min_y, segment.start.imag, segment.end.imag)
            max_x = max(max_x, segment.start.real, segment.end.real)
            max_y = max(max_y, segment.start.imag, segment.end.imag)

    # Calculate center of the bounding box
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Calculate the offset required to center the figure
    offset_x = 0
    offset_y = 0

    with open(isi_file, 'w') as isi:
        isi.write('; ISI File Generated for 3D cutting\n')

        # Loop through each path and color
        for path, attr in zip(paths, attributes):
            color_class = attr.get('class', '')

            # Apply Z offset based on color class (both start from Z=0, but extrusion depth differs)
            if 'cls-1' in color_class:  # Dark Blue: non-recessed
                extrusion_depth = extrusion_depth_cls_1  # Small extrusion depth for non-recessed
            elif 'cls-2' in color_class:  # Light Blue: recessed
                extrusion_depth = extrusion_depth_cls_2  # Larger extrusion depth for recessed color
            else:
                extrusion_depth = 0.1  # Default extrusion depth

            # Loop over each segment to add extrusion
            for layer in range(10):  # Adjust the range for how many layers to cut
                for segment in path:
                    # Apply scaling and centering to each point
                    start_x = (segment.start.real + offset_x) * scale_factor
                    start_y = (segment.start.imag + offset_y) * scale_factor
                    end_x = (segment.end.real + offset_x) * scale_factor
                    end_y = (segment.end.imag + offset_y) * scale_factor

                    # Write the toolpath for the current Z height
                    isi.write(f'LINE X{start_x:.3f} Y{start_y:.3f} Z{z_height:.3f} -> ')
                    isi.write(f'X{end_x:.3f} Y{end_y:.3f} Z{z_height + extrusion_depth:.3f}\n')

                # After each layer, decrease Z height for the next layer (the actual cutting happens here)
                z_height -= extrusion_depth  # Move down by extrusion depth for the next pass

        isi.write('; End of ISI File\n')

def get_scale_factor():
    # Take width and height input in inches from the user
    width_inch = st.number_input("Enter width in inches", min_value=0.0, step=0.1)
    height_inch = st.number_input("Enter height in inches", min_value=0.0, step=0.1)
    
    # Convert inches to mm
    width_mm = width_inch * 25.4
    height_mm = height_inch * 25.4
    
    # Calculate the scale factor
    scale_factor = min(width_mm, height_mm) / 1000  # Scaling down to keep the factor between 0.01 and 10.0
    
    # Ensure the scale factor is within the desired range
    scale_factor = max(0.01, min(scale_factor, 10.0))

    st.write("Scale factor is: ",scale_factor)
    
    return scale_factor
# G-code visualization function
# def visualize_gcode(gcode_file):
#     with open(gcode_file, 'r') as gcode:
#         lines = gcode.readlines()

#     x_vals = []
#     y_vals = []

#     for line in lines:
#         if line.startswith('G1'):
#             parts = line.split()
#             x = y = None
#             for part in parts:
#                 if part.startswith('X'):
#                     x = float(part[1:])
#                 elif part.startswith('Y'):
#                     y = float(part[1:])
#             if x is not None and y is not None:
#                 x_vals.append(x)
#                 y_vals.append(y)

#     fig, ax = plt.subplots()
#     ax.plot(x_vals, y_vals, label='Toolpath')
#     ax.set_xlabel('X (mm)')
#     ax.set_ylabel('Y (mm)')
#     ax.set_title('G-code Toolpath Visualization')
#     ax.legend()

#     st.pyplot(fig)

# ISI visualization function
# def visualize_isi(isi_file):
#     with open(isi_file, 'r') as isi:
#         lines = isi.readlines()

#     x_vals = []
#     y_vals = []

#     for line in lines:
#         if line.startswith('LINE'):
#             parts = line.split()
#             x1, y1 = float(parts[1]), float(parts[2])
#             x2, y2 = float(parts[4]), float(parts[5])
#             x_vals.extend([x1, x2])
#             y_vals.extend([y1, y2])

#     fig, ax = plt.subplots()
#     ax.plot(x_vals, y_vals, label='Toolpath')
#     ax.set_xlabel('X (mm)')
#     ax.set_ylabel('Y (mm)')
#     ax.set_title('ISI Toolpath Visualization')
#     ax.legend()

#     st.pyplot(fig)

# Streamlit UI
# Streamlit UI
st.title('SVG to G-code or ISI File Generator')

# File uploader for SVG file
uploaded_svg = st.file_uploader("Upload an SVG file", type="svg")

# If an SVG file is uploaded
if uploaded_svg is not None:
    # Save uploaded file
    with open("uploaded_file.svg", "wb") as f:
        f.write(uploaded_svg.getbuffer())
    
    st.success("SVG file uploaded successfully!")

    # Display the uploaded SVG
    st.subheader("SVG Preview")
    
    # Convert the SVG file to base64 encoding
    svg_base64 = base64.b64encode(uploaded_svg.getvalue()).decode()

    # Display the SVG as an embedded object in the app
    st.markdown(f'<embed src="data:image/svg+xml;base64,{svg_base64}" width="600" height="400" type="image/svg+xml">', unsafe_allow_html=True)

    # Ask the user for the file format choice
    file_format = st.selectbox("Choose output file format", ['G-code (.gcode)', 'ISI File (.lsi)'])

    # Ask the user to input a scale factor
    scale_factor = get_scale_factor()

    extrusion_depth_cls_1 = st.number_input(
        "Enter the extrusion depth for 'cls-1' (non-recessed, Light Blue):",
        min_value=0.0,
        max_value=5.0,
        value=0.1,
        step=0.1
    )

    extrusion_depth_cls_2 = st.number_input(
        "Enter the extrusion depth for 'cls-2' (recessed, Dark Blue):",
        min_value=0.0,
        max_value=5.0,
        value=0.5,
        step=0.1
    )

    # Button to generate G-code or ISI file
    if st.button("Generate File"):
        output_file = "output"
        if file_format == 'G-code (.gcode)':
            output_file += ".gcode"
            svg_to_gcode_with_3d_depth_and_colors("uploaded_file.svg", output_file, scale_factor=scale_factor)
            # visualize_gcode(output_file)
        else:
            output_file += ".lsi"
            svg_to_isi_with_3d_depth_and_colors("uploaded_file.svg", output_file, scale_factor=scale_factor)
            # visualize_isi(output_file)

        # Provide the download link
        with open(output_file, "rb") as f:
            st.download_button("Download your file", f, file_name=output_file)
        
        st.success(f"{file_format} file generated successfully!")
