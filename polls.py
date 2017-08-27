import strawpy


class Poll(object):

    def __init__(self, poll_id):
        self.poll_id = poll_id
        self.poll = strawpy.get_poll(self.poll_id)


    def top(self):
        """
        return a list of subreddits, sorted by popularity, according to the
        amount of votes received on StrawPoll.

        Returns a list of requested subreddits from top to bottom.
        """
        return [tup[0] for tup in sorted(self.poll.results_with_percent, key=lambda t: t[1])]

