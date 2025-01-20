import vtk
import numpy as np
import slicer
import json

# 定義目錄變數
directory_number = "70"
base_path = rf"C:\Users\willy\Desktop\Done\{directory_number}"

def process_model(model_path, centerline_path, output_json_path, output_model_path, model_name_prefix, radius):
    # Load model
    modelNode = slicer.util.loadNodeFromFile(model_path, 'ModelFile')
    model_polydata = modelNode.GetPolyData()

    # Load centerline file
    centerlineNode = slicer.util.loadNodeFromFile(centerline_path, 'ModelFile')

    # Get the PolyData of the centerline and clean it
    centerline_polydata = centerlineNode.GetPolyData()
    cleaner = vtk.vtkCleanPolyData()
    cleaner.SetInputData(centerline_polydata)
    cleaner.Update()
    cleaned_centerline = cleaner.GetOutput()

    # Interpolation using vtkSplineFilter
    spline_filter = vtk.vtkSplineFilter()
    spline_filter.SetInputData(cleaned_centerline)
    spline_filter.SetSubdivideToLength()  
    spline_filter.SetLength(1.0)  # the distance between each point is 1 mm
    spline_filter.Update()

    # Interpolated centerline
    interpolated_centerline = spline_filter.GetOutput()

    # Extract interpolated point coordinates
    interpolated_points = interpolated_centerline.GetPoints()

    # Get the first point point[0]
    point_0 = np.array(interpolated_points.GetPoint(0))

    # Create a sphere that clips outside the radius
    sphere = vtk.vtkSphere()
    sphere.SetCenter(point_0)
    sphere.SetRadius(radius)

    # Use vtkClipPolyData to clip the model and keep the part inside the sphere
    clipper = vtk.vtkClipPolyData()
    clipper.SetInputData(model_polydata)
    clipper.SetClipFunction(sphere)
    clipper.InsideOutOn()  # keep the part inside the sphere
    clipper.Update()

    # Save the clipped model to clipped_model_polydata
    clipped_model_polydata = clipper.GetOutput()

    # Use vtkFillHolesFilter to fill cropped holes
    fill_holes_filter = vtk.vtkFillHolesFilter()
    fill_holes_filter.SetInputData(clipped_model_polydata)
    fill_holes_filter.SetHoleSize(100.0)  
    fill_holes_filter.Update()

    # Triangulated closed surface
    triangle_filter = vtk.vtkTriangleFilter()
    triangle_filter.SetInputData(fill_holes_filter.GetOutput())
    triangle_filter.Update()

    # Get the filled model
    filled_model_polydata = triangle_filter.GetOutput()

    # Visualize the filled model
    clipped_model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", f"{model_name_prefix}_FilledClosedModel")
    clipped_model_node.SetAndObservePolyData(filled_model_polydata)

    # Hide the original model and show only the filled model
    modelNode.SetDisplayVisibility(0)
    clipped_model_node.CreateDefaultDisplayNodes()
    clipped_model_node.GetDisplayNode().SetVisibility(1)

    # Mark the red point at the first point of the center line (point_0)
    sphere_source_red = vtk.vtkSphereSource()
    sphere_source_red.SetCenter(point_0)
    sphere_source_red.SetRadius(1.0) 
    sphere_source_red.Update()

    # Create a red dot node and display it
    red_sphere_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", f"{model_name_prefix}_RedPoint_0")
    red_sphere_node.SetAndObservePolyData(sphere_source_red.GetOutput())
    red_sphere_node.CreateDefaultDisplayNodes()
    red_sphere_node.GetDisplayNode().SetColor(0, 1, 0)  # red
    red_sphere_node.GetDisplayNode().SetVisibility(1)

    # Green points are generated at the radius position
    matching_points_coordinates = []

    for i in range(interpolated_points.GetNumberOfPoints()):
        point = np.array(interpolated_points.GetPoint(i))

        # Calculate the distance between the current - the first point
        distance = np.linalg.norm(point - point_0)

        # If the distance is exactly equal to the radius, a green point is generated
        if np.isclose(distance, radius, atol=0.5):  
            # create a green ball
            sphere_source = vtk.vtkSphereSource()
            sphere_source.SetCenter(point)
            sphere_source.SetRadius(1.0) 
            sphere_source.Update()

            # display green dots
            green_sphere_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", f"{model_name_prefix}_GreenSphere_{i}")
            green_sphere_node.SetAndObservePolyData(sphere_source.GetOutput())
            green_sphere_node.CreateDefaultDisplayNodes()
            green_sphere_node.GetDisplayNode().SetColor(1, 0, 0)  # green
            green_sphere_node.GetDisplayNode().SetVisibility(1)

            # save
            matching_points_coordinates.append({"coordinates": point.tolist(), "radius": radius})

    # Store found points as JSON file
    with open(output_json_path, 'w') as json_file:
        json.dump(matching_points_coordinates, json_file, indent=4)

    # Print the number of green points generated
    num_green_points = len(matching_points_coordinates)
    print(f"The number of green dots: {num_green_points}")
    print(f"Crop according to radius {radius} mm, and store the green points to {output_json_path}")

    # Save the clipped and filled model using slicer.util.saveNode
    success = slicer.util.saveNode(clipped_model_node, output_model_path)

    if success:
        print(f"The cut and filled model has been saved to {output_model_path}")
    else:
        print("error")

    # Refresh 3D view
    slicer.app.processEvents()


# Process the left superior model
process_model(
    fr"{base_path}\left_model_superior.vtk", 
    fr"{base_path}\Centerline_PV_Left_Superior.vtk", 
    fr"{base_path}\points_within_radius_left_superior.json", 
    fr"{base_path}\left_model_superior_clipped.vtk", 
    "LeftSuperiorModel",
    20.0  # left superior model radius
)

# Process the left inferior model
process_model(
    fr"{base_path}\left_model_inferior.vtk", 
    fr"{base_path}\Centerline_PV_Left_Inferior.vtk", 
    fr"{base_path}\points_within_radius_left_inferior.json", 
    fr"{base_path}\left_model_inferior_clipped.vtk", 
    "LeftInferiorModel",
    20.0  # left inferior model radius
)

# Process the right superior model
process_model(
    fr"{base_path}\right_model_superior.vtk", 
    fr"{base_path}\Centerline_PV_Right_Superior.vtk", 
    fr"{base_path}\points_within_radius_right_superior.json", 
    fr"{base_path}\right_model_superior_clipped.vtk", 
    "RightSuperiorModel",
    20.0  # right superior model radius
)

# Process the right inferior model
process_model(
    fr"{base_path}\right_model_inferior.vtk", 
    fr"{base_path}\Centerline_PV_Right_Inferior.vtk", 
    fr"{base_path}\points_within_radius_right_inferior.json", 
    fr"{base_path}\right_model_inferior_clipped.vtk", 
    "RightInferiorModel",
    20.0  # right inferior model radius
)
