import argparse
import importlib
import pkgutil
import sys

from chemex import experiments, util, version


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def arg_parse():
    description = (
        "ChemEx is an analysis program for chemical exchange detected by "
        "NMR. It is designed to take almost any kind of NMR data to aid the "
        "analysis, but the principle techniques are CPMG relaxation "
        "dispersion and Chemical Exchange Saturation Transfer."
    )

    parser = MyParser(
        description=description,
        prog='chemex',
    )

    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(version.__version__))

    subparsers = parser.add_subparsers(dest='commands', )

    parser_info = subparsers.add_parser(
        "info",
        help="Shows classes of experiments that can be fit",
        description="Enter a class of experiments.",
    )

    subparsers_info = parser_info.add_subparsers(dest='types')
    subparsers_info.required = True

    exp_types = [
        name
        for _, name, ispkg in pkgutil.iter_modules(experiments.__path__, experiments.__name__ + '.')
        if ispkg
        ]

    for exp_type in exp_types:

        name_exp_type = exp_type.replace('chemex.experiments.', '')

        package_exp_type = importlib.import_module(exp_type)
        parser_info_type = subparsers_info.add_parser(
            name_exp_type,
            help=package_exp_type.__doc__.split('\n')[0],
            description="Enter an experiment to obtain more info about it.",
        )
        subparsers_info_type = parser_info_type.add_subparsers(dest='experiments')
        subparsers_info_type.required = True

        exps = [
            name
            for _, name, ispkg in pkgutil.walk_packages(package_exp_type.__path__, package_exp_type.__name__ + '.')
            if not ispkg
            ]

        for exp in exps:

            name_exp = exp.replace('chemex.experiments.', '')

            package_exp = importlib.import_module(exp)

            if hasattr(package_exp, 'Profile'):
                subparsers_info_type.add_parser(
                    name_exp,
                    help=package_exp.__doc__.split('\n')[0],
                    add_help=False,
                )

    # Parser fit
    parser_fit = subparsers.add_parser(
        "fit",
        help="Starts a fit",
        prefix_chars='+-'
    )

    parser_fit.add_argument(
        '-e',
        dest='experiments',
        metavar='FILE',
        nargs='+',
        required=True,
        help='Input files containing experimental setup and data location'
    )

    parser_fit.add_argument(
        '-d',
        dest='model',
        metavar='MODEL',
        default='2st.pb_kex',
        help='Exchange model used to fit the data'
    )

    parser_fit.add_argument(
        '-p',
        dest='parameters',
        metavar='FILE',
        required=True,
        help='Input file containing the fitting parameters'
    )

    parser_fit.add_argument(
        '-m',
        dest='method',
        metavar='FILE',
        help='Input file containing the fitting method'
    )

    parser_fit.add_argument(
        '-o',
        dest='out_dir',
        metavar='DIR',
        default='./output',
        help='Directory for output'
    )

    parser_fit.add_argument(
        '--noplot',
        action='store_true',
        help='No plots of the fits'
    )

    group_residue_selec = parser_fit.add_mutually_exclusive_group()

    group_residue_selec.add_argument(
        '+r',
        dest='res_incl',
        metavar='ID',
        nargs='+',
        help='residue(s) to include in the fit'
    )

    group_residue_selec.add_argument(
        '-r',
        dest='res_excl',
        metavar='ID',
        nargs='+',
        help='residue(s) to exclude from the fit'
    )

    group_simulation = parser_fit.add_mutually_exclusive_group()

    group_simulation.add_argument(
        '--mc',
        metavar='N',
        type=int,
        help='Run N Monte-Carlo simulation'
    )

    group_simulation.add_argument(
        '--bs',
        metavar='N',
        type=int,
        help='Run N Bootstrap simulation'
    )

    args = parser.parse_args()

    if args.commands == 'fit':
        if args.res_incl:
            args.res_incl = set([res.lower() for res in args.res_incl])
        if args.res_excl:
            args.res_excl = set([res.lower() for res in args.res_excl])

    return args


def format_experiment_help(name_experiment=None):
    headline1 = "Experimental parameters"
    headline2 = "Fitted parameters (by default)"
    headline3 = "Fixed parameters (by default)"

    module_exp = importlib.import_module('.'.join(['chemex.experiments', name_experiment]))

    title = module_exp.__doc__.split('\n')[0]
    description = '\n'.join(module_exp.__doc__.split('\n')[1:]).strip('\n')

    util.header1(title)
    print("")
    print(description)
    print("")

    util.header2(headline1)
    for name in module_exp.attributes_exp:
        print(("  * {:s}".format(name)))

    util.header2(headline2)
    for name, settings in module_exp.params_exp.items():
        if settings['vary']:
            print(("  * {:s}".format(name)))

    util.header2(headline3)
    for name, settings in module_exp.params_exp.items():
        if not settings['vary']:
            print(("  * {:s}".format(name)))
