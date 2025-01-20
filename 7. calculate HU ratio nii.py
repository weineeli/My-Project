import slicer
import os
import numpy as np


file_number = "2"  

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

        # 创建新数组：将脂肪范围设置为 1（白色），其他区域设置为 0（黑色）
        new_labelmap_array = np.zeros(ct_array.shape, dtype=np.int16)  # 默认设置为黑色（0）
        new_labelmap_array[mask_fat_region] = 1  # 脂肪范围设置为白色（1）

        # 创建新的 LabelMap 节点
        updated_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.util.updateVolumeFromArray(updated_node, new_labelmap_array)

        # 检查节点是否创建成功
        if updated_node is None:
            raise RuntimeError(f"无法为模型 {model_name}_{scale} 创建新节点！")

        # 保存节点
        output_path = fr"{base_path}/{file_number}_HU_{model_name}_{scale}.nrrd"
        slicer.util.saveNode(updated_node, output_path)
        print(f"{model_name} {scale} 的最终遮罩已生成并保存到: {output_path}")

# 输出每个模型的脂肪体积，先1X再2X
print("\n--- 各模型脂肪体积统计 ---")

# 先列出所有模型的 1X 脂肪体积
for model_name, model_1x_path, model_2x_path in model_details:
    print(f"{model_name}_1x: {model_volumes.get(f'{model_name}_1x', 0.00):.2f} cm³")

# 然后列出所有模型的 2X 脂肪体积
for model_name, model_1x_path, model_2x_path in model_details:
    print(f"{model_name}_2x: {model_volumes.get(f'{model_name}_2x', 0.00):.2f} cm³")
