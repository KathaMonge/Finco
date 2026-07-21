from concurrent.futures import ThreadPoolExecutor


OCR_EXECUTOR = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="ocr",
)

IO_EXECUTOR = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="io",
)
