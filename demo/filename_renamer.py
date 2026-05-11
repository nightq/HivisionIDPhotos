"""
文件名自动补全功能
- OCR 识别照片中的姓名
- 在 Excel 中搜索姓名匹配
- 用匹配行的所有列值拼接成新文件名
- 重名文件单独存放
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
        """从识别的文本中提取可能的姓名

        规则：
        - 2-4个中文字符
        - 排除常见的非姓名词汇
        """
        # 提取2-4个中文字符的组合（常见姓名长度）
        name_pattern = r"[一-龥]{2,4}"
        potential_names = re.findall(name_pattern, text)

        # 排除常见的非姓名词汇
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
        """加载 Excel 数据

        Args:
            excel_path: Excel 文件路径
            name_column: 姓名列的列名，默认为"姓名"

        Returns:
            DataFrame
        """
        if not self.deps_available:
            raise RuntimeError(f"缺少依赖: {self.deps_missing}")

        # 尝试读取 Excel
        df = pd.read_excel(excel_path)

        # 检查姓名列是否存在
        if name_column not in df.columns:
            # 尝试常见的列名变体
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

    def find_matching_row(self, df: pd.DataFrame, name_column: str, name: str) -> Optional[pd.Series]:
        """在 DataFrame 中查找匹配的行

        Args:
            df: Excel 数据
            name_column: 姓名列名
            name: 要搜索的姓名

        Returns:
            匹配的行，如果无匹配或有多匹配返回 None
        """
        # 精确匹配
        matches = df[df[name_column] == name]

        if len(matches) == 0:
            # 尝试部分匹配
            matches = df[df[name_column].astype(str).str.contains(name, na=False)]

        if len(matches) == 1:
            return matches.iloc[0]
        else:
            return None  # 0 个或多个匹配，都不处理

    def generate_filename_from_row(self, row: pd.Series, exclude_columns: List[str] = None) -> str:
        """从 DataFrame 行生成文件名

        Args:
            row: DataFrame 的一行
            exclude_columns: 要排除的列名列表

        Returns:
            用 "-" 连接的文件名
        """
        if exclude_columns is None:
            exclude_columns = []

        parts = []
        for col, value in row.items():
            if col in exclude_columns:
                continue
            # 转换为字符串并清理非法字符
            value_str = str(value).strip()
            # 移除文件名非法字符
            value_str = re.sub(r'[\\/*?:"<>|\n\r\t]', "", value_str)
            if value_str and value_str != "nan":
                parts.append(value_str)

        return "-".join(parts)

    def process_single_image(
        self,
        image_path: str,
        df: pd.DataFrame,
        name_column: str,
    ) -> Tuple[str, str, str]:
        """处理单张图片

        Args:
            image_path: 图片路径
            df: Excel 数据
            name_column: 姓名列名

        Returns:
            (状态, OCR识别的姓名, 新文件名/原因)
            状态: success, duplicate, no_match, error
        """
        try:
            full_text, names = self.ocr_image(image_path)

            if not names:
                return "no_match", "", "未识别到有效姓名"

            # 尝试每个识别到的姓名，取第一个匹配的
            for name in names:
                matching_row = self.find_matching_row(df, name_column, name)
                if matching_row is not None:
                    new_filename = self.generate_filename_from_row(matching_row)
                    return "success", name, new_filename

            return "no_match", names[0] if names else "", "Excel中未找到匹配姓名"

        except Exception as e:
            return "error", "", str(e)

    def batch_rename(
        self,
        image_files: List[str],
        excel_path: str,
        name_column: str = "姓名",
        output_dir: str = None,
    ) -> Dict:
        """批量重命名照片

        Args:
            image_files: 图片文件路径列表
            excel_path: Excel 文件路径
            name_column: 姓名列名
            output_dir: 输出目录（默认为临时目录）

        Returns:
            处理结果统计和文件列表
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

        # 创建输出目录
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="idphoto_rename_")

        success_dir = os.path.join(output_dir, "已重命名")
        duplicate_dir = os.path.join(output_dir, "重名")
        no_match_dir = os.path.join(output_dir, "未匹配")

        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(duplicate_dir, exist_ok=True)
        os.makedirs(no_match_dir, exist_ok=True)

        results = {
            "total": len(image_files),
            "success": 0,
            "duplicate": 0,
            "no_match": 0,
            "error": 0,
            "success_files": [],
            "duplicate_files": [],
            "no_match_files": [],
            "error_files": [],
        }

        for img_path in image_files:
            if not os.path.exists(img_path):
                continue

            status, recognized_name, info = self.process_single_image(
                img_path, df, actual_name_column
            )
            original_name = os.path.basename(img_path)
            ext = os.path.splitext(original_name)[1]

            if status == "success":
                # 成功：复制到已重命名目录
                new_name = info + ext
                dst_path = os.path.join(success_dir, new_name)
                shutil.copy2(img_path, dst_path)
                results["success"] += 1
                results["success_files"].append((original_name, new_name, recognized_name))
            elif status == "duplicate":
                # 重名：复制到重名目录，保持原名
                dst_path = os.path.join(duplicate_dir, original_name)
                shutil.copy2(img_path, dst_path)
                results["duplicate"] += 1
                results["duplicate_files"].append((original_name, recognized_name))
            elif status == "no_match":
                # 未匹配：复制到未匹配目录，保持原名
                dst_path = os.path.join(no_match_dir, original_name)
                shutil.copy2(img_path, dst_path)
                results["no_match"] += 1
                results["no_match_files"].append((original_name, recognized_name, info))
            else:
                # 错误
                results["error"] += 1
                results["error_files"].append((original_name, info))

        results["output_dir"] = output_dir
        return results
