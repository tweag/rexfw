from pickle import dumps
from struct import pack
from socket import socket

from rexfw.statistics.writers import AbstractStatisticsWriter

# timestamp is the number of seconds since unix epoch time.
# Carbon-cache will use the time of arrival if the timestamp is set to -1.
# https://graphite.readthedocs.io/en/stable/feeding-carbon.html


class GraphiteStatisticsWriter(AbstractStatisticsWriter):
    """
    Writes statistics to Graphite server.
    :param str job_name
    :param str graphite_url
    :param int graphite_port
    """

    def __init__(
        self,
        job_name,
        variables_to_write=[],
        quantities_to_write=[],
        graphite_url="127.0.0.1",
        graphite_port=2004,
    ):
        super(GraphiteStatisticsWriter, self).__init__("", variables_to_write,
                                                       quantities_to_write)
        self.job_name = job_name
        self.sock = socket()
        self.sock.connect((graphite_url, graphite_port))

    def make_tuples_list(self, step, elements):
        # export list of (path, (timestamp, value)). for more info look at:
        # https://graphite.readthedocs.io/en/stable/feeding-carbon.html
        return []

    def write(self, step, elements):
        list_of_stats_tuples = self.make_tuples_list(step, elements)
        payload = dumps(list_of_stats_tuples, protocol=2)
        size = pack("!L", len(payload))
        self.sock.sendall(size)
        self.sock.sendall(payload)
        # TODO: for large size of data, they should be pushed once a certain number of samples
        # (METRICS_BUFFER_SIZE) are buffered or upon a defined period of time (MAX_BUFFER _TIME)
        # For more info look at
        # https://www.metricfire.com/blog/monitoring-with-graphite-installation-and-setup/


class GraphiteREStatisticsWriter(GraphiteStatisticsWriter):
    def make_tuples_list(self, step, elements):
        timestamp = -1
        list_of_stats_tuples = []
        for e in elements:
            if e.name == "acceptance rate" and len(e.origins) == 2:
                path = self.job_name + "." + "_".join(e.origins) + "." + "acceptance_rate"
                list_of_stats_tuples.append((path, (timestamp, e.current_value)))
        return list_of_stats_tuples


class GraphiteMCMCStatisticsWriter(GraphiteStatisticsWriter):
    def make_tuples_list(self, step, elements):
        timestamp = -1
        list_of_stats_tuples = []
        for e in elements:
            log_this = False
            path_template = self.job_name + "." + e.origins[0] + ".{}"
            if e.name == "acceptance rate" and len(e.origins) == 1:
                path = path_template.format("acceptance_rate")
                log_this = True
            if e.name == "stepsize":
                path = path_template.format("stepsize")
                log_this = True
            if e.name == "neg_log_prob":
                path = path_template.format("negative_log_prob")
                log_this = True
            if log_this:
                list_of_stats_tuples.append((path, (timestamp, float(e.current_value))))
        return list_of_stats_tuples