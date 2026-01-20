import threading

LLM_SEMAPHORE = threading.Semaphore(3)