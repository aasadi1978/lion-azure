from lion.orm.cost import Cost


class TourCost():

    # Cost break-down: https://chatgpt.com/share/678d54c8-6520-8003-a491-6977358dc618
    def __init__(self):
        self.__dct_operator_cost = {
            'wage_per_hour': 20,
            'eur_per_km': 1.5, 
            'eur_per_min': 0.35, # wage/minute
            'eur_per_min_break_time': 0.6,
            'eur_per_shift': 350}
        
        # Cost.to_dict()
        # self.__default_cost = self.__dct_operator_cost.get('FedEx Express', {})

    @property
    def dct_operator_cost(self):
        return self.__dct_operator_cost

    def calculate_cost(self, dct_tour):
        """
        This module is used to calculate a tour cost regardless of supplier
        If cost info is available in the system, it will be used otherwise, default cost component will be used
        """

        try:

            # operator = dct_tour.get('operator', 'FedEx Express')
            # __dct_operator_cost = self.__dct_operator_cost.get(
            #     operator, self.__default_cost)

            total_empty_dist_cost = dct_tour['tour_repos_dist'] * \
                self.__dct_operator_cost['eur_per_km']

            dct_tour['total_empty_cost'] = total_empty_dist_cost

            break_time_cost = int(0.5 + dct_tour.get('break_time', 0) * self.__dct_operator_cost[
                'eur_per_min_break_time'])
            
            idle_time_cost = int(0.5 + dct_tour['idle_time'] * self.__dct_operator_cost['eur_per_min'])

            dct_tour['break_time_cost'] = break_time_cost
            dct_tour['idle_time_cost'] = idle_time_cost

            dct_tour['tour_variable_cost'] = total_empty_dist_cost + 0.8 * break_time_cost + 1.2 * idle_time_cost

            dct_tour['tour_fixed_cost'] = self.__dct_operator_cost['eur_per_shift']

            dct_tour['total_dist_cost'] = total_empty_dist_cost

            dct_tour['tour_dist'] = dct_tour['tour_repos_dist'] + dct_tour['tour_input_dist']

            dct_tour['tour_cost'] = dct_tour['tour_fixed_cost'] + dct_tour['tour_variable_cost']

        except Exception:
            from lion.logger.status_logger import log_message
            from lion.logger.exception_logger import log_exception
            log_message(message='Tour cost calculation failed! %s' % log_exception(False),
                       module_name='calculate_tour_cost.py/calculate_cost')

            return {}

        return dct_tour

    def calculate_suplier_cost(self, dct_tour, operator='FedEx Express'):
        """
        This module is used to calculate a tour cost per supplier
        """
        try:

            __dct_operator_cost = self.__dct_operator_cost.get(
                operator, {})

            if not __dct_operator_cost:
                raise ValueError(f'No cost was found for {operator}.')

            else:

                dct_tour['operator'] = operator
                total_empty_dist_cost = dct_tour['tour_repos_dist'] * \
                    __dct_operator_cost['eur_per_km']

                total_loaded_dist_cost = dct_tour[
                    'tour_input_dist'] * __dct_operator_cost['eur_per_km']

                dct_tour['total_dist_cost'] = total_empty_dist_cost + \
                    total_loaded_dist_cost

                dct_tour['tour_fixed_cost'] = __dct_operator_cost['eur_per_shift']

                dct_tour['tour_dist'] = dct_tour['tour_repos_dist'] + \
                    dct_tour['tour_input_dist']

                dct_tour['tour_cost'] = dct_tour[
                    'tour_fixed_cost'] + total_empty_dist_cost

        except Exception:
            from lion.logger.status_logger import log_message
            from lion.logger.exception_logger import log_exception
            log_message(message='Tour cost calculation failed! %s' % log_exception(False),
                       module_name='calculate_tour_cost.py/calculate_suplier_cost')

            return {}

        return dct_tour


if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        print(TourCost().dct_operator_cost)
