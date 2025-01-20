import slicer
import vtk

# 定義主要變數

model_number = "20"  
base_dir = r"C:\Users\willy\Desktop\Done"
input_file_name = "right_model_superior.vtk"
output_file_name = "right_model_superiorr.vtk"

# 組合完整路徑
input_file_path = f"{base_dir}\\{model_number}\\{input_file_name}"
output_file_path = f"{base_dir}\\{model_number}\\{output_file_name}"

# 1. 載入模型 (不再需要使用 returnNode 參數)
modelNode = slicer.util.loadNodeFromFile(input_file_path, 'ModelFile')

if modelNode:
    print("模型加載成功")

# 2. 應用 vtkConnectivityFilter 過濾
connectivityFilter = vtk.vtkConnectivityFilter()
connectivityFilter.SetInputData(modelNode.GetPolyData())
connectivityFilter.SetExtractionModeToLargestRegion()  # 保留最大連通區域
connectivityFilter.Update()

# 3. 獲取結果並更新模型
cleanPolyData = connectivityFilter.GetOutput()
modelNode.SetAndObservePolyData(cleanPolyData)

# 4. 保存處理過後的模型
slicer.util.saveNode(modelNode, output_file_path)
print(f"已保存處理過後的模型至: {output_file_path}")
