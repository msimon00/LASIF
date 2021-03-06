#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Some utility functionality.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2013
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/copyleft/gpl.html)
"""
from fnmatch import fnmatch
from lxml import etree
from lxml.builder import E


def channel_in_parser(parser_object, channel_id, starttime, endtime):
    """
    Simply function testing if a given channel is part of a Parser object.

    Returns True or False.

    :type parser_object: :class:`obspy.xseed.Parser`
    :param parser_object: The parser object.
    """
    channels = parser_object.getInventory()["channels"]
    for chan in channels:
        if not fnmatch(chan["channel_id"], channel_id):
            continue
        if starttime < chan["start_date"]:
            continue
        if chan["end_date"] and \
                (endtime > chan["end_date"]):
            continue
        return True
    return False


def table_printer(header, data):
    """
    Pretty table printer.

    :type header: A list of strings
    :param data: A list of lists containing data items.
    """
    row_format = "{:>15}" * (len(header))
    print row_format.format(*(["=" * 15] * len(header)))
    print row_format.format(*header)
    print row_format.format(*(["=" * 15] * len(header)))
    for row in data:
        print row_format.format(*row)


def generate_ses3d_4_0_template(filename):
    """
    Generates a template for SES3D input files.

    :param filename: Where to store it.
    """
    doc = E.ses3d_4_0_input_file_template(
        E.simulation_parameters(
            E.number_of_time_steps("500"),
            E.time_increment("0.75"),
            E.is_dissipative("false")),
        E.output_directory("../OUTPUT/CHANGE_ME/"),
        E.adjoint_output_parameters(
            E.sampling_rate_of_forward_field("10"),
            E.forward_field_output_directory("../OUTPUT/CHANGE_ME/ADJOINT/")),
        E.computational_setup(
            E.nx_global("15"),
            E.ny_global("15"),
            E.nz_global("10"),
            E.lagrange_polynomial_degree("4"),
            E.px_processors_in_theta_direction("1"),
            E.py_processors_in_phi_direction("1"),
            E.pz_processors_in_r_direction("1")))
    string_doc = etree.tostring(doc, pretty_print=True,
        xml_declaration=True, encoding="UTF-8")

    with open(filename, "wb") as open_file:
        open_file.write(string_doc)


def read_ses3d_4_0_template(filename):
    """
    Reads a SES3D template file to a dictionary.
    """
    # Convert it to a recursive dictionary.
    root = etree.parse(filename).getroot()
    input_file = recursive_dict(root)
    # Small sanity check.
    # XXX: Replace with xsd.
    if input_file[0] != "ses3d_4_0_input_file_template":
        msg = "Not a SES3D 4.0 compatible templates."
        raise ValueError(msg)
    input_file = input_file[1]

    # Convert some types.
    dis = input_file["simulation_parameters"]["is_dissipative"]
    if dis.lower() == "true":
       dis = True
    else:
        dis = False
    input_file["simulation_parameters"]["is_dissipative"]  = dis
    return input_file


def recursive_dict(element):
    """
    Maps an XML tree into a dict of dict.

    From the lxml documentation.
    """
    return element.tag, \
        dict(map(recursive_dict, element)) or element.text
