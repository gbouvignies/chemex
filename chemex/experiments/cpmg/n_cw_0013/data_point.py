"""
Created on Jun 15, 2017

@author: tyuwen
"""

# Standard imports
from inspect import getargspec

from scipy import pi


# Local imports
from chemex.parsing import parse_assignment
from chemex.experiments.base_data_point import BaseDataPoint
from chemex.constants import xi_ratio
from .back_calculation import make_calc_observable
from ..plotting import plot_data

# Constants
TWO_PI = 2.0 * pi
RATIO_N = xi_ratio['N']

PAR_DICT = {

    # experimental requirements (used in __init__ and check_parameters)
    'par_conv': ((str, ('resonance_id','fh_flg',)),

                 (float, ('h_larmor_frq',
                          'temperature',
                          'carrier',
                          'time_t2',
                          'pw',
                          'time_equil')),

                 (int, ('ncyc', 'ncyc_max',))),

    # Some stuff to get a nice help output
    'exp': ('resonance_id', 'h_larmor_frq', 'temperature', 'carrier',
            'time_t2', 'time_equil', 'pw', 'ncyc', 'ncyc_max', 'fh_flg'),

    'fit': ('pb', 'kex', 'dw', 'i0', 'r_nxy'),

    'fix': ('r_nz', 'dr_nxy', 'cs'),

}


class DataPoint(BaseDataPoint):
    """Intensity measured during a cpmg pulse train of frequency frq"""

    def __init__(self, val, err, par):
        BaseDataPoint.__init__(self, val, err, par, PAR_DICT['par_conv'], plot_data)

        self.par['ppm_to_rads'] = TWO_PI * self.par['h_larmor_frq'] * RATIO_N

        temperature = self.par['temperature']
        resonance_id = self.par['resonance_id']
        h_larmor_frq = self.par['h_larmor_frq']
        experiment_name = self.par['experiment_name']

        index, residue_type, nucleus_type = parse_assignment(resonance_id)[0]
        nucleus_name = residue_type + str(index) + nucleus_type

        self.par['_id'] = tuple((temperature, nucleus_name, h_larmor_frq))

        args = (self.par[arg] for arg in getargspec(make_calc_observable.__wrapped__).args)
        self.calc_observable = make_calc_observable(*args)

        self.kwargs_default = {'ncyc': self.par['ncyc']}

        self.short_long_par_names = (('i0', ('i0', resonance_id, experiment_name)),
                                     ('pb', ('pb', temperature)),
                                     ('kex', ('kex', temperature)),
                                     ('dw', ('dw', nucleus_name)),
                                     ('cs', ('cs', nucleus_name, temperature)),
                                     ('r_nxy', ('r_nxy', nucleus_name, h_larmor_frq, temperature)),
                                     ('dr_nxy', ('dr_nxy', nucleus_name, h_larmor_frq, temperature)),
                                     ('r_nz', ('r_nz', nucleus_name, h_larmor_frq, temperature)),)

        self.fitting_parameter_names.update(long_name
                                            for short_name, long_name in self.short_long_par_names
                                            if short_name in PAR_DICT['fit'])

        self.fixed_parameter_names.update(long_name
                                          for short_name, long_name in self.short_long_par_names
                                          if short_name in PAR_DICT['fix'])

    def __repr__(self):
        """Print the data point"""

        output = list()
        output.append('{resonance_id:6s}'.format(**self.par))
        output.append('{h_larmor_frq:6.1f}'.format(**self.par))
        output.append('{time_t2:6.1e}'.format(**self.par))
        output.append('{ncyc:4d}'.format(**self.par))
        output.append('{temperature:4.1f}'.format(**self.par))
        output.append('{fh_flg:3s}'.format(**self.par))
        output.append('{:10.5f}'.format(self.val))
        output.append('{:10.5f}'.format(self.err))

        if self.cal:
            output.append('{:10.5f}'.format(self.cal))

        return ' '.join(output)



