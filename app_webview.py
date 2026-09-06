import os
import sys
import logging
from pathlib import Path
import webview
from ui.web_bridge import WebBridgeAPI

logger = logging.getLogger(__name__)

def configure_webview2_permissions():
    """Configures Edge WebView2 on Windows to automatically grant microphone
    and media permissions so the student is never prompted repeatedly during voice mode.
    """
    if sys.platform != 'win32':
        return

    try:
        import webview.platforms.edgechromium as edge
        from Microsoft.Web.WebView2.Core import (
            CoreWebView2PermissionKind,
            CoreWebView2PermissionState,
        )

        orig_init = edge.EdgeChrome.__init__
        orig_ready = edge.EdgeChrome.on_webview_ready

        def patched_init(self, form, window, cache_dir):
            orig_init(self, form, window, cache_dir)
            if hasattr(self, 'webview') and hasattr(self.webview, 'CreationProperties') and self.webview.CreationProperties:
                current_args = self.webview.CreationProperties.AdditionalBrowserArguments or ''
                flags = [
                    '--use-fake-ui-for-media-stream',
                    '--allow-file-access-from-files',
                    '--enable-features=WebSpeechAPI'
                ]
                for f in flags:
                    if f not in current_args:
                        current_args += f' {f}'
                self.webview.CreationProperties.AdditionalBrowserArguments = current_args.strip()

        def patched_ready(self, sender, args):
            orig_ready(self, sender, args)
            if sender and hasattr(sender, 'CoreWebView2') and sender.CoreWebView2:
                def on_permission_requested(s, p_args):
                    try:
                        kind_str = str(p_args.PermissionKind)
                        if p_args.PermissionKind == CoreWebView2PermissionKind.Microphone or 'Microphone' in kind_str:
                            p_args.State = CoreWebView2PermissionState.Allow
                            try:
                                p_args.SavesInProfile = True
                            except Exception:
                                logger.warning("Failed to set SavesInProfile on permission request", exc_info=True)
                            try:
                                p_args.Handled = True
                            except Exception:
                                logger.warning("Failed to set Handled on permission request", exc_info=True)
                        else:
                            p_args.State = CoreWebView2PermissionState.Allow
                    except Exception as err:
                        logger.warning(f"Permission handler error: {err}", exc_info=True)

                sender.CoreWebView2.PermissionRequested += on_permission_requested

        edge.EdgeChrome.__init__ = patched_init
        edge.EdgeChrome.on_webview_ready = patched_ready
    except Exception as e:
        logger.warning(f"Could not configure WebView2 auto-permissions ({e})", exc_info=True)

def launch_webview_app():
    configure_webview2_permissions()
    api = WebBridgeAPI()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, 'ui', 'web', 'index.html')
    url = Path(html_file).as_uri()
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

