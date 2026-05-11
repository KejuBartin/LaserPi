import threading
import asyncio

def start_ableton_link(control_state, interval=0.016):
    try:
        import aalink
    except Exception:
        return None

    stop_flag = threading.Event()

    def thread_fn():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def init_and_run():
            link = aalink.Link(120)
            link.enabled = True

            while not stop_flag.is_set():
                try:
                    await link.sync(interval)
                except Exception:
                    # if link fails temporarily, continue
                    await asyncio.sleep(interval)
                    continue

                # update shared state with link tempo and phase
                try:
                    control_state.update(bpm=getattr(link, 'tempo', control_state.snapshot().bpm),
                                         beat_phase=getattr(link, 'phase', control_state.snapshot().beat_phase))
                except Exception:
                    pass

        try:
            loop.run_until_complete(init_and_run())
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    thread = threading.Thread(target=thread_fn, daemon=True)
    thread.start()

    def stop():
        stop_flag.set()
        thread.join(timeout=1.0)

    return stop
