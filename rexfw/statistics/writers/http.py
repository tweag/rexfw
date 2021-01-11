'''
Statistics writer classes which send statistics via HTTP to
a server.
'''
import requests
import json
from abc import abstractmethod

from rexfw.statistics.writers import (AbstractStatisticsWriter,
                                      sort_mcmc_quantities,
                                      sort_re_quantities)


class LoggingError(Exception):
    def __init__(self, response):
        msg = ("Sending sampling statistics to URL {} failed. "
               "Response content is as follows:\n{}")
        super().__init__(msg.format(response.request.url,
                                    response.content))


class AbstractHTTPStatisticsWriter(AbstractStatisticsWriter):
    # prefix the data key in the JSON to be sent with
    # something informative in subclasses
    _data_prefix = ""
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
    def _sanitize_value(self, value):
        '''
        Sanitize a quantity's current value, e.g., for an acceptance
        rate, replace None by 0.0

        :param value: a quantity's current value
        :type value: could be literally anything
        '''
        pass
    
    @abstractmethod
    def _sort_quantities(self, quantities):
        pass

    def _make_data_dict(self, elements):
        '''
        Make a dictionary (which can be serialized to JSON) from the data
        in elements.

        :param elements: list of quantities to write
        :type elements: list of :class:`.LoggedQuantity`
        '''
        statistics_data = {}
        for quantity_name in set([quantity.name
                                  for quantity in elements]):
            filtered_quantities = elements.select(name=quantity_name)
            sorted_quantities = self._sort_quantities(filtered_quantities)
            data = self._quantities_to_JSONable_dict(quantity_name,
                                                     sorted_quantities)
            statistics_data.update(**data)
        all_data = {"{}statistics".format(self._data_prefix): statistics_data}

        return all_data

    def _augment_with_metadata(self, all_data, step):
        all_data['mcmc_step'] = step
        return all_data
    
    def write(self, step, elements):
        '''
        Sends values of quantities in elements for a given
        step to the HTTP endpoint.

        :param step: sampling step
        :type step: int
        :param elements: list of quantities to write
        :type elements: list of :class:`.LoggedQuantity`
        '''
        all_data = self._make_data_dict(elements)
        self._augment_with_metadata(all_data, step)
        response = requests.post(self._http_endpoint,
                                 json=json.dumps(all_data))
        if not response.ok:
            raise LoggingError(response)


class REHTTPStatisticsWriter(AbstractHTTPStatisticsWriter):
    _data_prefix = "re_"
    
    def _sort_quantities(self, quantities):
        return sort_re_quantities(quantities)

    def _sanitize_value(self, value):
        return 0.0 if value is None else value

class MCMCHTTPStatisticsWriter(AbstractHTTPStatisticsWriter):
    _data_prefix = "mcmc_"
    
    def _sort_quantities(self, quantities):
        return sort_mcmc_quantities(quantities)

    def _sanitize_value(self, value):
        return 0.0 if value is None else value
