import can
import threading
import queue
import time

# ==== Configuration ====
LOG_FILE = "/home/mobase/Can_FD/Tcan_communication_0.asc"
CAN_INTERFACE = "can0"
QUEUE_SIZE = 10000  # Limit for the message queue to avoid memory issues

# ==== Globals ====
msg_queue = queue.Queue(maxsize=QUEUE_SIZE)
dropped_count = 0
stop_flag = threading.Event()

# ==== Setup CAN FD Interface ====
bus = can.interface.Bus(channel=CAN_INTERFACE, bustype="socketcan", fd=True)
logger = can.Logger(LOG_FILE, file_format="asc")


def receiver():
    """Receives CAN FD messages and puts them in a queue."""
    global dropped_count
    print("📡 Receiver thread started.")
    while not stop_flag.is_set():
        try:
            msg = bus.recv(timeout=1.0)
            if msg:
                try:
                    msg_queue.put_nowait(msg)
                except queue.Full:
                    dropped_count += 1
        except Exception as e:
            print("❌ Receiver error:", e)
            break


def writer():
    """Takes messages from the queue and logs them."""
    print("💾 Writer thread started.")
    while not stop_flag.is_set():
        try:
            msg = msg_queue.get(timeout=1.0)
            if msg is None:
                break
            logger.log_message(msg)
        except queue.Empty:
            continue
        except Exception as e:
            print("❌ Logger error:", e)
            break


# ==== Main Script ====

recv_thread = threading.Thread(target=receiver, daemon=True)
log_thread = threading.Thread(target=writer, daemon=True)

recv_thread.start()
log_thread.start()

print(f"🔴 CAN FD logging started on {CAN_INTERFACE}. Logging to: {LOG_FILE}")

try:
    while True:
        time.sleep(5)
        print(f"✅ Logging running... Dropped frames: {dropped_count}")
except KeyboardInterrupt:
    print("\n🛑 Stopping logging...")

    stop_flag.set()
    msg_queue.put(None)  # Unblock writer thread

    log_thread.join()
    recv_thread.join()

    logger.stop()
    bus.shutdown()

    print(f"✅ Logging complete. Total dropped frames: {dropped_count}")
