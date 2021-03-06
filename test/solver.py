#! /usr/bin/env python
# -*- coding:utf8 -*-
#
# solver.py
#
# This file is part of pymls, a software distributed under the MIT license.
# For any question, please contact one of the authors cited below.
#
# Copyright (c) 2017
# 	Olivier Dazel <olivier.dazel@univ-lemans.fr>
# 	Mathieu Gaborit <gaborit@kth.se>
# 	Peter Göransson <pege@kth.se>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#

import unittest
import os
import itertools

import numpy as np

from pymls import Solver, Layer, backing, from_yaml
from pymls.media import Air, EqFluidJCA

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))


FREQS = [10, 500, 1000, 3000]
ANGLES = [5, 35, 45, 80]
THICKNESSES = [2e-3, 10e-3, 100e-3]
BACKINGS = [('rigid', backing.rigid), ('transmission', backing.transmission)]

NB_PLACES = 10


class SolverTests(unittest.TestCase):

    def test_air_analytical(self):

        for d in THICKNESSES:
            S = Solver()
            S.layers = [Layer(Air, d)]
            S.backing = backing.rigid
            result = S.solve(FREQS, 0)

            for i_f, f in enumerate(result['f']):
                omega = 2*np.pi*f
                k_air = omega*np.sqrt(Air.rho/Air.K)
                Z_s = -1j*Air.Z/np.tan(k_air*d)

                R_analytical = (Z_s-Air.Z)/(Z_s+Air.Z)

                self.assertAlmostEqual(
                    R_analytical,
                    result['R'][i_f],
                    NB_PLACES,
                    f'(reflection) f={f}Hz, d={d}, theta=0'
                )

    def helper_numerical_tests(self, materials, backings, tol):

        for mat_name in materials:
            mat = from_yaml(THIS_FILE_DIR+f'/materials/{mat_name}.yaml')

            for (backing_type, backing_func) in backings:
                for d in THICKNESSES:
                    reference = np.loadtxt(THIS_FILE_DIR+f'/references/{mat_name}_{int(d*1e3)}mm_{backing_type}.csv')

                    for l in reference:
                        S = Solver()
                        S.layers = [Layer(mat, d)]
                        S.backing = backing_func
                        result = S.solve(l[0], l[1])

                        self.assertAlmostEqual(result['R'][0], l[2]+1j*l[3], tol)
                        if backing_func == backing.transmission:
                            self.assertAlmostEqual(result['T'][0], l[4]+1j*l[5], tol)

    def test_elastic_rigid_numerical(self):
        self.helper_numerical_tests(['wood', 'glass'], BACKINGS[:0], NB_PLACES)

    def test_pem_rigid_numerical(self):
        self.helper_numerical_tests(['foam2'], BACKINGS[:0], NB_PLACES)

    def test_elastic_transmission_numerical(self):
        self.helper_numerical_tests(['wood', 'glass'], BACKINGS[1:1], NB_PLACES)

    def test_pem_transmission_numerical(self):
        self.helper_numerical_tests(['foam2'], BACKINGS[1:1], NB_PLACES)

    def helper_bi_mat(self, mat1_name, mat2_name, backings, tol):

        mat1 = from_yaml(THIS_FILE_DIR+f'/materials/{mat1_name}.yaml')
        mat2 = from_yaml(THIS_FILE_DIR+f'/materials/{mat2_name}.yaml')

        prefix = f'{mat1_name}_{mat2_name}'

        for (backing_type, backing_func) in backings:
            for (d1, d2) in itertools.product(THICKNESSES, THICKNESSES):
                filename = THIS_FILE_DIR+f'/references/{prefix}_{int(d1*1e3)}mm_{int(d2*1e3)}mm_{backing_type}.csv'
                if not os.path.exists(filename):
                    continue

                reference = np.loadtxt(filename)

                for l in reference:
                    S = Solver()
                    S.layers = [Layer(mat1, d1), Layer(mat2, d2)]
                    S.backing = backing_func
                    result = S.solve(l[0], l[1])

                    self.assertAlmostEqual(result['R'][0], l[2]+1j*l[3], tol)
                    if backing_func == backing.transmission:
                        self.assertAlmostEqual(result['T'][0], l[4]+1j*l[5], tol)

    def test_pem_bois_rigid_numerical(self):
        self.helper_bi_mat('foam2', 'wood', BACKINGS[:0], 10)

    def test_pem_bois_transmission_numerical(self):
        self.helper_bi_mat('foam2', 'wood', BACKINGS[1:1], 10)

    def test_2xpem_rigid_numerical(self):
        self.helper_bi_mat('foam2', 'foam2', BACKINGS[:0], 10)

    def test_2xpem_transmission_numerical(self):
        self.helper_bi_mat('foam2', 'foam2', BACKINGS[1:1], 10)

    def helper_numerical_tests_eqf(self, materials, backings, tol):

        for mat_name in materials:
            mat = from_yaml(THIS_FILE_DIR+f'/materials/{mat_name}.yaml', force=EqFluidJCA)

            for (backing_type, backing_func) in backings:
                for d in THICKNESSES:
                    for a in ANGLES:
                        reference = np.loadtxt(THIS_FILE_DIR+f'/references/eqf/{mat_name}_{int(d*1e3)}mm_{backing_type}_{a}deg.PW')

                        for l in reference:
                            S = Solver()
                            S.layers = [Layer(mat, d)]
                            S.backing = backing_func
                            result = S.solve(l[0], a)

                            self.assertAlmostEqual(
                                result['R'][0], l[2]+1j*l[3], tol,
                                f'(reflection) {mat_name} : f={l[0]}Hz angle={a}deg d={d:2.3f}m'
                            )
                            if backing_func == backing.transmission:
                                self.assertAlmostEqual(
                                    result['T'][0], l[5]+1j*l[6], tol,
                                    f'(transmission) {mat_name} : f={l[0]}Hz angle={a}deg d={d:2.3f}m'
                                )

    def helper_bi_mat_eqf(self, mat1_name, mat2_name, backings, tol, no_is_default=-1, ref_path='eqf'):

        if no_is_default == 1:
            mat1 = from_yaml(THIS_FILE_DIR+f'/materials/{mat1_name}.yaml')
        else:
            mat1 = from_yaml(THIS_FILE_DIR+f'/materials/{mat1_name}.yaml', force=EqFluidJCA)

        if no_is_default == 2:
            mat2 = from_yaml(THIS_FILE_DIR+f'/materials/{mat2_name}.yaml')
        else:
            mat2 = from_yaml(THIS_FILE_DIR+f'/materials/{mat2_name}.yaml', force=EqFluidJCA)

        prefix = f'{mat1_name}_{mat2_name}'

        for (backing_type, backing_func) in backings:
            for (d1, d2) in itertools.product(THICKNESSES, THICKNESSES):
                for a in ANGLES:
                    filename = THIS_FILE_DIR+f'/references/{ref_path}/{prefix}_{int(d1*1e3)}mm_{int(d2*1e3)}mm_{backing_type}_{a}deg.PW'
                    if not os.path.exists(filename):
                        continue

                    reference = np.loadtxt(filename)

                    for l in reference:
                        S = Solver()
                        S.layers = [Layer(mat1, d1), Layer(mat2, d2)]
                        S.backing = backing_func
                        result = S.solve(l[0], a)

                        self.assertAlmostEqual(
                            result['R'][0], l[2]+1j*l[3], tol,
                            f'(reflection) {mat1_name} {mat2_name} : f={l[0]}Hz angle={a}deg d1={d1:2.3f}m d2={d2:2.3f}m'
                        )
                        if backing_func == backing.transmission:
                            self.assertAlmostEqual(
                                result['T'][0], l[5]+1j*l[6], tol,
                                f'(transmission) {mat1_name} {mat2_name} : f={l[0]}Hz angle={a}deg d1={d1:2.3f}m d2={d2:2.3f}m'
                            )

    def test_foams_eqf(self):
        self.helper_numerical_tests_eqf(['foam', 'foam2'], BACKINGS, NB_PLACES)

    # def test_foam_wood_eqf(self):
    #     self.helper_bi_mat_eqf('foam', 'wood', BACKINGS, NB_PLACES, no_is_default=2)
    #     self.helper_bi_mat_eqf('wood', 'foam', BACKINGS, NB_PLACES, no_is_default=1)
    #
    # def test_foam2_wood_eqf(self):
    #     self.helper_bi_mat_eqf('foam2', 'wood', BACKINGS, NB_PLACES, no_is_default=2)
    #     self.helper_bi_mat_eqf('wood', 'foam2', BACKINGS, NB_PLACES, no_is_default=1)
    #
    def test_foam_foam_eqf(self):
        self.helper_bi_mat_eqf('foam', 'foam', BACKINGS, NB_PLACES)

    def test_foam2_foam2_eqf(self):
        self.helper_bi_mat_eqf('foam2', 'foam2', BACKINGS, NB_PLACES)

    def test_foam2_foam_eqf(self):
        self.helper_bi_mat_eqf('foam2', 'foam', BACKINGS, NB_PLACES)
        self.helper_bi_mat_eqf('foam', 'foam2', BACKINGS, NB_PLACES)

    def test_eqf_pem(self):
        self.helper_bi_mat_eqf('foam', 'foam', BACKINGS, NB_PLACES, no_is_default=2, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam', 'foam2', BACKINGS, NB_PLACES, no_is_default=2, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam2', 'foam2', BACKINGS, NB_PLACES, no_is_default=2, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam2', 'foam', BACKINGS, NB_PLACES, no_is_default=2, ref_path='eqf_pem')

    def test_pem_eqf(self):
        self.helper_bi_mat_eqf('foam', 'foam', BACKINGS, NB_PLACES, no_is_default=1, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam', 'foam2', BACKINGS, NB_PLACES, no_is_default=1, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam2', 'foam2', BACKINGS, NB_PLACES, no_is_default=1, ref_path='eqf_pem')
        self.helper_bi_mat_eqf('foam2', 'foam', BACKINGS, NB_PLACES, no_is_default=1, ref_path='eqf_pem')
