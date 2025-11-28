from datetime import datetime
LOG_INFO = "INFO"
LOG_DEBUG = "DEBUG"

LOG_PATH = "/tmp/game_client.log"

def glog(message, type=LOG_INFO):
    current_time = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
    with open(LOG_PATH, "a") as log:
        log.write(f"[{current_time}] {type} -> {message}\n")

