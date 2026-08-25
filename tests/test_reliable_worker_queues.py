from nanexus.queue import AIQueue, ChatQueueJob, SummaryJob


class FakeRedis:
    def __init__(self):
        self.lists = {}

    def lpush(self, key, value):
        self.lists.setdefault(key, []).insert(0, value)

    def brpoplpush(self, source, destination, timeout=0):
        values = self.lists.get(source, [])
        if not values:
            return None
        payload = values.pop()
        self.lpush(destination, payload)
        return payload

    def rpoplpush(self, source, destination):
        return self.brpoplpush(source, destination)

    def lrem(self, key, count, value):
        values = self.lists.get(key, [])
        if value not in values:
            return 0
        values.remove(value)
        return 1

    def lrange(self, key, start, stop):
        return list(self.lists.get(key, []))


def test_summary_in_flight_recovery_and_ack():
    client = FakeRedis()
    queue = AIQueue(client)
    job = SummaryJob(summary_date="2026-08-24")
    queue.enqueue_summary(job)
    assert queue.dequeue_summary(timeout=0) == job
    assert queue.recover_summaries() == 1
    claimed = queue.dequeue_summary(timeout=0)
    queue.acknowledge_summary(claimed)
    assert client.lists[f"{queue._settings.summary_queue_key}:processing"] == []


def test_chat_in_flight_recovery_and_ack():
    client = FakeRedis()
    queue = AIQueue(client)
    job = ChatQueueJob(job_id="00000000-0000-0000-0000-000000000001")
    queue.enqueue_chat(job)
    assert queue.dequeue_chat(timeout=0) == job
    assert queue.recover_chats() == 1
    claimed = queue.dequeue_chat(timeout=0)
    queue.acknowledge_chat(claimed)
    assert client.lists[f"{queue._settings.chat_queue_key}:processing"] == []
