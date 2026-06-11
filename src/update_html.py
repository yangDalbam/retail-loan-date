"""
이 스크립트는 dashboard.html 내의 canvas 태그를 레이아웃 조정용 div로 감싸는 작업을 수행합니다.
"""
import os
import re

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, 'report', 'dashboard.html')

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Wrap canvas if not wrapped
    if 'class="canvas-wrapper"' not in content:
        content = re.sub(
            r'(<canvas id="chart\d+"></canvas>)',
            r'<div class="canvas-wrapper" style="position: relative; flex: 1; width: 100%; min-height: 0;">\1</div>',
            content
        )

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("HTML patched")

if __name__ == '__main__':
    main()
