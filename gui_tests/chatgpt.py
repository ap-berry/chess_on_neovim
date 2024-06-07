import threading
import time

# Shared variable
events = []

# Lock for synchronizing access to the shared variable
events_lock = threading.Lock()

def update_events():
    event_id = 1
    while True:
        time.sleep(2)
        with events_lock:
            events.append(f"Event {event_id}")
            event_id += 1
        print(f"Updated events: {events}")

def read_events():
    seen_events = set()
    while True:
        with events_lock:
            new_events = [event for event in events if event not in seen_events]
        if new_events:
            print(f"New events: {new_events}")
            seen_events.update(new_events)
        time.sleep(1)

# Creating threads
updater_thread = threading.Thread(target=update_events)
reader_thread = threading.Thread(target=read_events)

# Starting threads
updater_thread.start()
reader_thread.start()

# Joining threads to the main thread
updater_thread.join()
reader_thread.join()
