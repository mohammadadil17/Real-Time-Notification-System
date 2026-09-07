import signal
import sys
import time

from app.core.config import settings
from app.services.batching import scan_due_user_ids
from app.services.digesting import flush_user_batch


def run() -> None:
    print(
        f"[digest-worker] starting, window={settings.batch_window_seconds}s "
        f"poll_interval={settings.digest_poll_interval_seconds}s",
        flush=True,
    )

    running = True

    def _shutdown(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    while running:
        for user_id in scan_due_user_ids():
            try:
                notification = flush_user_batch(user_id)
            except Exception as exc:
                # One user's batch failing (e.g. a transient DB hiccup) must not
                # take down the loop for every other due user.
                print(
                    f"[digest-worker] failed to flush batch for user_id={user_id}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                continue
            if notification is not None:
                print(
                    f"[digest-worker] created digest id={notification.id} "
                    f"for user_id={user_id}: {notification.message!r}",
                    flush=True,
                )
        time.sleep(settings.digest_poll_interval_seconds)


if __name__ == "__main__":
    run()
