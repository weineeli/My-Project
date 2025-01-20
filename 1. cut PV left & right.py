import vtk

# 定義變數來替換路徑中的數字
file_number = '70'

# 加載 VTK 文件，使用變數來構建路徑
reader = vtk.vtkPolyDataReader()
reader.SetFileName(fr"C:\Users\willy\Desktop\Done\{file_number}\PV.vtk")
reader.Update()

# 獲取從 reader 中的 polydata
polydata = reader.GetOutput()

# 定義用於切割模型的平面
plane_left = vtk.vtkPlane()
plane_left.SetOrigin(6, 0, 0)  # 設定平面的原點
plane_left.SetNormal(2, 0, 0)  # 設定平面的法向量 (沿著 YZ 平面切割)

plane_right = vtk.vtkPlane()
plane_right.SetOrigin(6, 0, 0)  # 設定平面的原點
plane_right.SetNormal(-2, 0, 0)  # 設定平面的法向量 (沿著 -YZ 平面切割)

# 使用 vtkClipPolyData 對左側部分進行切割
clipper_left = vtk.vtkClipPolyData()
clipper_left.SetClipFunction(plane_left)
clipper_left.SetInputData(polydata)
clipper_left.Update()

# 使用 vtkClipPolyData 對右側部分進行切割
clipper_right = vtk.vtkClipPolyData()
clipper_right.SetClipFunction(plane_right)
clipper_right.SetInputData(polydata)
clipper_right.Update()

# 獲取切割後的 polydata
left_polydata = clipper_left.GetOutput()
right_polydata = clipper_right.GetOutput()

# 保存左側切割的 polydata 到新的 VTK 文件，使用變數來構建路徑
writer_left = vtk.vtkPolyDataWriter()
writer_left.SetFileName(fr"C:\Users\willy\Desktop\Done\{file_number}\left_model.vtk")
writer_left.SetInputData(left_polydata)
writer_left.Write()

# 保存右側切割的 polydata 到新的 VTK 文件，使用變數來構建路徑
writer_right = vtk.vtkPolyDataWriter()
writer_right.SetFileName(fr"C:\Users\willy\Desktop\Done\{file_number}\right_model.vtk")
writer_right.SetInputData(right_polydata)
writer_right.Write()
