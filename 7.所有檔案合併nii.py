import slicer
import os
import numpy as np
import vtk

file_number = "70"  

base_path = f"C:/Users/willy/Desktop/Done/{file_number}"
ct_image_path = fr"{base_path}/{file_number}.nrrd"

model_details = [
    ("Right_Superior", fr"{base_path}/right_model_superior_1x.vtk", fr"{base_path}/right_model_superior_2x.vtk"),
    ("Right_Inferior", fr"{base_path}/right_model_inferior_1x.vtk", fr"{base_path}/right_model_inferior_2x.vtk"),
    ("Left_Superior", fr"{base_path}/left_model_superior_1x.vtk", fr"{base_path}/left_model_superior_2x.vtk"),
    ("Left_Inferior", fr"{base_path}/left_model_inferior_1x.vtk", fr"{base_path}/left_model_inferior_2x.vtk"),
]

# HU range for fat (脂肪的HU範圍)
fat_hu_min = -190
fat_hu_max = -30

# load CT image
if not os.path.exists(ct_image_path):
    raise FileNotFoundError(f"CT 影像檔案不存在: {ct_image_path}")
ct_image_node = slicer.util.loadVolume(ct_image_path)

# 获取 CT 影像数据
ct_array = slicer.util.arrayFromVolume(ct_image_node)
spacing = ct_image_node.GetSpacing()  # 获取体素尺寸，单位为毫米
voxel_volume_mm3 = spacing[0] * spacing[1] * spacing[2]  # 每个体素的体积（立方毫米）
voxel_volume_cm3 = voxel_volume_mm3 / 1000.0  # 每个体素的体积（立方厘米）

# 初始化已分配的遮罩，用于保存所有模型的累计结果
allocated_mask = np.zeros(ct_array.shape, dtype=bool)
model_volumes = {}  # 用于保存每个模型的脂肪体积

# 用于存储合并后的 1x 和 2x 遮罩
combined_mask_1x = np.zeros(ct_array.shape, dtype=np.int16)
combined_mask_2x = np.zeros(ct_array.shape, dtype=np.int16)

# 遍历每个模型
for model_name, model_1x_path, model_2x_path in model_details:
    for scale, model_path in [("1x", model_1x_path), ("2x", model_2x_path)]:
        if not os.path.exists(model_path):
            print(f"模型文件不存在，跳过: {model_path}")
            continue

        # 加载模型
        model_node = slicer.util.loadModel(model_path)
        if not model_node:
            print(f"无法加载模型：{model_path}")
            continue

        # 创建分割节点用于生成遮罩
        segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportModelToSegmentationNode(model_node, segmentation_node)
        segmentation_node.CreateBinaryLabelmapRepresentation()

        # 将遮罩设置为与 CT 影像一致的空间
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(ct_image_node)

        # 导出分割为 LabelMap
        labelmap_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentation_node, labelmap_node, ct_image_node)

        # 获取遮罩数据
        labelmap_array = slicer.util.arrayFromVolume(labelmap_node)

        # 筛选脂肪范围：遮罩区域必须在脂肪范围内
        mask_fat_region = (labelmap_array == 1) & (ct_array >= fat_hu_min) & (ct_array <= fat_hu_max)

        # 检查重叠区域，避免重复计算
        overlap_region = allocated_mask & mask_fat_region

        if np.any(overlap_region):
            print(f"{model_name} {scale} 检测到重叠区域，开始完全消除重叠...")

            # 重叠区域的体素完全排除
            mask_fat_region[overlap_region] = False  # 移除重叠区域的体素

        # 更新脂肪体积计算
        fat_voxel_count = np.sum(mask_fat_region)  # 脂肪区域内的体素数
        fat_volume_cm3 = fat_voxel_count * voxel_volume_cm3  # 总脂肪体积
        model_volumes[f"{model_name}_{scale}"] = fat_volume_cm3

        print(f"{model_name} {scale} 的脂肪体积为: {fat_volume_cm3:.2f} cm³")

        # 将当前模型的脂肪范围加入已分配遮罩
        allocated_mask |= mask_fat_region

        # 创建新的 LabelMap 数组：将脂肪范围设置为标签（例如，1-右上，2-右下，...）
        new_labelmap_array = np.zeros(ct_array.shape, dtype=np.int16)  # 默认设置为黑色（0）

        # 根据模型名称为其分配不同的标签（1-4）
        label = {"Right_Superior": 1, "Right_Inferior": 2, "Left_Superior": 3, "Left_Inferior": 4}.get(model_name, 0)
        new_labelmap_array[mask_fat_region] = label  # 脂肪范围设置为对应的标签（1、2、3 或 4）

        # 将每个模型的 1x 和 2x 遮罩合并
        if scale == "1x":
            combined_mask_1x += new_labelmap_array
        else:
            combined_mask_2x += new_labelmap_array

# 保存合并后的 1x 和 2x 遮罩为 NIfTI 格式 (.nii)
combined_mask_1x_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
slicer.util.updateVolumeFromArray(combined_mask_1x_node, combined_mask_1x)

# 创建 vtkMatrix4x4 实例并传递给 GetIJKToRASMatrix 方法
ijk_to_ras_matrix = vtk.vtkMatrix4x4()
ct_image_node.GetIJKToRASMatrix(ijk_to_ras_matrix)

# 确保合并的遮罩使用原始 CT 图像的方向和原点
combined_mask_1x_node.SetOrigin(ct_image_node.GetOrigin())
combined_mask_1x_node.SetIJKToRASMatrix(ijk_to_ras_matrix)  # 设置方向矩阵
combined_mask_1x_node.SetSpacing(spacing)

combined_mask_1x_path = fr"{base_path}/{file_number}_HU_combined_1x.nii"
slicer.util.saveNode(combined_mask_1x_node, combined_mask_1x_path)

combined_mask_2x_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
slicer.util.updateVolumeFromArray(combined_mask_2x_node, combined_mask_2x)

# 确保合并的遮罩使用原始 CT 图像的方向和原点
combined_mask_2x_node.SetOrigin(ct_image_node.GetOrigin())
combined_mask_2x_node.SetIJKToRASMatrix(ijk_to_ras_matrix)  # 设置方向矩阵
combined_mask_2x_node.SetSpacing(spacing)

combined_mask_2x_path = fr"{base_path}/{file_number}_HU_combined_2x.nii"
slicer.util.saveNode(combined_mask_2x_node, combined_mask_2x_path)

print(f"合并后的 1x 遮罩已保存到: {combined_mask_1x_path}")
print(f"合并后的 2x 遮罩已保存到: {combined_mask_2x_path}")

# 输出每个模型的脂肪体积，先1X再2X
print("\n--- 各模型脂肪体积统计 ---")

# 先列出所有模型的 1X 脂肪体积
for model_name, model_1x_path, model_2x_path in model_details:
    print(f"{model_name}_1x: {model_volumes.get(f'{model_name}_1x', 0.00):.4f} cm³")

# 然后列出所有模型的 2X 脂肪体积
for model_name, model_1x_path, model_2x_path in model_details:
    print(f"{model_name}_2x: {model_volumes.get(f'{model_name}_2x', 0.00):.4f} cm³")
