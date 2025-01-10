import streamlit as st
import svgpathtools
import os
import base64
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Function to generate G-code (same as earlier)
def svg_to_gcode_with_3d_depth_and_colors(svg_file, gcode_file, bit_diameter=0.5, recess_depth=1.75):
    paths, attributes = svgpathtools.svg2paths(svg_file)
    z_height = 0
    layer_height = 0.2
    bit_radius = bit_diameter / 2
    outline_size = (28, 38)

    with open(gcode_file, 'w') as gcode:
        gcode.write('; Generated G-code for 3D cutting\n')
        gcode.write('G21 ; Set units to mm\n')
        gcode.write('G90 ; Use absolute positioning\n')
        gcode.write('G28 ; Home all axes\n')

        for path, attr in zip(paths, attributes):
            color_class = attr.get('class', '')
            if 'cls-2' in color_class:
                z_offset = 0
            elif 'cls-1' in color_class:
                z_offset = recess_depth
            else:
                z_offset = 0
            
            for segment in path:
                start = segment.start
                end = segment.end
                
                gcode.write(f'G1 X{start.real:.3f} Y{start.imag:.3f} Z{z_height + z_offset:.3f} F1500\n')
                gcode.write(f'G1 X{end.real:.3f} Y{end.imag:.3f} Z{z_height + z_offset + layer_height:.3f} F1500\n')
                z_height += layer_height
        
        gcode.write('G28 ; Home all axes\n')
        gcode.write('M104 S0 ; Turn off extruder\n')
        gcode.write('M140 S0 ; Turn off bed\n')
        gcode.write('M84 ; Disable motors\n')

# Function to generate .isi file
def svg_to_isi(svg_file, isi_file):
    paths, attributes = svgpathtools.svg2paths(svg_file)
    with open(isi_file, 'w') as isi:
        isi.write('; ISI File Generated from SVG\n')
        for path, attr in zip(paths, attributes):
            color_class = attr.get('class', '')
            isi.write(f'; Path with color class: {color_class}\n')
            for segment in path:
                start = segment.start
                end = segment.end
                isi.write(f'LINE {start.real:.3f} {start.imag:.3f} -> {end.real:.3f} {end.imag:.3f}\n')
        isi.write('; End of ISI File\n')

# G-code visualization function
def visualize_gcode(gcode_file):
    with open(gcode_file, 'r') as gcode:
        lines = gcode.readlines()

    x_vals = []
    y_vals = []

    for line in lines:
        if line.startswith('G1'):
            parts = line.split()
            x = y = None
            for part in parts:
                if part.startswith('X'):
                    x = float(part[1:])
                elif part.startswith('Y'):
                    y = float(part[1:])
            if x is not None and y is not None:
                x_vals.append(x)
                y_vals.append(y)

    fig, ax = plt.subplots()
    ax.plot(x_vals, y_vals, label='Toolpath')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title('G-code Toolpath Visualization')
    ax.legend()

    st.pyplot(fig)

# ISI visualization function
def visualize_isi(isi_file):
    with open(isi_file, 'r') as isi:
        lines = isi.readlines()

    x_vals = []
    y_vals = []

    for line in lines:
        if line.startswith('LINE'):
            parts = line.split()
            x1, y1 = float(parts[1]), float(parts[2])
            x2, y2 = float(parts[4]), float(parts[5])
            x_vals.extend([x1, x2])
            y_vals.extend([y1, y2])

    fig, ax = plt.subplots()
    ax.plot(x_vals, y_vals, label='Toolpath')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title('ISI Toolpath Visualization')
    ax.legend()

    st.pyplot(fig)

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
    file_format = st.selectbox("Choose output file format", ['G-code (.gcode)', 'ISI File (.isi)'])

    # Button to generate G-code or ISI file
    if st.button("Generate File"):
        output_file = "output"
        if file_format == 'G-code (.gcode)':
            output_file += ".gcode"
            svg_to_gcode_with_3d_depth_and_colors("uploaded_file.svg", output_file)
            visualize_gcode(output_file)
        else:
            output_file += ".isi"
            svg_to_isi("uploaded_file.svg", output_file)
            visualize_isi(output_file)

        # Provide the download link
        with open(output_file, "rb") as f:
            st.download_button("Download your file", f, file_name=output_file)
        
        st.success(f"{file_format} file generated successfully!")
