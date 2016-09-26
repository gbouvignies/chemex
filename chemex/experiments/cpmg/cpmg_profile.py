import copy
from functools import lru_cache

import numpy as np
from chemex import constants, peaks
from chemex.experiments import base_profile
from chemex.experiments.cpmg import plotting


class CPMGProfile(base_profile.BaseProfile):
    def __init__(self, profile_name, measurements, exp_details):

        self.profile_name = profile_name
        self.ncycs = measurements['ncycs']
        self.val = measurements['intensities']
        self.err = measurements['intensities_err']

        self.reference = (self.ncycs == 0)

        self.h_larmor_frq = base_profile.check_par(exp_details, 'h_larmor_frq', float)
        self.temperature = base_profile.check_par(exp_details, 'temperature', float)
        self.time_t2 = base_profile.check_par(exp_details, 'time_t2', float)
        self.pw = base_profile.check_par(exp_details, 'pw', float, 0.0)
        self.p_total = base_profile.check_par(exp_details, 'p_total', float, required=False)
        self.l_total = base_profile.check_par(exp_details, 'l_total', float, required=False)

        self.experiment_name = base_profile.check_par(exp_details, 'name')
        self.model = base_profile.check_par(exp_details, 'model', default='2st.pb_kex')

        self.tau_cp_list = np.array(
            [self.time_t2 / (4.0 * ncyc) - self.pw if ncyc > 0 else
             self.time_t2 / 2.0 if ncyc else
             0.0
             for ncyc in self.ncycs]
        )

        self.plot_data = plotting.plot_data

        self.peak = peaks.Peak(self.profile_name)
        self.resonance_i = self.peak.resonances[0]
        self.ppm_i = 2.0 * np.pi * self.h_larmor_frq * constants.xi_ratio[self.resonance_i['atom']]
        if len(self.peak.resonances) > 1:
            self.resonance_s = self.peak.resonances[1]
            self.ppm_s = 2.0 * np.pi * self.h_larmor_frq * constants.xi_ratio[self.resonance_s['atom']]

        if self.pw > 0.0:
            self.omega1_i = 2.0 * np.pi / (4.0 * self.pw)
        else:
            self.omega1_i = 0.0

        self.calculate_unscaled_profile_cached = lru_cache(5)(self.calculate_unscaled_profile)

        self.map_names = {}

    def calculate_unscaled_profile(self, *args, **kwargs):
        pass

    def calculate_scale(self, cal):

        scale = (
            sum(cal * self.val / self.err ** 2) /
            sum((cal / self.err) ** 2)
        )

        return scale

    def calculate_profile(self, params):

        kwargs = {
            short_name: params[long_name].value
            for short_name, long_name in self.map_names.items()
            }

        values = self.calculate_unscaled_profile_cached(**kwargs)
        scale = self.calculate_scale(values)

        return values * scale

    def ncycs_to_nu_cpmgs(self, ncycs=None):

        if ncycs is None:
            ncycs = np.array([ncyc if ncyc >= 0 else 0.5 for ncyc in self.ncycs])

        return ncycs / self.time_t2

    def filter_points(self, params=None):
        """Evaluate some criteria to know whether the point should be considered
        in the calculation or not.

        Returns 'True' if the point should NOT be considered.
        """

        return False

    def print_profile(self, params=None):
        """Print the data point"""

        output = []

        if params is not None:
            values = self.calculate_profile(params)
        else:
            values = self.val

        iter_vals = list(zip(self.ncycs, self.val, self.err, values))

        output.append("[{}]".format(self.profile_name))
        output.append("# {:>5s}   {:>17s} {:>17s} {:>17s}"
                      .format("ncyc", "intensity (exp)", "uncertainty", "intensity (calc)"))

        for ncyc, val, err, cal in iter_vals:

            line = (
                "  "
                "{0:5.0f} "
                "= "
                "{1:17.8e} "
                "{2:17.8e} "
                    .format(ncyc, val, err)
            )

            if params is not None:
                line += "{:17.8e}".format(cal)
            else:
                line += "{:17s}".format("xxx")

            output.append(line)

        output.append("")
        output.append("")

        return "\n".join(output).upper()

    def make_bs_profile(self):

        indexes = np.array(range(len(self.val)))
        pool1 = indexes[self.reference]
        pool2 = indexes[np.logical_not(self.reference)]

        bs_indexes = []
        if pool1.size:
            bs_indexes.extend(np.random.choice(pool1, len(pool1)))
        bs_indexes.extend(np.random.choice(pool2, len(pool2)))

        bs_indexes = sorted(bs_indexes)

        profile = copy.deepcopy(self)
        profile.ncycs = profile.ncycs[bs_indexes]
        profile.tau_cp_list = profile.tau_cp_list[bs_indexes]
        profile.val = profile.val[bs_indexes]
        profile.err = profile.err[bs_indexes]

        profile.calculate_unscaled_profile_cached = lru_cache(5)(profile.calculate_unscaled_profile)

        return profile
