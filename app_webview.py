import os
import sys
import webview
from ui.web_bridge import WebBridgeAPI

def launch_webview_app():
    api = WebBridgeAPI()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, 'ui', 'web', 'index.html')
    
    url = f"file:///{html_file.replace(os.sep, '/')}"
    window = webview.create_window(
        title='Sentence Jigsaw 3.0',
        url=url,
        js_api=api,
        width=1140,
        height=880,
        min_size=(960, 680),
        text_select=True
    )
    webview.start()

if __name__ == '__main__':
    launch_webview_app()
