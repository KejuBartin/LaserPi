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

                # Update timing from Link unless override mode is active.
                try:
                    snapshot = control_state.snapshot()
                    if bool(getattr(snapshot, "motion_override_bpm", False)):
                        # In override mode, keep local BPM/phase from the slider-driven clock.
                        continue
                    control_state.update(
                        bpm=getattr(link, "tempo", snapshot.bpm),
                        beat_phase=getattr(link, "phase", snapshot.beat_phase),
                    )
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
