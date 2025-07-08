import os
import sys
import argparse
from PIL import Image
import numpy as np

def auto_split_characters(image, min_width=2):
    """
    自动横向切割图片中的字符块，返回每个字符的(x0, y0, x1, y1)
    """
    arr = np.array(image)
    h, w = arr.shape[0], arr.shape[1]
    # 统计每一列是否有非透明像素
    if arr.shape[2] == 4:
        alpha = arr[:, :, 3]
        col_has = np.any(alpha > 0, axis=0)
    else:
        col_has = np.any(np.any(arr[:, :3] != 255, axis=2), axis=0)
    # 找到字符区间
    bounds = []
    in_char = False
    for x in range(w):
        if col_has[x] and not in_char:
            start = x
            in_char = True
        elif not col_has[x] and in_char:
            end = x
            if end - start >= min_width:
                bounds.append((start, end))
            in_char = False
    if in_char:
        end = w
        if end - start >= min_width:
            bounds.append((start, end))
    # 返回每个字符的(x0, y0, x1, y1)
    char_boxes = []
    for (x0, x1) in bounds:
        # 上下全高
        char_boxes.append((x0, 0, x1, h))
    return char_boxes

def save_char_images(image, char_boxes, output_dir, margin=2):
    os.makedirs(output_dir, exist_ok=True)
    char_paths = []
    for idx, (x0, y0, x1, y1) in enumerate(char_boxes):
        # 左右各加margin
        x0m = max(0, x0 - margin)
        x1m = min(image.width, x1 + margin)
        char_img = image.crop((x0m, y0, x1m, y1))
        out_path = os.path.join(output_dir, f"char_{idx}.png")
        char_img.save(out_path)
        char_paths.append(out_path)
    return char_paths

def write_mapping_template(char_paths, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, path in enumerate(char_paths):
            f.write(f"char_{idx}=\n")
    print(f"[提示] 映射模板已生成: {output_path}")

def read_mapping(mapping_path, n):
    mapping = []
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                _, ch = line.strip().split('=', 1)
                mapping.append(ch)
    if len(mapping) != n:
        raise ValueError(f"映射文件字符数({len(mapping)})与切割图片数({n})不符")
    return mapping

def gen_font_atlas(char_paths, output_img_path, margin=1):
    # 横向拼接所有字符图片
    imgs = [Image.open(p) for p in char_paths]
    heights = [im.height for im in imgs]
    max_h = max(heights)
    widths = [im.width for im in imgs]
    total_w = sum(widths) + margin * (len(imgs) - 1)
    atlas = Image.new('RGBA', (total_w, max_h), (0, 0, 0, 0))
    x = 0
    rects = []
    for im in imgs:
        atlas.paste(im, (x, 0))
        rects.append((x, 0, im.width, im.height))
        x += im.width + margin
    atlas.save(output_img_path)
    return rects, max_h

def gen_fnt_file(fnt_path, chars, rects, img_name, line_height):
    # BMFont文本格式
    with open(fnt_path, 'w', encoding='utf-8') as f:
        f.write(f"info face=\"custom\" size={line_height} bold=0 italic=0 charset=\"\" unicode=0 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1\n")
        f.write(f"common lineHeight={line_height} base=0 scaleW=0 scaleH=0 pages=1 packed=0\n")
        f.write(f"page id=0 file=\"{img_name}\"\n")
        f.write(f"chars count={len(chars)}\n")
        for i, ch in enumerate(chars):
            ch_id = ord(ch) if ch else 32
            x, y, w, h = rects[i]
            f.write(f"char id={ch_id} x={x} y={y} width={w} height={h} xoffset=0 yoffset=0 xadvance={w} page=0 chnl=0\n")
    print(f"[完成] .fnt文件已生成: {fnt_path}")

def main():
    parser = argparse.ArgumentParser(description='图片字体切割与.fnt生成工具')
    parser.add_argument('--input', required=True, help='输入图片路径')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--char-order', help='字符顺序字符串')
    parser.add_argument('--mapping', help='字符映射文件路径')
    parser.add_argument('--only-cut', action='store_true', help='只切割图片并生成映射模板')
    args = parser.parse_args()

    image = Image.open(args.input).convert('RGBA')
    char_boxes = auto_split_characters(image)
    char_dir = os.path.join(args.output, 'chars')
    char_paths = save_char_images(image, char_boxes, char_dir)
    print(f"[信息] 已切割{len(char_paths)}个字符图片，保存在: {char_dir}")

    if args.only_cut or (not args.char_order and not args.mapping):
        # 只切割图片，生成映射模板
        mapping_path = os.path.join(args.output, 'mapping.txt')
        write_mapping_template(char_paths, mapping_path)
        print("[提示] 请填写mapping.txt后再运行本脚本生成.fnt")
        return

    if args.char_order:
        chars = list(args.char_order)
        if len(chars) != len(char_paths):
            print(f"[错误] 字符顺序数量({len(chars)})与切割图片数({len(char_paths)})不符")
            sys.exit(1)
    elif args.mapping:
        chars = read_mapping(args.mapping, len(char_paths))
    else:
        print("[错误] 未指定字符顺序或映射文件")
        sys.exit(1)

    # 生成图集和fnt
    atlas_path = os.path.join(args.output, 'font.png')
    rects, max_h = gen_font_atlas(char_paths, atlas_path)
    fnt_path = os.path.join(args.output, 'font.fnt')
    gen_fnt_file(fnt_path, chars, rects, os.path.basename(atlas_path), max_h)
    print(f"[完成] 字体图集已生成: {atlas_path}")

if __name__ == '__main__':
    main()
