'''
Statistics writer classes which send statistics via HTTP to
a server.
'''
import requests
import json
from abc import abstractmethod

from rexfw.statistics.writers import AbstractStatisticsWriter


class LoggingError(Exception):
    def __init__(self, response):
        msg = ("Sending sampling statistics to URL {} failed. "
               "Response content is as follows:\n{}")
        super().__init__(msg.format(response.request.url,
                                    response.content))


class AbstractHTTPStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self, http_endpoint, variables_to_write=[],
                 quantities_to_write=[]):
        '''
        Base class for classes which write sampling statistics
        to HTTP endpoints.

        :param http_endpoint: IP address / host name of HTTP endpoint
        :type http_endpoint: str

        :param variables_to_write: list of sampling variable names for which to
                                   write statistics
        :type variables_to_write: list of str

        :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                    write statistics
        :type quantities_to_write: list of :class:`.LoggedQuantity`
        '''
        super().__init__(variables_to_write, quantities_to_write)
        self._http_endpoint = http_endpoint


    @abstractmethod
    def _quantities_to_JSONable_dict(self, quantity_name, quantities):
        '''
        Turns a list of :class:`.Quantity objects into some Python object that
        can be serialized via JSON.

        :param quantity_name: str
        :param quantities: list of :class:`Quantity objects
        '''
        value_list = [self._sanitize_value(x.current_value)
                      for x in quantities]
        
        return {quantity_name: value_list}

    @abstractmethod
    def _sort_quantities(self, quantities):
        pass

    def _sanitize_value(self, value):
        '''
        TODO: this might need to be customizable, e.g., to replace
        None value for an acceptance rate by 0.0
        '''
        return value
    
    def write(self, step, elements):
        '''
        Sends values of quantities in elements for a given
        step to the HTTP endpoint.

        :param int step: sampling step
        :param elements: list of quantities to write
        :type elements: list of :class:`.LoggedQuantity`
        '''

        metadata = {'mcmc_step': step}
        all_data = metadata
        for quantity_name in set([quantity.name
                                  for quantity in elements]):
            filtered_quantities = elements.select(name=quantity_name)
            # sorted_quantities = map(self._sort_quantities, filtered_quantities)
            data = self._quantities_to_JSONable_dict(quantity_name,
                                                     filtered_quantities)
            all_data.update(**data)

        response = requests.post(self._http_endpoint,
                                 json=json.dumps(all_data))
        if not response.ok:
            raise LoggingError(response)


class REHTTPStatisticsWriter(AbstractHTTPStatisticsWriter):
    def _sort_quantities(self, quantities):
        '''
        TODO: totally copy & pasted from StandardConsoleREStatisticsWriter
        '''
        # for swap statistics such as the acceptance rates, origins is a list
        # of the form ['replica1', 'replica2']. We thus sort by the smaller
        # replica index.
        def key(x): return min([int(y[len('replica'):]) for y in x.origins])
        return sorted(quantities, key=key)


class MCMCHTTPStatisticsWriter(AbstractHTTPStatisticsWriter):
    def _sort_quantities(self, quantities):
        '''
        TODO: totally copy & pasted from StandardFileMCMCStatisticsWriter
        '''
        # for MCMC statistics, there is only one origin, which is
        # a single replica (as compared to swap moves). So we sort by
        # the replica index of the first and only entry of origins.
        def key(x): return int(list(x.origins)[0][len('replica'):])
        return sorted(quantities, key=key)
