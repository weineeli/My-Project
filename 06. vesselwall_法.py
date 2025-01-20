import vtk
import slicer

# 禁用VTK警告消息
def disable_vtk_warnings():
    logger = vtk.vtkObject()
    logger.GlobalWarningDisplayOff()

# 调用该函数禁用所有VTK警告
disable_vtk_warnings()

# 設定路徑中的變數
folder_number = "70"

# 設定固定距離
fixed_distance_1x = 5.0

# 計算2倍固定距離
def calculate_fixed_distance_2x(fixed_distance_1x):
    return fixed_distance_1x * 2

fixed_distance_2x = calculate_fixed_distance_2x(fixed_distance_1x)

# 使用 FillHolesFilter 來填補孔洞
def fill_holes(polydata, hole_size=1000.0):
    fill_holes_filter = vtk.vtkFillHolesFilter()
    fill_holes_filter.SetInputData(polydata)
    fill_holes_filter.SetHoleSize(hole_size)  # 設置孔洞最大尺寸
    fill_holes_filter.Update()
    return fill_holes_filter.GetOutput()

# 使用 Smoothing 來平滑模型
def smooth_polydata(polydata, num_iterations=20, relaxation_factor=0.1):
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

# 通用函式: 加載模型、生成延伸模型並保存，並加載至3D Slicer
def process_vessel_model(centerline_path, vessel_path, output_path_1x, output_path_2x, fixed_distance_1x, fixed_distance_2x, model_name):
    # 加載中心線文件
    centerlineNode = slicer.util.loadNodeFromFile(centerline_path, 'ModelFile')
    centerline_polydata = centerlineNode.GetPolyData()

    # 加載原始血管模型
    vesselNode = slicer.util.loadNodeFromFile(vessel_path, 'ModelFile')
    if vesselNode is None:
        print(f"原始血管模型無法加載: {vessel_path}")
        return

    # 函式：計算模型的體積
    def calculate_volume(polydata):
        mass = vtk.vtkMassProperties()
        mass.SetInputData(polydata)
        mass.Update()
        volume = mass.GetVolume()  # 計算體積
        return volume

    # 函式：生成固定距離的延伸模型並保存
    def generate_and_save_model(vesselNode, fixed_distance, output_path, color, model_suffix):
        polydata = vesselNode.GetPolyData()

        # 計算法向量
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ComputePointNormalsOn()
        normals.Update()

        # 取得法向量
        normal_vectors = normals.GetOutput().GetPointData().GetNormals()

        # 取得所有點座標
        points = polydata.GetPoints()

        # 創建新的點座標，基於法向量將點推動
        new_points = vtk.vtkPoints()

        for i in range(points.GetNumberOfPoints()):
            p = points.GetPoint(i)
            n = normal_vectors.GetTuple(i)
            
            # 沿法向量方向延伸
            new_point = [p[j] + fixed_distance * n[j] for j in range(3)]
            new_points.InsertNextPoint(new_point)

        # 更新模型的點
        new_polydata = vtk.vtkPolyData()
        new_polydata.DeepCopy(polydata)
        new_polydata.SetPoints(new_points)

        # 使用 Delaunay 進行封閉
        delaunay_polydata = delaunay_closing(new_polydata)

        # 平滑模型
        smoothed_polydata = smooth_polydata(delaunay_polydata)

        # 計算擴展模型的體積
        extended_volume = calculate_volume(smoothed_polydata)

        # 檢查延伸後模型是否有開口
        closure_status = check_if_open(smoothed_polydata)

        # 加載到Slicer並設置透明度
        extended_vessel_model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", f"{model_name}_{model_suffix}")
        extended_vessel_model_node.SetAndObservePolyData(smoothed_polydata)
        extended_vessel_model_node.CreateDefaultDisplayNodes()
        extended_display_node = extended_vessel_model_node.GetDisplayNode()
        extended_display_node.SetColor(*color)
        extended_display_node.SetOpacity(0.5)  # 設置透明度為50%

        # 使用slicer.util.saveNode保存模型
        slicer.util.saveNode(extended_vessel_model_node, output_path)

        # 返回體積和是否有開口
        return extended_volume, closure_status

    # 計算原始模型的體積
    original_volume = calculate_volume(vesselNode.GetPolyData())
    result = f"{model_name} 的體積: {original_volume:.3f}\n"

    # 生成1倍固定距離模型
    volume_1x, closure_1x = generate_and_save_model(vesselNode, fixed_distance_1x, output_path_1x, (0, 1, 0), "1x")
    volume_2x, closure_2x = generate_and_save_model(vesselNode, fixed_distance_2x, output_path_2x, (1, 0, 0), "2x")

    # 更新输出顺序并将它们连在一起
    result += f"擴展模型1x的體積 ({fixed_distance_1x}mm): {volume_1x:.3f}\n"
    result += f"擴展模型2x的體積 ({fixed_distance_2x}mm): {volume_2x:.3f}\n"
    result += f"擴展模型1x是否有開口 ({fixed_distance_1x}mm): {closure_1x}\n"
    result += f"擴展模型2x是否有開口 ({fixed_distance_2x}mm): {closure_2x}\n"

    return result

# 定義路徑格式
base_path = f"C:\\Users\\willy\\Desktop\\Done\\{folder_number}"

# 定義左側和右側的模型處理參數
vessels = [
    ("Centerline_PV_Left_Superior.vtk", "left_model_superior_clipped.vtk", "left_model_superior_1x.vtk", "left_model_superior_2x.vtk", "Left_Model_Superior"),
    ("Centerline_PV_Left_Inferior.vtk", "left_model_inferior_clipped.vtk", "left_model_inferior_1x.vtk", "left_model_inferior_2x.vtk", "Left_Model_Inferior"),
    ("Centerline_PV_Right_Superior.vtk", "right_model_superior_clipped.vtk", "right_model_superior_1x.vtk", "right_model_superior_2x.vtk", "Right_Model_Superior"),
    ("Centerline_PV_Right_Inferior.vtk", "right_model_inferior_clipped.vtk", "right_model_inferior_1x.vtk", "right_model_inferior_2x.vtk", "Right_Model_Inferior"),
]

# 初始化存儲結果的列表
results = []
batch_size = 5  # 每批次打印的模型數量

# 遍歷並處理每個血管模型
for i, (centerline, clipped, model_1x, model_2x, model_name) in enumerate(vessels):
    result = process_vessel_model(
        f"{base_path}\\{centerline}",
        f"{base_path}\\{clipped}",
        f"{base_path}\\{model_1x}",
        f"{base_path}\\{model_2x}",
        fixed_distance_1x,
        fixed_distance_2x,
        model_name
    )
    results.append(result)

    # 每5個輸出一組
    if (i + 1) % batch_size == 0 or (i + 1) == len(vessels):
        # 合併並打印當前批次結果
        print("\n".join(results))
        results = []
