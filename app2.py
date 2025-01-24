import streamlit as st
import svgpathtools
import os
import base64
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import svgpathtools
from svgpathtools import Path


def svg_to_gcode_with_3d_depth_and_colors(svg_file, gcode_file, recess_depth=1.75, extrusion_depth=0.1, scale_factor=0.05, grid_spacing=35):
    paths, attributes = svgpathtools.svg2paths(svg_file)
    z_height = 0  # Starting Z height (same for both colors
    # bit_diameter is assumed to be in inches

    # Function to check if a point is inside a path
    def is_point_inside_path(path, x, y):
        point = complex(x, y)
        crossings = 0
        for segment in path:
            if (segment.start.imag > y) != (segment.end.imag > y):
                cross_x = (y - segment.start.imag) * (segment.end.real - segment.start.real) / (segment.end.imag - segment.start.imag) + segment.start.real
                if x < cross_x:
                    crossings += 1
        return crossings % 2 == 1  # If the point has an odd number of crossings, it is inside

    # Find the bounding box (min and max X, Y values) for all paths
    def get_bounding_box(path):
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        for segment in path:
            min_x = min(min_x, segment.start.real, segment.end.real)
            min_y = min(min_y, segment.start.imag, segment.end.imag)
            max_x = max(max_x, segment.start.real, segment.end.real)
            max_y = max(max_y, segment.start.imag, segment.end.imag)

        return min_x, min_y, max_x, max_y

    # Find the overall bounding box for all paths
    min_x_all, min_y_all = float('inf'), float('inf')
    max_x_all, max_y_all = float('-inf'), float('-inf')

    for path in paths:
        min_x, min_y, max_x, max_y = get_bounding_box(path)
        min_x_all = min(min_x_all, min_x)
        min_y_all = min(min_y_all, min_y)
        max_x_all = max(max_x_all, max_x)
        max_y_all = max(max_y_all, max_y)

    # Translate all paths so that the bounding box starts at (0,0)
    offset_x = -min_x_all
    offset_y = -min_y_all

    with open(gcode_file, 'w') as gcode:
        gcode.write('; Generated G-code for 3D cutting\n')
        gcode.write('G20 ; Set units to Inches\n')
        gcode.write('G90 ; Use absolute positioning\n')
        gcode.write('G28 ; Home all axes\n')

        # Loop through each path and color
        for path, attr in zip(paths, attributes):
            color_class = attr.get('class', '')

            # Check the color class and determine depth
            if 'cls-1' in color_class:  # Light Blue: recessed
                z_height = 0  # Reset Z height for cls-1 areas to ensure uniformity
                extrusion_depth = extrusion_depth_cls_1  # Apply the correct depth for recessed areas

                min_x, min_y, max_x, max_y = get_bounding_box(path)

                current_y = min_y
                while current_y < max_y:
                    x_start = None
                    x_end = None

                    # Find the start and end X positions for the current Y line
                    for x in range(int(min_x), int(max_x) + 1):
                        if is_point_inside_path(path, x, current_y):
                            if x_start is None:
                                x_start = x
                            x_end = x

                    # Write G-code for the detected line segment
                    if x_start is not None and x_end is not None:
                        gcode.write(f'G1 X{(x_start + offset_x) * scale_factor:.3f} Y{(current_y + offset_y) * scale_factor:.3f} Z{z_height + extrusion_depth:.3f} F1500\n')
                        gcode.write(f'G1 X{(x_end + offset_x) * scale_factor:.3f} Y{(current_y + offset_y) * scale_factor:.3f} Z{z_height + extrusion_depth:.3f} F1500\n')

                    current_y += grid_spacing  # Move to the next grid line

            elif 'cls-2' in color_class:  # Dark Blue: NON-recessed
                extrusion_depth = extrusion_depth_cls_2  # Default extrusion depth for cls-2, you can modify this

            else:
                extrusion_depth = 0.1  # Default extrusion depth

            # Process the path for cutting (loop through layers)
            for layer in range(10):  # Adjust the range for the number of layers
                for segment in path:
                    start_x = (segment.start.real + offset_x) * scale_factor
                    start_y = (segment.start.imag + offset_y) * scale_factor
                    end_x = (segment.end.real + offset_x) * scale_factor
                    end_y = (segment.end.imag + offset_y) * scale_factor

                    gcode.write(f'G1 X{start_x:.3f} Y{start_y:.3f} Z{z_height:.3f} F1500\n')
                    gcode.write(f'G1 X{end_x:.3f} Y{end_y:.3f} Z{z_height + extrusion_depth:.3f} F1500\n')

                z_height -= extrusion_depth  # Move down by extrusion depth for the next pass

        gcode.write('G28 ; Home all axes\n')
        gcode.write('M104 S0 ; Turn off extruder\n')
        gcode.write('M140 S0 ; Turn off bed\n')
        gcode.write('M84 ; Disable motors\n')

def get_scale_factor():
    # Take width and height input in inches from the user
    scaling_factor = 100

    # Input fields for width and height in scaled units
    st.subheader("X")
    scaled_width_input = st.number_input("Enter width in scaled units", min_value=0.0, value=20.0, step=0.1)

    st.subheader("Y")
    scaled_height_input = st.number_input("Enter height in scaled units", min_value=0.0, value=40.0, step=0.1)

    # Convert the scaled values back to inches (e.g., 20 becomes 0.2)
    width_inch = scaled_width_input / scaling_factor
    height_inch = scaled_height_input / scaling_factor
    # Calculate the scale factor

    scale_factor = min(width_inch, height_inch) / 1000  # Adjust the divisor to scale down further

    # Ensure the scale factor is within the desired range
    scale_factor = max(0.001, min(scale_factor, 1.0))


    return scale_factor

st.title('SVG to ISI File Generator')

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
    file_format ='ISI File (.lsi)'

    # Ask the user to input a scale factor
    scale_factor = get_scale_factor()

    # Sidebar inputs for block thickness and extrusion depths
    st.sidebar.subheader("Thickness of the block-Z ")
    block_thickness = st.sidebar.number_input(
        "In Inches",
        min_value=0.0,
        max_value=9.0,
        value=4.0,
        step=0.1
    )
  

    st.sidebar.subheader("Light Blue")
    extrusion_depth_cls_1 = st.sidebar.number_input(
        "Recessed, in inches",
        min_value=0.0,
        max_value=block_thickness,  # Max value is based on block thickness
        value=min(4.0, block_thickness),
        step=0.1
    )
    extrusion_depth_cls_1 = extrusion_depth_cls_1/1000

    st.sidebar.write("Dark Blue")
    extrusion_depth_cls_2 = st.sidebar.number_input(
        "Non-recessed, in inches",
        min_value=0.0,
        max_value=block_thickness,  # Max value is based on block thickness
        value=min(0.1, block_thickness),
        step=0.1
    )
    extrusion_depth_cls_2 = extrusion_depth_cls_2/1000

    # Button to generate G-code or ISI file
    if st.button("Generate File"):
        output_file = "output"
        if file_format == 'G-code (.gcode)':
            output_file += ".lsi"
            svg_to_gcode_with_3d_depth_and_colors("uploaded_file.svg", output_file, scale_factor=scale_factor)
            # visualize_gcode(output_file)
        else:
            output_file += ".lsi"
            svg_to_gcode_with_3d_depth_and_colors("uploaded_file.svg", output_file, scale_factor=scale_factor)
            # visualize_isi(output_file)

        # Provide the download link
        with open(output_file, "rb") as f:
            st.download_button("Download your file", f, file_name=output_file)
        
        st.success(f"{file_format} file generated successfully!")
