from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from yt_thumbsense.config import get_settings

settings = get_settings()

redis_conn = Redis.from_url(settings.redis_url)
main_queue = Queue("main", connection=redis_conn)
scheduler = Scheduler(queue=main_queue, connection=redis_conn)

if __name__ == "__main__":
    from rq import Worker

    worker = Worker([main_queue])
    worker.work(with_scheduler=True)
