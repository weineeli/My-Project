import vtk

# 讀取VTK文件
def read_vtk_file(file_path):
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(file_path)
    reader.Update()
    return reader.GetOutput()

# 寫入VTK文件
def write_vtk_file(polydata, output_path):
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(polydata)
    writer.Write()

# 使用 vtkDecimatePro 來去除枝微末節
def decimate_model(polydata, target_reduction=0.5):
    # 使用vtkDecimatePro進行簡化
    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(polydata)
    decimate.SetTargetReduction(target_reduction)  
    decimate.PreserveTopologyOn()  
    decimate.Update()
    return decimate.GetOutput()

# 使用 FillHolesFilter 來填補孔洞
def fill_holes(polydata, hole_size=1000.0):
    fill_holes_filter = vtk.vtkFillHolesFilter()
    fill_holes_filter.SetInputData(polydata)
    fill_holes_filter.SetHoleSize(hole_size)  # 設置孔洞最大尺寸
    fill_holes_filter.Update()
    return fill_holes_filter.GetOutput()

# 使用 Smoothing 來平滑模型
def smooth_polydata(polydata, num_iterations=20, relaxation_factor=0.5):
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputData(polydata)
    smoother.SetNumberOfIterations(num_iterations)
    smoother.SetRelaxationFactor(relaxation_factor)
    smoother.FeatureEdgeSmoothingOff()
    smoother.BoundarySmoothingOn()
    smoother.Update()
    return smoother.GetOutput()

# 使用 Delaunay3D 重新封閉模型
def delaunay_closing(polydata):
    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputData(polydata)
    delaunay.Update()
    
    surface_filter = vtk.vtkDataSetSurfaceFilter()
    surface_filter.SetInputConnection(delaunay.GetOutputPort())
    surface_filter.Update()

    return surface_filter.GetOutput()

# 使用 FeatureEdges 檢查模型是否有開口
def check_if_open(polydata):
    feature_edges = vtk.vtkFeatureEdges()
    feature_edges.SetInputData(polydata)
    feature_edges.BoundaryEdgesOn()
    feature_edges.NonManifoldEdgesOff()
    feature_edges.ManifoldEdgesOff()
    feature_edges.FeatureEdgesOff()
    feature_edges.Update()

    num_open_edges = feature_edges.GetOutput().GetNumberOfCells()

    if num_open_edges > 0:
        return "open."
    else:
        return "closed."

# 主程式
def process_model(input_file, output_file, target_reduction=0.5):
    # 讀取模型
    polydata = read_vtk_file(input_file)

    # 去除枝微末節（簡化模型）
    polydata = decimate_model(polydata, target_reduction)

    # 填補孔洞
    polydata = fill_holes(polydata)

    # 平滑模型
    polydata = smooth_polydata(polydata)

    # 重新封閉模型
    polydata = delaunay_closing(polydata)

    # 檢查模型是否開口
    status = check_if_open(polydata)
    print(f"The model is {status}")

    # 輸出結果
    write_vtk_file(polydata, output_file)
    print(f"Processed model has been saved to {output_file}")

# 設定輸入和輸出檔案路徑
input_file = "C:/Users/willy/Desktop/PV.vtk"
output_file = "C:/Users/willy/Desktop/PV_processed3.vtk"

target_reduction = 0.5  

# 執行處理流程
process_model(input_file, output_file, target_reduction)
