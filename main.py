import subprocess
from time import sleep
import xml.etree.ElementTree as ET
import signal

def get_ui_xml_tree():
    prcs = subprocess.run(["adb", "exec-out", "uiautomator", "dump", "/dev/tty"], capture_output=True)
    ui_xml = prcs.stdout.rstrip(b"UI hierchary dumped to: /dev/tty\n")
    if signal_received:
        return None

    return ET.fromstring(ui_xml)

def open_pixel_screenshots():
    subprocess.run(["adb", "shell", "am", "start", "-n", "com.google.android.apps.pixel.agent/.app.ui.browser.BrowserActivity", "--activity-clear-task"], capture_output=True)

def open_first_screenshot():
    # find first screenshot on ui xml
    node = get_ui_xml_tree().find(""".//node[@class='android.view.View'][@long-clickable="true"]""")
    press_node(node)

def press_node(node):
    # get bounds attribute value
    bounds_str = node.attrib['bounds']
    
    # parse it as two-dimensional strings array
    bounds = [i.split(',') for i in bounds_str[1:-1].split('][')]
    
    # convert strings to coordinates
    [x1, y1], [x2, y2] = [[int(i[0]), int(i[1])] for i in bounds]
    
    # compute center coordinates
    x = x1 + ((x2-x1)/2)
    y = y1 + ((y2-y1)/2)

    subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])

def next_screenshot():
    subprocess.run(['adb', 'shell', 'input', 'swipe', '800', '1000', '200', '1000', '20'])

def get_process_now_button(ui):
    return ui.find(""".//node[@text="Process now"]""")

def get_screenshot_title(ui):
    node = ui.find(""".//node[@resource-id="ContainerTitleTag"]/node[@class="android.widget.TextView"]""")
    if node is None:
        node = ui.find(""".//node[@resource-id="ContainerTitleTag"]//node[@class="android.widget.TextView"]""")
    if node is None:
        return ""
    return node.attrib['text']

signal_received = False
def signal_handler(sig, frame):
    global signal_received
    print("received interrupt signal...")
    signal_received = True

animations_delay = 0.5


if __name__ == '__main__':
    open_pixel_screenshots()
    open_first_screenshot()
    signal.signal(signal.SIGINT, signal_handler)

    processed_screenshots = 0
    screenshot_title_repeats = 0
    previous_screenshot_title = ""
    while screenshot_title_repeats < 10 and not signal_received:
        ui = get_ui_xml_tree()
        if signal_received:
            break

        
        current_screenshot_title = get_screenshot_title(ui)
        if previous_screenshot_title != current_screenshot_title:
            screenshot_title_repeats = 0
            previous_screenshot_title = current_screenshot_title
        else:
            screenshot_title_repeats += 1

        process_now_btn = get_process_now_button(ui)
        if process_now_btn is not None:
            processed_screenshots += 1
            press_node(process_now_btn)
            sleep(animations_delay)

        next_screenshot()

    print(f"finished! processed {processed_screenshots} screenshots")
