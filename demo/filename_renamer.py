"""
文件名自动补全功能 - 三步处理模式

步骤1: OCR 识别照片中的姓名，重命名为 原文件名-识别出的名字
步骤2: （用户手动修改文件名）
步骤3: 从文件名中提取名字，在 Excel 中搜索匹配，匹配成功则改为 原文件名-名字-行号，失败则改为 原文件名-名字
"""

import os
import re
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    Image = None


class FilenameRenamer:
    def __init__(self):
        self.reader = None
        self._init_dependencies()

    def _init_dependencies(self):
        """检查并初始化依赖"""
        missing = []
        if pd is None:
            missing.append("pandas")
        if not EASYOCR_AVAILABLE:
            missing.append("easyocr")
        if Image is None:
            missing.append("pillow")

        if missing:
            self.deps_available = False
            self.deps_missing = ", ".join(missing)
        else:
            self.deps_available = True
            self.deps_missing = ""

    def _get_ocr_reader(self):
        """懒加载 OCR 阅读器"""
        if self.reader is None:
            self.reader = easyocr.Reader(["ch_sim", "en"], verbose=False)
        return self.reader

    def extract_names_from_text(self, text: str) -> List[str]:
        """从识别的文本中提取可能的姓名"""
        name_pattern = r"[一-龥]{2,4}"
        potential_names = re.findall(name_pattern, text)

        exclude_words = {
            "姓名", "性别", "年龄", "学院", "专业", "班级", "学号",
            "学校", "日期", "时间", "地址", "电话", "手机", "邮箱",
            "编号", "证件", "身份证", "照片", "图片", "文件",
        }

        names = []
        for name in potential_names:
            if name not in exclude_words and len(name) >= 2:
                names.append(name)

        return names

    def ocr_image(self, image_path: str) -> Tuple[str, List[str]]:
        """OCR 识别图片中的文字"""
        if not self.deps_available:
            raise RuntimeError(f"缺少依赖: {self.deps_missing}")

        reader = self._get_ocr_reader()
        results = reader.readtext(image_path, detail=0)
        full_text = " ".join(results)
        names = self.extract_names_from_text(full_text)
        return full_text, names

    def load_excel_data(self, excel_path: str, name_column: str = "姓名") -> pd.DataFrame:
        """加载 Excel 数据"""
        if not self.deps_available:
            raise RuntimeError(f"缺少依赖: {self.deps_missing}")

        df = pd.read_excel(excel_path)

        if name_column not in df.columns:
            for col in ["姓名", "名字", "名称", "学生姓名", "员工姓名"]:
                if col in df.columns:
                    name_column = col
                    break
            else:
                raise ValueError(
                    f"Excel 中未找到姓名列 '{name_column}'，"
                    f"可用列: {', '.join(df.columns.tolist())}"
                )

        return df, name_column

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|\n\r\t]', "", filename)

    # ==================== 步骤1: OCR 识别并重命名 ====================

    def step1_ocr_rename(
        self,
        image_files: List[str],
        output_dir: str = None,
    ) -> Dict:
        """步骤1: OCR 识别照片中的姓名，重命名为 原文件名-识别出的名字

        Args:
            image_files: 图片文件路径列表
            output_dir: 输出目录

        Returns:
            处理结果
        """
        if not self.deps_available:
            return {
                "error": f"缺少必要依赖: {self.deps_missing}",
                "hint": "请安装: pip install pandas easyocr pillow openpyxl",
            }

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="step1_ocr_")

        success_dir = os.path.join(output_dir, "识别成功")
        failed_dir = os.path.join(output_dir, "识别失败")
        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(failed_dir, exist_ok=True)

        results = {
            "total": len(image_files),
            "success": 0,
            "failed": 0,
            "success_files": [],
            "failed_files": [],
            "output_dir": output_dir,
        }

        for img_path in image_files:
            if not os.path.exists(img_path):
                continue

            original_name = os.path.basename(img_path)
            name_without_ext = os.path.splitext(original_name)[0]
            ext = os.path.splitext(original_name)[1]

            try:
                full_text, names = self.ocr_image(img_path)

                if names:
                    recognized_name = names[0]
                    new_filename = f"{name_without_ext}-{recognized_name}{ext}"
                    new_filename = self._sanitize_filename(new_filename)
                    dst_path = os.path.join(success_dir, new_filename)
                    shutil.copy2(img_path, dst_path)
                    results["success"] += 1
                    results["success_files"].append(
                        (original_name, new_filename, recognized_name)
                    )
                else:
                    dst_path = os.path.join(failed_dir, original_name)
                    shutil.copy2(img_path, dst_path)
                    results["failed"] += 1
                    results["failed_files"].append(
                        (original_name, "未识别到有效姓名")
                    )

            except Exception as e:
                dst_path = os.path.join(failed_dir, original_name)
                shutil.copy2(img_path, dst_path)
                results["failed"] += 1
                results["failed_files"].append((original_name, f"识别错误: {str(e)}"))

        return results

    # ==================== 步骤3: Excel 匹配并重命名 ====================

    def step3_excel_match_rename(
        self,
        image_files: List[str],
        excel_path: str,
        name_column: str = "姓名",
        output_dir: str = None,
    ) -> Dict:
        """步骤3: 从文件名中提取名字，在 Excel 中搜索匹配

        匹配成功: 原文件名-名字-行号
        匹配失败: 原文件名-名字（不变）

        Args:
            image_files: 图片文件路径列表（来自步骤1的输出）
            excel_path: Excel 文件路径
            name_column: 姓名列名
            output_dir: 输出目录

        Returns:
            处理结果
        """
        if not self.deps_available:
            return {
                "error": f"缺少必要依赖: {self.deps_missing}",
                "hint": "请安装: pip install pandas easyocr pillow openpyxl",
            }

        try:
            df, actual_name_column = self.load_excel_data(excel_path, name_column)
        except Exception as e:
            return {"error": f"Excel 加载失败: {str(e)}"}

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="step3_match_")

        matched_dir = os.path.join(output_dir, "匹配成功")
        unmatched_dir = os.path.join(output_dir, "未匹配")
        os.makedirs(matched_dir, exist_ok=True)
        os.makedirs(unmatched_dir, exist_ok=True)

        results = {
            "total": len(image_files),
            "matched": 0,
            "unmatched": 0,
            "matched_files": [],
            "unmatched_files": [],
            "output_dir": output_dir,
        }

        for img_path in image_files:
            if not os.path.exists(img_path):
                continue

            original_name = os.path.basename(img_path)
            name_without_ext = os.path.splitext(original_name)[0]
            ext = os.path.splitext(original_name)[1]

            try:
                parts = name_without_ext.rsplit("-", 1)
                if len(parts) >= 2:
                    name_from_filename = parts[1]
                else:
                    name_from_filename = name_without_ext

                matches = df[df[actual_name_column].astype(str).str.strip() == name_from_filename.strip()]

                if len(matches) == 1:
                    row_number = matches.index[0] + 2
                    new_filename = f"{name_without_ext}-{row_number}{ext}"
                    new_filename = self._sanitize_filename(new_filename)
                    dst_path = os.path.join(matched_dir, new_filename)
                    shutil.copy2(img_path, dst_path)
                    results["matched"] += 1
                    results["matched_files"].append(
                        (original_name, new_filename, name_from_filename, row_number)
                    )
                else:
                    dst_path = os.path.join(unmatched_dir, original_name)
                    shutil.copy2(img_path, dst_path)
                    results["unmatched"] += 1
                    reason = "找到多个匹配" if len(matches) > 1 else "未找到匹配"
                    results["unmatched_files"].append(
                        (original_name, name_from_filename, reason)
                    )

            except Exception as e:
                dst_path = os.path.join(unmatched_dir, original_name)
                shutil.copy2(img_path, dst_path)
                results["unmatched"] += 1
                results["unmatched_files"].append(
                    (original_name, "", f"处理错误: {str(e)}")
                )

        return results
