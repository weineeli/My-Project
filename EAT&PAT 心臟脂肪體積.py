import slicer
import os
import numpy as np
import vtk

# 更新路径
ct_image_path = r"C:\Users\willy\Desktop\4.nrrd"
model_1x_path = r"C:\Users\willy\Desktop\PV_processed3.vtk"

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

# 只处理 Heart 模型
if not os.path.exists(model_1x_path):
    print(f"模型文件不存在，跳过: {model_1x_path}")
else:
    # 加载模型
    model_node = slicer.util.loadModel(model_1x_path)
    if not model_node:
        print(f"无法加载模型：{model_1x_path}")
    else:
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

        # 更新脂肪体积计算
        fat_voxel_count = np.sum(mask_fat_region)  # 脂肪区域内的体素数
        fat_volume_cm3 = fat_voxel_count * voxel_volume_cm3  # 总脂肪体积
        model_volumes["Heart"] = fat_volume_cm3

        print(f"Heart 的脂肪體積為: {fat_volume_cm3:.2f} cm³")

        # 将当前模型的脂肪范围加入已分配遮罩
        allocated_mask |= mask_fat_region

        # 创建新数组：将脂肪范围设置为 1（白色），其他区域设置为 0（黑色）
        new_labelmap_array = np.zeros(ct_array.shape, dtype=np.int16)  # 默认设置为黑色（0）
        new_labelmap_array[mask_fat_region] = 1  # 脂肪范围设置为白色（1）

        # 创建新的 LabelMap 节点
        updated_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.util.updateVolumeFromArray(updated_node, new_labelmap_array)

        # 获取原始 CT 图像的方向矩阵
        ijk_to_ras_matrix = vtk.vtkMatrix4x4()
        ct_image_node.GetIJKToRASMatrix(ijk_to_ras_matrix)

        # 确保新节点使用正确的方向和原点
        updated_node.SetOrigin(ct_image_node.GetOrigin())
        updated_node.SetIJKToRASMatrix(ijk_to_ras_matrix)  # 设置方向矩阵
        updated_node.SetSpacing(spacing)

        # 检查节点是否创建成功
        if updated_node is None:
            raise RuntimeError(f"无法为模型 Heart 创建新节点！")

        # 保存节点
        output_path = r"C:\Users\willy\Desktop\HU_Heart.nrrd"
        slicer.util.saveNode(updated_node, output_path)
        print(f"Heart 的最終 mask 已生成並保存到: {output_path}")

# 输出 Heart 模型的脂肪体积
print("\n--- Heart 脂肪 ---")
print(f"Heart: {model_volumes.get('Heart', 0.00):.2f} cm³")
