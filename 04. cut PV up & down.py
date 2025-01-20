import vtk
import numpy as np

# 定義目錄變數
directory_number = "70"

# 定義模型類型列表
model_types = ["left", "right"]

# 迭代處理 left 和 right 模型
for model_type in model_types:
    # 根據模型類型設置文件路徑
    model_path = fr"C:\Users\willy\Desktop\Done\{directory_number}\{model_type}_model.vtk"
    centerline_inferior_path = fr"C:\Users\willy\Desktop\Done\{directory_number}\Centerline_PV_{model_type.capitalize()}_Inferior.vtk"
    centerline_superior_path = fr"C:\Users\willy\Desktop\Done\{directory_number}\Centerline_PV_{model_type.capitalize()}_Superior.vtk"

    # 加載模型
    reader_model = vtk.vtkPolyDataReader()
    reader_model.SetFileName(model_path)
    reader_model.Update()
    model_polydata = reader_model.GetOutput()

    # 加載中心線
    reader_centerline_inferior = vtk.vtkPolyDataReader()
    reader_centerline_inferior.SetFileName(centerline_inferior_path)
    reader_centerline_inferior.Update()
    centerline_inferior = reader_centerline_inferior.GetOutput()

    reader_centerline_superior = vtk.vtkPolyDataReader()
    reader_centerline_superior.SetFileName(centerline_superior_path)
    reader_centerline_superior.Update()
    centerline_superior = reader_centerline_superior.GetOutput()

    # 計算模型點到中心線的最近距離
    def get_closest_point_on_line_kdtree(line_polydata, point):
        kd_tree_locator = vtk.vtkKdTreePointLocator()
        kd_tree_locator.SetDataSet(line_polydata)
        kd_tree_locator.BuildLocator()
        closest_point_id = kd_tree_locator.FindClosestPoint(point)
        return line_polydata.GetPoint(closest_point_id)

    def calculate_distance(point1, point2):
        return np.linalg.norm(np.array(point1) - np.array(point2))

    # 增加空間權重來優化前段切割
    def calculate_weighted_distance(point1, point2, weight=1.0):
        distance = calculate_distance(point1, point2)
        weighted_distance = distance * weight  # 根據距離乘上權重
        return weighted_distance

    # 創建兩個新的PolyData，用來存儲分割結果
    points_inferior = vtk.vtkPoints()
    points_superior = vtk.vtkPoints()

    cells_inferior = vtk.vtkCellArray()
    cells_superior = vtk.vtkCellArray()

    point_map_inferior = {}
    point_map_superior = {}

    # 定義前段區域閥值來區分是否需要調整
    front_threshold = 25  # 根據實際情況調整，代表前段的點分佈

    # 對每個點進行最近中心線判斷
    for i in range(model_polydata.GetNumberOfPoints()):
        point = model_polydata.GetPoint(i)

        # 計算點到inferior和superior中心線的距離
        closest_inferior = get_closest_point_on_line_kdtree(centerline_inferior, point)
        closest_superior = get_closest_point_on_line_kdtree(centerline_superior, point)

        # 判斷當前點是否處於模型的前段區域
        z_coordinate = point[2]  # Z軸坐標可以作為前段的判斷依據
        if z_coordinate > front_threshold:
            weight = 0.2  # 對前段部分使用較小的距離權重
        else:
            weight = 1.0  # 其他部分使用默認權重

        # 根據權重調整距離
        distance_inferior = calculate_weighted_distance(point, closest_inferior, weight)
        distance_superior = calculate_weighted_distance(point, closest_superior, weight)

        # 根據距離將點分配給相應的部分
        if distance_inferior < distance_superior:
            new_id = points_inferior.InsertNextPoint(point)
            point_map_inferior[i] = new_id  # 保存原點ID和新ID的映射
        else:
            new_id = points_superior.InsertNextPoint(point)
            point_map_superior[i] = new_id  # 保存原點ID和新ID的映射

    # 處理多邊形面，將其分配給對應的部分
    for i in range(model_polydata.GetNumberOfCells()):
        cell = model_polydata.GetCell(i)
        point_ids = cell.GetPointIds()
        point_id_list = [point_ids.GetId(j) for j in range(point_ids.GetNumberOfIds())]

        # 計算面上所有點是否應該屬於inferior還是superior部分
        if all(pid in point_map_inferior for pid in point_id_list):
            new_cell = vtk.vtkTriangle()
            for j in range(3):
                new_cell.GetPointIds().SetId(j, point_map_inferior[point_id_list[j]])
            cells_inferior.InsertNextCell(new_cell)
        elif all(pid in point_map_superior for pid in point_id_list):
            new_cell = vtk.vtkTriangle()
            for j in range(3):
                new_cell.GetPointIds().SetId(j, point_map_superior[point_id_list[j]])
            cells_superior.InsertNextCell(new_cell)

    # 構建inferior部分模型
    polydata_inferior = vtk.vtkPolyData()
    polydata_inferior.SetPoints(points_inferior)
    polydata_inferior.SetPolys(cells_inferior)

    # 構建superior部分模型
    polydata_superior = vtk.vtkPolyData()
    polydata_superior.SetPoints(points_superior)
    polydata_superior.SetPolys(cells_superior)

    # 使用 vtkFillHolesFilter 來填補分割後的洞
    def fill_holes(polydata):
        fill_holes_filter = vtk.vtkFillHolesFilter()
        fill_holes_filter.SetInputData(polydata)
        fill_holes_filter.SetHoleSize(100.0)  # 根據需要調整大小
        fill_holes_filter.Update()
        return fill_holes_filter.GetOutput()

    # 填補inferior部分的洞
    filled_polydata_inferior = fill_holes(polydata_inferior)

    # 填補superior部分的洞
    filled_polydata_superior = fill_holes(polydata_superior)

    # 保存分割和填補後的結果
    writer_inferior = vtk.vtkPolyDataWriter()
    writer_inferior.SetFileName(fr"C:\Users\willy\Desktop\Done\{directory_number}\{model_type}_model_inferior.vtk")
    writer_inferior.SetInputData(filled_polydata_inferior)
    writer_inferior.Write()

    writer_superior = vtk.vtkPolyDataWriter()
    writer_superior.SetFileName(fr"C:\Users\willy\Desktop\Done\{directory_number}\{model_type}_model_superior.vtk")
    writer_superior.SetInputData(filled_polydata_superior)
    writer_superior.Write()

    print(f"模型 '{model_type}' 已成功保存")
