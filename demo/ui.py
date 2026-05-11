import gradio as gr
import os
import pathlib
from demo.locales import LOCALES
from demo.processor import IDPhotoProcessor
from demo.filename_renamer import FilenameRenamer

"""
只裁切模式:
1. 如果重新上传了照片，然后点击按钮，第一次会调用不裁切的模式，第二次会调用裁切的模式
"""


def load_description(fp):
    """
    加载title.md文件作为Demo的顶部栏
    """
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def create_ui(
    processor: IDPhotoProcessor,
    root_dir: str,
    human_matting_models: list,
    face_detect_models: list,
    language: list,
):

    # 加载环境变量DEFAULT_LANG, 如果有且在language中，则将DEFAULT_LANG设置为环境变量
    if "DEFAULT_LANG" in os.environ and os.environ["DEFAULT_LANG"] in language:
        DEFAULT_LANG = os.environ["DEFAULT_LANG"]
    else:
        DEFAULT_LANG = language[0]

    DEFAULT_HUMAN_MATTING_MODEL = "modnet_photographic_portrait_matting"
    DEFAULT_FACE_DETECT_MODEL = "retinaface-resnet50"

    if DEFAULT_HUMAN_MATTING_MODEL in human_matting_models:
        human_matting_models.remove(DEFAULT_HUMAN_MATTING_MODEL)
        human_matting_models.insert(0, DEFAULT_HUMAN_MATTING_MODEL)

    if DEFAULT_FACE_DETECT_MODEL not in face_detect_models:
        DEFAULT_FACE_DETECT_MODEL = "mtcnn"

    demo = gr.Blocks(title="证件照工具")

    with demo:
        gr.HTML(load_description(os.path.join(root_dir, "demo/assets/title.md")))
        with gr.Tabs():
            # ------------------------ 单张处理 Tab ------------------------
            with gr.Tab("单张处理") as single_tab:
                with gr.Row():
                    # ------------------------ 左半边 UI ------------------------
                    with gr.Column():
                        img_input = gr.Image(height=400)

                with gr.Row():
                    # 语言选择器
                    language_options = gr.Dropdown(
                        choices=language,
                        label="Language",
                        value=DEFAULT_LANG,
                    )

                    face_detect_model_options = gr.Dropdown(
                        choices=face_detect_models,
                        label=LOCALES["face_model"][DEFAULT_LANG]["label"],
                        value=DEFAULT_FACE_DETECT_MODEL,
                    )

                    matting_model_options = gr.Dropdown(
                        choices=human_matting_models,
                        label=LOCALES["matting_model"][DEFAULT_LANG]["label"],
                        value=human_matting_models[0],
                    )

                # TAB1 - 关键参数 ------------------------------------------------
                with gr.Tab(
                    LOCALES["key_param"][DEFAULT_LANG]["label"]
                ) as key_parameter_tab:
                    # 尺寸模式
                    with gr.Row():
                        mode_options = gr.Radio(
                            choices=LOCALES["size_mode"][DEFAULT_LANG]["choices"],
                            label=LOCALES["size_mode"][DEFAULT_LANG]["label"],
                            value=LOCALES["size_mode"][DEFAULT_LANG]["choices"][0],
                            min_width=520,
                        )
                        
                    # 尺寸列表
                    with gr.Row(visible=True) as size_list_row:
                        size_list_options = gr.Dropdown(
                            choices=LOCALES["size_list"][DEFAULT_LANG]["choices"],
                            label=LOCALES["size_list"][DEFAULT_LANG]["label"],
                            value=LOCALES["size_list"][DEFAULT_LANG]["choices"][0],
                            elem_id="size_list",
                        )
                    # 自定义尺寸px
                    with gr.Row(visible=False) as custom_size_px:
                        custom_size_height_px = gr.Number(
                            value=413,
                            label=LOCALES["custom_size_px"][DEFAULT_LANG]["height"],
                            interactive=True,
                        )
                        custom_size_width_px = gr.Number(
                            value=295,
                            label=LOCALES["custom_size_px"][DEFAULT_LANG]["width"],
                            interactive=True,
                        )
                    # 自定义尺寸mm
                    with gr.Row(visible=False) as custom_size_mm:
                        custom_size_height_mm = gr.Number(
                            value=35,
                            label=LOCALES["custom_size_mm"][DEFAULT_LANG]["height"],
                            interactive=True,
                        )
                        custom_size_width_mm = gr.Number(
                            value=25,
                            label=LOCALES["custom_size_mm"][DEFAULT_LANG]["width"],
                            interactive=True,
                        )

                    # 背景颜色
                    color_options = gr.Radio(
                        choices=LOCALES["bg_color"][DEFAULT_LANG]["choices"],
                        label=LOCALES["bg_color"][DEFAULT_LANG]["label"],
                        value=LOCALES["bg_color"][DEFAULT_LANG]["choices"][0],
                    )
                    
                    # 自定义颜色RGB
                    with gr.Row(visible=False) as custom_color_rgb:
                        custom_color_R = gr.Number(value=0, label="R", minimum=0, maximum=255, interactive=True)
                        custom_color_G = gr.Number(value=0, label="G", minimum=0, maximum=255, interactive=True)
                        custom_color_B = gr.Number(value=0, label="B", minimum=0, maximum=255, interactive=True)
                    
                    # 自定义颜色HEX
                    with gr.Row(visible=False) as custom_color_hex:
                        custom_color_hex_value = gr.Text(value="000000", label="Hex", interactive=True)

                    # 渲染模式
                    render_options = gr.Radio(
                        choices=LOCALES["render_mode"][DEFAULT_LANG]["choices"],
                        label=LOCALES["render_mode"][DEFAULT_LANG]["label"],
                        value=LOCALES["render_mode"][DEFAULT_LANG]["choices"][0],
                    )
                    
                    with gr.Row():
                        # 插件模式
                        plugin_options = gr.CheckboxGroup(
                            label=LOCALES["plugin"][DEFAULT_LANG]["label"],
                            choices=LOCALES["plugin"][DEFAULT_LANG]["choices"],
                            interactive=True,
                            value=LOCALES["plugin"][DEFAULT_LANG]["value"]
                        )

                # TAB2 - 高级参数 ------------------------------------------------
                with gr.Tab(
                    LOCALES["advance_param"][DEFAULT_LANG]["label"]
                ) as advance_parameter_tab:
                    head_measure_ratio_option = gr.Slider(
                        minimum=0.1,
                        maximum=0.5,
                        value=0.2,
                        step=0.01,
                        label=LOCALES["head_measure_ratio"][DEFAULT_LANG]["label"],
                        interactive=True,
                    )
                    top_distance_option = gr.Slider(
                        minimum=0.02,
                        maximum=0.5,
                        value=0.12,
                        step=0.01,
                        label=LOCALES["top_distance"][DEFAULT_LANG]["label"],
                        interactive=True,
                    )

                    image_kb_options = gr.Radio(
                        choices=LOCALES["image_kb"][DEFAULT_LANG]["choices"],
                        label=LOCALES["image_kb"][DEFAULT_LANG]["label"],
                        value=LOCALES["image_kb"][DEFAULT_LANG]["choices"][0],
                    )

                    custom_image_kb_size = gr.Slider(
                        minimum=10,
                        maximum=1000,
                        value=50,
                        label=LOCALES["image_kb_size"][DEFAULT_LANG]["label"],
                        interactive=True,
                        visible=False,
                    )

                    image_dpi_options = gr.Radio(
                        choices=LOCALES["image_dpi"][DEFAULT_LANG]["choices"],
                        label=LOCALES["image_dpi"][DEFAULT_LANG]["label"],
                        value=LOCALES["image_dpi"][DEFAULT_LANG]["choices"][0],
                    )
                    custom_image_dpi_size = gr.Slider(
                        minimum=72,
                        maximum=600,
                        value=300,
                        label=LOCALES["image_dpi_size"][DEFAULT_LANG]["label"],
                        interactive=True,
                        visible=False,
                    )

                # TAB3 - 美颜 ------------------------------------------------
                with gr.Tab(
                    LOCALES["beauty_tab"][DEFAULT_LANG]["label"]
                ) as beauty_parameter_tab:
                    # 美白组件
                    whitening_option = gr.Slider(
                        label=LOCALES["whitening_strength"][DEFAULT_LANG]["label"],
                        minimum=0,
                        maximum=15,
                        value=2,
                        step=1,
                        interactive=True,
                    )

                    with gr.Row():
                        # 亮度组件
                        brightness_option = gr.Slider(
                            label=LOCALES["brightness_strength"][DEFAULT_LANG]["label"],
                            minimum=-5,
                            maximum=25,
                            value=0,
                            step=1,
                            interactive=True,
                        )
                        # 对比度组件
                        contrast_option = gr.Slider(
                            label=LOCALES["contrast_strength"][DEFAULT_LANG]["label"],
                            minimum=-10,
                            maximum=50,
                            value=0,
                            step=1,
                            interactive=True,
                        )
                        # 饱和度组件
                        saturation_option = gr.Slider(
                            label=LOCALES["saturation_strength"][DEFAULT_LANG]["label"],
                            minimum=-10,
                            maximum=50,
                            value=0,
                            step=1,
                            interactive=True,
                        )

                    # 锐化组件
                    sharpen_option = gr.Slider(
                        label=LOCALES["sharpen_strength"][DEFAULT_LANG]["label"],
                        minimum=0,
                        maximum=5,
                        value=0,
                        step=1,
                        interactive=True,
                    )

                # TAB4 - 水印 ------------------------------------------------
                with gr.Tab(
                    LOCALES["watermark_tab"][DEFAULT_LANG]["label"]
                ) as watermark_parameter_tab:
                    watermark_options = gr.Radio(
                        choices=LOCALES["watermark_switch"][DEFAULT_LANG]["choices"],
                        label=LOCALES["watermark_switch"][DEFAULT_LANG]["label"],
                        value=LOCALES["watermark_switch"][DEFAULT_LANG]["choices"][0],
                    )

                    with gr.Row():
                        watermark_text_options = gr.Text(
                            label=LOCALES["watermark_text"][DEFAULT_LANG]["label"],
                            value=LOCALES["watermark_text"][DEFAULT_LANG]["value"],
                            placeholder=LOCALES["watermark_text"][DEFAULT_LANG][
                                "placeholder"
                            ],
                            interactive=False,
                        )
                        watermark_text_color = gr.ColorPicker(
                            label=LOCALES["watermark_color"][DEFAULT_LANG]["label"],
                            interactive=False,
                            value="#FFFFFF",
                        )

                    watermark_text_size = gr.Slider(
                        minimum=10,
                        maximum=100,
                        value=20,
                        label=LOCALES["watermark_size"][DEFAULT_LANG]["label"],
                        interactive=False,
                        step=1,
                    )

                    watermark_text_opacity = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0.15,
                        label=LOCALES["watermark_opacity"][DEFAULT_LANG]["label"],
                        interactive=False,
                        step=0.01,
                    )

                    watermark_text_angle = gr.Slider(
                        minimum=0,
                        maximum=360,
                        value=30,
                        label=LOCALES["watermark_angle"][DEFAULT_LANG]["label"],
                        interactive=False,
                        step=1,
                    )

                    watermark_text_space = gr.Slider(
                        minimum=10,
                        maximum=200,
                        value=25,
                        label=LOCALES["watermark_space"][DEFAULT_LANG]["label"],
                        interactive=False,
                        step=1,
                    )

                    def update_watermark_text_visibility(choice, language):
                        return [
                            gr.update(
                                interactive=(
                                    choice
                                    == LOCALES["watermark_switch"][language]["choices"][
                                        1
                                    ]
                                )
                            )
                        ] * 6

                    watermark_options.change(
                        fn=update_watermark_text_visibility,
                        inputs=[watermark_options, language_options],
                        outputs=[
                            watermark_text_options,
                            watermark_text_color,
                            watermark_text_size,
                            watermark_text_opacity,
                            watermark_text_angle,
                            watermark_text_space,
                        ],
                    )
                
                # TAB5 - 打印 ------------------------------------------------
                with gr.Tab(
                    LOCALES["print_tab"][DEFAULT_LANG]["label"]
                ) as print_parameter_tab:
                    print_options = gr.Radio(
                        choices=LOCALES["print_switch"][DEFAULT_LANG]["choices"],
                        label=LOCALES["print_switch"][DEFAULT_LANG]["label"],
                        value=LOCALES["print_switch"][DEFAULT_LANG]["choices"][0],
                        interactive=True,
                    )
                

                img_but = gr.Button(
                    LOCALES["button"][DEFAULT_LANG]["label"],
                    elem_id="btn",
                    variant="primary"
                )

                example_images = gr.Examples(
                    inputs=[img_input],
                    examples=[
                        [path.as_posix()]
                        for path in sorted(
                            pathlib.Path(os.path.join(root_dir, "demo/images")).rglob(
                                "*.jpg"
                            )
                        )
                    ],
                )

            # ---------------- 右半边 UI ----------------
            with gr.Column():
                notification = gr.Text(
                    label=LOCALES["notification"][DEFAULT_LANG]["label"], visible=False
                )
                with gr.Row():
                    # 标准照
                    img_output_standard = gr.Image(
                        label=LOCALES["standard_photo"][DEFAULT_LANG]["label"],
                        height=350,
                        format="png",
                    )
                    # 高清照
                    img_output_standard_hd = gr.Image(
                        label=LOCALES["hd_photo"][DEFAULT_LANG]["label"],
                        height=350,
                        format="png",
                    )
                # 排版照
                img_output_layout = gr.Image(
                    label=LOCALES["layout_photo"][DEFAULT_LANG]["label"],
                    height=350,
                    format="png",
                )
                # 模版照片
                with gr.Accordion(
                    LOCALES["template_photo"][DEFAULT_LANG]["label"], open=False
                ) as template_image_accordion:      
                    img_output_template = gr.Gallery(
                        label=LOCALES["template_photo"][DEFAULT_LANG]["label"],
                        height=350,
                        format="png",
                    )
                # 抠图图像
                with gr.Accordion(
                    LOCALES["matting_image"][DEFAULT_LANG]["label"], open=False
                ) as matting_image_accordion:
                    with gr.Row():
                        img_output_standard_png = gr.Image(
                            label=LOCALES["standard_photo_png"][DEFAULT_LANG]["label"],
                            height=350,
                            format="png",
                            elem_id="standard_photo_png",
                        )
                        img_output_standard_hd_png = gr.Image(
                            label=LOCALES["hd_photo_png"][DEFAULT_LANG]["label"],
                            height=350,
                            format="png",
                            elem_id="hd_photo_png",
                        )

            # ---------------- 多语言切换函数 ----------------
            def change_language(language):
                return {
                    face_detect_model_options: gr.update(
                        label=LOCALES["face_model"][language]["label"]
                    ),
                    matting_model_options: gr.update(
                        label=LOCALES["matting_model"][language]["label"]
                    ),
                    size_list_options: gr.update(
                        label=LOCALES["size_list"][language]["label"],
                        choices=LOCALES["size_list"][language]["choices"],
                        value=LOCALES["size_list"][language]["choices"][0],
                    ),
                    mode_options: gr.update(
                        label=LOCALES["size_mode"][language]["label"],
                        choices=LOCALES["size_mode"][language]["choices"],
                        value=LOCALES["size_mode"][language]["choices"][0],
                    ),
                    color_options: gr.update(
                        label=LOCALES["bg_color"][language]["label"],
                        choices=LOCALES["bg_color"][language]["choices"],
                        value=LOCALES["bg_color"][language]["choices"][0],
                    ),
                    img_but: gr.update(value=LOCALES["button"][language]["label"]),
                    render_options: gr.update(
                        label=LOCALES["render_mode"][language]["label"],
                        choices=LOCALES["render_mode"][language]["choices"],
                        value=LOCALES["render_mode"][language]["choices"][0],
                    ),
                    image_kb_options: gr.update(
                        label=LOCALES["image_kb_size"][language]["label"],
                        choices=LOCALES["image_kb"][language]["choices"],
                        value=LOCALES["image_kb"][language]["choices"][0],
                    ),
                    custom_image_kb_size: gr.update(
                        label=LOCALES["image_kb"][language]["label"]
                    ),
                    notification: gr.update(
                        label=LOCALES["notification"][language]["label"]
                    ),
                    img_output_standard: gr.update(
                        label=LOCALES["standard_photo"][language]["label"]
                    ),
                    img_output_standard_hd: gr.update(
                        label=LOCALES["hd_photo"][language]["label"]
                    ),
                    img_output_standard_png: gr.update(
                        label=LOCALES["standard_photo_png"][language]["label"]
                    ),
                    img_output_standard_hd_png: gr.update(
                        label=LOCALES["hd_photo_png"][language]["label"]
                    ),
                    img_output_layout: gr.update(
                        label=LOCALES["layout_photo"][language]["label"]
                    ),
                    head_measure_ratio_option: gr.update(
                        label=LOCALES["head_measure_ratio"][language]["label"]
                    ),
                    top_distance_option: gr.update(
                        label=LOCALES["top_distance"][language]["label"]
                    ),
                    key_parameter_tab: gr.update(
                        label=LOCALES["key_param"][language]["label"]
                    ),
                    advance_parameter_tab: gr.update(
                        label=LOCALES["advance_param"][language]["label"]
                    ),
                    watermark_parameter_tab: gr.update(
                        label=LOCALES["watermark_tab"][language]["label"]
                    ),
                    watermark_text_options: gr.update(
                        label=LOCALES["watermark_text"][language]["label"],
                        placeholder=LOCALES["watermark_text"][language]["placeholder"],
                    ),
                    watermark_text_color: gr.update(
                        label=LOCALES["watermark_color"][language]["label"]
                    ),
                    watermark_text_size: gr.update(
                        label=LOCALES["watermark_size"][language]["label"]
                    ),
                    watermark_text_opacity: gr.update(
                        label=LOCALES["watermark_opacity"][language]["label"]
                    ),
                    watermark_text_angle: gr.update(
                        label=LOCALES["watermark_angle"][language]["label"]
                    ),
                    watermark_text_space: gr.update(
                        label=LOCALES["watermark_space"][language]["label"]
                    ),
                    watermark_options: gr.update(
                        label=LOCALES["watermark_switch"][language]["label"],
                        choices=LOCALES["watermark_switch"][language]["choices"],
                        value=LOCALES["watermark_switch"][language]["choices"][0],
                    ),
                    matting_image_accordion: gr.update(
                        label=LOCALES["matting_image"][language]["label"]
                    ),
                    beauty_parameter_tab: gr.update(
                        label=LOCALES["beauty_tab"][language]["label"]
                    ),
                    whitening_option: gr.update(
                        label=LOCALES["whitening_strength"][language]["label"]
                    ),
                    image_dpi_options: gr.update(
                        label=LOCALES["image_dpi"][language]["label"],
                        choices=LOCALES["image_dpi"][language]["choices"],
                        value=LOCALES["image_dpi"][language]["choices"][0],
                    ),
                    custom_image_dpi_size: gr.update(
                        label=LOCALES["image_dpi"][language]["label"]
                    ),
                    brightness_option: gr.update(
                        label=LOCALES["brightness_strength"][language]["label"]
                    ),
                    contrast_option: gr.update(
                        label=LOCALES["contrast_strength"][language]["label"]
                    ),
                    sharpen_option: gr.update(
                        label=LOCALES["sharpen_strength"][language]["label"]
                    ),
                    saturation_option: gr.update(
                        label=LOCALES["saturation_strength"][language]["label"]
                    ),
                    custom_size_width_px: gr.update(
                        label=LOCALES["custom_size_px"][language]["width"]
                    ),
                    custom_size_height_px: gr.update(
                        label=LOCALES["custom_size_px"][language]["height"]
                    ),
                    custom_size_width_mm: gr.update(
                        label=LOCALES["custom_size_mm"][language]["width"]
                    ),
                    custom_size_height_mm: gr.update(
                        label=LOCALES["custom_size_mm"][language]["height"]
                    ),
                    img_output_template: gr.update(
                        label=LOCALES["template_photo"][language]["label"]
                    ),
                    template_image_accordion: gr.update(
                        label=LOCALES["template_photo"][language]["label"]
                    ),
                    plugin_options: gr.update(
                        label=LOCALES["plugin"][language]["label"],
                        choices=LOCALES["plugin"][language]["choices"],
                        value=LOCALES["plugin"][language]["choices"][0],
                    ),
                    print_parameter_tab: gr.update(
                        label=LOCALES["print_tab"][language]["label"]
                    ),
                    print_options: gr.update(
                        label=LOCALES["print_switch"][language]["label"],
                        choices=LOCALES["print_switch"][language]["choices"],
                        value=LOCALES["print_switch"][language]["choices"][0],
                    ),
                }

            def change_visibility(option, lang, locales_key, custom_component):
                return {
                    custom_component: gr.update(
                        visible=option == LOCALES[locales_key][lang]["choices"][-1]
                    )
                }

            def change_color(colors, lang):
                return {
                    custom_color_rgb: gr.update(visible = colors == LOCALES["bg_color"][lang]["choices"][-2]),
                    custom_color_hex: gr.update(visible = colors == LOCALES["bg_color"][lang]["choices"][-1]),
                }
                

            def change_size_mode(size_option_item, lang):
                choices = LOCALES["size_mode"][lang]["choices"]
                # 如果选择自定义尺寸mm
                if size_option_item == choices[3]:
                    return {
                        custom_size_px: gr.update(visible=False),
                        custom_size_mm: gr.update(visible=True),
                        size_list_row: gr.update(visible=False),
                        plugin_options: gr.update(interactive=True),
                    }
                # 如果选择自定义尺寸px
                elif size_option_item == choices[2]:
                    return {
                        custom_size_px: gr.update(visible=True),
                        custom_size_mm: gr.update(visible=False),
                        size_list_row: gr.update(visible=False),
                        plugin_options: gr.update(interactive=True),
                    }
                # 如果选择只换底，则隐藏所有尺寸组件
                elif size_option_item == choices[1]:
                    return {
                        custom_size_px: gr.update(visible=False),
                        custom_size_mm: gr.update(visible=False),
                        size_list_row: gr.update(visible=False),
                        plugin_options: gr.update(interactive=False),
                    }
                # 如果选择预设尺寸，则隐藏自定义尺寸组件
                else:
                    return {
                        custom_size_px: gr.update(visible=False),
                        custom_size_mm: gr.update(visible=False),
                        size_list_row: gr.update(visible=True),
                        plugin_options: gr.update(interactive=True),
                    }

            def change_image_kb(image_kb_option, lang):
                return change_visibility(
                    image_kb_option, lang, "image_kb", custom_image_kb_size
                )

            def change_image_dpi(image_dpi_option, lang):
                return change_visibility(
                    image_dpi_option, lang, "image_dpi", custom_image_dpi_size
                )

            # ---------------- 绑定事件 ----------------
            # 语言切换
            language_options.input(
                change_language,
                inputs=[language_options],
                outputs=[
                    size_list_options,
                    mode_options,
                    color_options,
                    img_but,
                    render_options,
                    image_kb_options,
                    matting_model_options,
                    face_detect_model_options,
                    custom_image_kb_size,
                    notification,
                    img_output_standard,
                    img_output_standard_hd,
                    img_output_standard_png,
                    img_output_standard_hd_png,
                    img_output_layout,
                    head_measure_ratio_option,
                    top_distance_option,
                    key_parameter_tab,
                    advance_parameter_tab,
                    watermark_parameter_tab,
                    watermark_text_options,
                    watermark_text_color,
                    watermark_text_size,
                    watermark_text_opacity,
                    watermark_text_angle,
                    watermark_text_space,
                    watermark_options,
                    matting_image_accordion,
                    beauty_parameter_tab,
                    whitening_option,
                    image_dpi_options,
                    custom_image_dpi_size,
                    brightness_option,
                    contrast_option,
                    sharpen_option,
                    saturation_option,
                    plugin_options,
                    custom_size_width_px,
                    custom_size_height_px,
                    custom_size_width_mm,
                    custom_size_height_mm,
                    img_output_template,
                    template_image_accordion,
                    print_parameter_tab,
                    print_options,
                ],
            )

            # ---------------- 设置隐藏/显示交互效果 ----------------
            # 尺寸模式
            mode_options.input(
                change_size_mode,
                inputs=[mode_options, language_options],
                outputs=[
                    custom_size_px,
                    custom_size_mm,
                    size_list_row,
                    plugin_options,
                ],
            )

            # 颜色
            color_options.input(
                change_color,
                inputs=[color_options, language_options],
                outputs=[custom_color_rgb, custom_color_hex],
            )

            # 图片kb
            image_kb_options.input(
                change_image_kb,
                inputs=[image_kb_options, language_options],
                outputs=[custom_image_kb_size],
            )

            # 图片dpi
            image_dpi_options.input(
                change_image_dpi,
                inputs=[image_dpi_options, language_options],
                outputs=[custom_image_dpi_size],
            )

            img_but.click(
                processor.process,
                inputs=[
                    img_input,
                    mode_options,
                    size_list_options,
                    color_options,
                    render_options,
                    image_kb_options,
                    custom_color_R,
                    custom_color_G,
                    custom_color_B,
                    custom_color_hex_value,
                    custom_size_height_px,
                    custom_size_width_px,
                    custom_size_height_mm,
                    custom_size_width_mm,
                    custom_image_kb_size,
                    language_options,
                    matting_model_options,
                    watermark_options,
                    watermark_text_options,
                    watermark_text_color,
                    watermark_text_size,
                    watermark_text_opacity,
                    watermark_text_angle,
                    watermark_text_space,
                    face_detect_model_options,
                    head_measure_ratio_option,
                    top_distance_option,
                    whitening_option,
                    image_dpi_options,
                    custom_image_dpi_size,
                    brightness_option,
                    contrast_option,
                    sharpen_option,
                    saturation_option,
                    plugin_options,
                    print_options,
                ],
                outputs=[
                    img_output_standard,
                    img_output_standard_hd,
                    img_output_standard_png,
                    img_output_standard_hd_png,
                    img_output_layout,
                    img_output_template,
                    template_image_accordion,
                    notification,
                ],
            )

            # ------------------------ 批量处理 Tab ------------------------
            with gr.Tab("批量处理") as batch_tab:
                with gr.Row():
                    with gr.Column():
                        batch_input = gr.File(
                            file_count="multiple",
                            label="上传多张照片",
                            file_types=["image"],
                        )
                        batch_status = gr.Textbox(
                            label="处理进度",
                            value="等待上传...",
                            interactive=False,
                        )
                        batch_process_btn = gr.Button(
                            "开始批量处理",
                            variant="primary",
                        )
                    with gr.Column():
                        batch_output_gallery = gr.Gallery(
                            label="处理结果",
                            show_label=True,
                            elem_id="gallery",
                            columns=[2],
                            height="auto",
                        )

                # 批量处理的参数设置（复用单张处理的参数逻辑）
                with gr.Accordion("参数设置", open=True):
                    with gr.Row():
                        batch_size_list_options = gr.Dropdown(
                            choices=LOCALES["size_list"][DEFAULT_LANG]["choices"],
                            label=LOCALES["size_list"][DEFAULT_LANG]["label"],
                            value=LOCALES["size_list"][DEFAULT_LANG]["choices"][0],
                        )
                        batch_color_options = gr.Radio(
                            choices=LOCALES["bg_color"][DEFAULT_LANG]["choices"],
                            label=LOCALES["bg_color"][DEFAULT_LANG]["label"],
                            value=LOCALES["bg_color"][DEFAULT_LANG]["choices"][0],
                        )
                    with gr.Row():
                        batch_matting_model = gr.Dropdown(
                            choices=human_matting_models,
                            label=LOCALES["matting_model"][DEFAULT_LANG]["label"],
                            value=human_matting_models[0],
                        )
                        batch_face_model = gr.Dropdown(
                            choices=face_detect_models,
                            label=LOCALES["face_model"][DEFAULT_LANG]["label"],
                            value=DEFAULT_FACE_DETECT_MODEL,
                        )

            # 绑定批量处理事件
            batch_process_btn.click(
                processor.process_batch,
                inputs=[
                    batch_input,
                    batch_size_list_options,
                    batch_color_options,
                    batch_matting_model,
                    batch_face_model,
                ],
                outputs=[batch_output_gallery, batch_status],
            )

            # ------------------------ 文件名自动补全 Tab ------------------------
            with gr.Tab("照片文件名自动补全") as rename_tab:
                gr.Markdown("""
                ### 📸 本地文件夹处理模式
                | 步骤 | 功能 | 说明 |
                |------|------|------|
                | 步骤1 | OCR 识别姓名 | 将文件名改为 `原文件名-识别出的名字` |
                | 手动 | 修正文件名 | 如识别不准确，可手动修改输出目录的文件名 |
                | 步骤3 | Excel 匹配 | 从文件名中提取名字，在 Excel 查找匹配 |

                ### 💡 优点
                - **无需上传下载** - 直接在本地文件夹处理
                - **适合大量照片** - 几百张照片也能快速处理
                - **随时可中断** - 处理一半也能看到中间结果
                """)

                # ==================== 步骤1: OCR 识别 ====================
                with gr.Accordion("📝 步骤1：OCR 识别并添加名字后缀", open=True):
                    gr.Markdown("""
                    **输入照片所在的文件夹绝对路径**

                    例如：
                    - Windows: `C:\\Users\\xxx\\Documents\\照片`
                    - Mac: `/Users/xxx/Documents/照片`
                    """)
                    with gr.Row():
                        with gr.Column():
                            step1_folder = gr.Textbox(
                                label="照片文件夹路径",
                                placeholder="请粘贴文件夹的绝对路径",
                                lines=2,
                            )
                            step1_btn = gr.Button(
                                "步骤1：开始 OCR 识别",
                                variant="primary",
                            )
                            step1_status = gr.Textbox(
                                label="处理状态",
                                value="等待输入...",
                                interactive=False,
                            )
                        with gr.Column():
                            step1_result = gr.Markdown(label="处理结果")

                # ==================== 步骤3: Excel 匹配 ====================
                with gr.Accordion("🔍 步骤3：Excel 匹配并添加行号后缀", open=True):
                    gr.Markdown("""
                    **输入步骤1输出的照片文件夹路径 + Excel 文件路径**

                    照片文件夹通常是：`原文件夹/step1_output/识别成功`
                    """)
                    with gr.Row():
                        with gr.Column():
                            step3_folder = gr.Textbox(
                                label="照片文件夹路径（step1 输出的文件夹）",
                                placeholder="请粘贴照片文件夹的绝对路径",
                                lines=2,
                            )
                            step3_excel_path = gr.Textbox(
                                label="Excel 文件路径",
                                placeholder="请粘贴 Excel 文件的绝对路径",
                                lines=2,
                            )
                            step3_name_column = gr.Textbox(
                                label="姓名列名",
                                value="姓名",
                                placeholder="Excel 中姓名所在的列名",
                            )
                            step3_btn = gr.Button(
                                "步骤3：开始 Excel 匹配",
                                variant="primary",
                            )
                            step3_status = gr.Textbox(
                                label="处理状态",
                                value="等待输入...",
                                interactive=False,
                            )
                        with gr.Column():
                            step3_result = gr.Markdown(label="处理结果")

                # ------------------- 步骤1 处理函数 -------------------
                def process_step1(folder_path):
                    if not folder_path or not folder_path.strip():
                        return "请先输入照片文件夹路径", ""

                    try:
                        renamer = FilenameRenamer()
                        if not renamer.deps_available:
                            return (
                                f"缺少必要依赖: {renamer.deps_missing}\n"
                                "请运行: pip install pandas easyocr pillow openpyxl",
                                "",
                            )

                        result = renamer.step1_ocr_rename(folder_path.strip())

                        if "error" in result:
                            return result["error"], ""

                        result_md = f"""
                        ### 📊 步骤1 处理完成
                        | 状态 | 数量 |
                        |------|------|
                        | 总计 | {result['total']} |
                        | ✅ 识别成功 | {result['success']} |
                        | ❌ 识别失败 | {result['failed']} |

                        ### 💾 输出目录
                        文件已保存到：`{result['output_dir']}`

                        ### 📂 目录结构
                        ```
                        {result['output_dir']}/
                        ├── 识别成功/    ← 这些文件已添加名字后缀
                        └── 识别失败/    ← 这些文件需要手动处理
                        ```

                        ### ✏️ 下一步
                        1. 打开「识别成功」文件夹，手动修改识别错误的文件名
                        2. 保持文件名格式：`原名-名字.jpg`（用 `-` 连接）
                        3. 将修改后的整个文件夹路径填入步骤3
                        """

                        if result["failed_files"]:
                            result_md += "\n#### ❌ 识别失败列表\n"
                            for filename, reason in result["failed_files"]:
                                result_md += f"- `{filename}`: {reason}\n"

                        if result["success_files"]:
                            result_md += "\n#### ✅ 部分识别成功示例\n"
                            for old, new, name in result["success_files"][:10]:
                                result_md += f"- `{old}` → `{new}` (识别: {name})\n"
                            if len(result["success_files"]) > 10:
                                result_md += f"- ... 还有 {len(result['success_files']) - 10} 个文件\n"

                        return (
                            f"步骤1完成！成功 {result['success']} / 总计 {result['total']}",
                            result_md,
                        )

                    except Exception as e:
                        import traceback
                        return f"处理失败: {str(e)}", f"详细错误：\n```\n{traceback.format_exc()}\n```"

                # ------------------- 步骤3 处理函数 -------------------
                def process_step3(folder_path, excel_path, name_column):
                    if not folder_path or not excel_path or not folder_path.strip() or not excel_path.strip():
                        return "请先输入照片文件夹路径和 Excel 文件路径", ""

                    try:
                        renamer = FilenameRenamer()
                        if not renamer.deps_available:
                            return (
                                f"缺少必要依赖: {renamer.deps_missing}\n"
                                "请运行: pip install pandas easyocr pillow openpyxl",
                                "",
                            )

                        result = renamer.step3_excel_match_rename(
                            folder_path.strip(),
                            excel_path.strip(),
                            name_column.strip(),
                        )

                        if "error" in result:
                            return result["error"], ""

                        result_md = f"""
                        ### 📊 步骤3 处理完成
                        | 状态 | 数量 |
                        |------|------|
                        | 总计 | {result['total']} |
                        | ✅ 匹配成功 | {result['matched']} |
                        | ❌ 未匹配 | {result['unmatched']} |

                        ### 💾 输出目录
                        文件已保存到：`{result['output_dir']}`

                        ### 📂 目录结构
                        ```
                        {result['output_dir']}/
                        ├── 匹配成功/    ← 这些文件已添加行号后缀
                        └── 未匹配/      ← 这些文件需要手动检查
                        ```
                        """

                        if result["matched_files"]:
                            result_md += "\n#### ✅ 匹配成功示例\n"
                            for old, new, name, row in result["matched_files"][:10]:
                                result_md += f"- `{old}` → `{new}` (行号: {row})\n"
                            if len(result["matched_files"]) > 10:
                                result_md += f"- ... 还有 {len(result['matched_files']) - 10} 个文件\n"

                        if result["unmatched_files"]:
                            result_md += "\n#### ❌ 未匹配列表\n"
                            for old, name, reason in result["unmatched_files"][:20]:
                                result_md += f"- `{old}` (提取名字: {name or '无'}, 原因: {reason})\n"
                            if len(result["unmatched_files"]) > 20:
                                result_md += f"- ... 还有 {len(result['unmatched_files']) - 20} 个文件\n"

                        return (
                            f"步骤3完成！匹配成功 {result['matched']} / 总计 {result['total']}",
                            result_md,
                        )

                    except Exception as e:
                        import traceback
                        return f"处理失败: {str(e)}", f"详细错误：\n```\n{traceback.format_exc()}\n```"

                # ------------------- 绑定事件 -------------------
                step1_btn.click(
                    process_step1,
                    inputs=[step1_folder],
                    outputs=[step1_status, step1_result],
                )

                step3_btn.click(
                    process_step3,
                    inputs=[step3_folder, step3_excel_path, step3_name_column],
                    outputs=[step3_status, step3_result],
                )

    return demo
