# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 14:28:25 2018

@author: Calil
"""

import numpy as np
from scipy.integrate import dblquad

from sharc.antenna.antenna_beamforming_imt import AntennaBeamformingImt
from sharc.support.named_tuples import AntennaPar

 
class BeamformingNormalizer(object):
    """
    
    """
    def __init__(self, res_deg: float, tol: float):
        """
        
        """
        # Initialize attributes
        self.res_deg = res_deg
        self.tol = tol
        
        self.phi_min_deg = -180
        self.phi_max_deg = 180
        self.theta_min_deg = 0
        self.theta_max_deg = 180
        
        self.phi_min_rad = np.deg2rad(self.phi_min_deg)
        self.phi_max_rad = np.deg2rad(self.phi_max_deg)
        self.theta_min_rad = np.deg2rad(self.theta_min_deg)
        self.theta_max_rad = np.deg2rad(self.theta_max_deg)
        
        self.phi_vals_deg = np.arange(self.phi_min_deg,
                                      self.phi_max_deg,res_deg)
        self.theta_vals_deg = np.arange(self.theta_min_deg,
                                        self.theta_max_deg,res_deg)
        self.antenna = None  
               
    def generate_correction_matrix(self, par: AntennaPar, c_chan: bool, file_name: str):
        """
        
        """
        # Create antenna object
        azi = 0 # Antenna azimuth: 0 degrees for simplicity
        ele = 0 # Antenna elevation: 0 degrees as well
        self.antenna = AntennaBeamformingImt(par,azi,ele)
        
        if c_chan:
            # Correction factor numpy array
            cf = np.zeros((len(self.phi_vals_deg),len(self.theta_vals_deg)))
            err = np.empty((len(self.phi_vals_deg),len(self.theta_vals_deg)), dtype=tuple)
            
            # Loop throug all the possible beams
            for phi_idx, phi in enumerate(self.phi_vals_deg):
                for theta_idx, theta in enumerate(self.theta_vals_deg):
                    cf[phi_idx,theta_idx], err[phi_idx,theta_idx] = self.calculate_correction_factor(phi,theta,c_chan)
                
        else:
            # Correction factor float
            cf, err = self.calculate_correction_factor(0,0,c_chan)
          
        # Save in file
        self._save_files(cf,par,file_name)
        return cf, err
            
    def calculate_correction_factor(self, phi_e: float, theta_t: float, c_chan: bool):
        """
        
        """
        if c_chan:
            self.antenna.add_beam(phi_e,theta_t)
            beam = int(len(self.antenna.beams_list) - 1)
            int_f = lambda t,p: \
            np.power(10,self.antenna._beam_gain(np.rad2deg(p),np.rad2deg(t),beam)/10)*np.sin(t)
        else:
            int_f = lambda t,p: \
            np.power(10,self.antenna.element.element_pattern(np.rad2deg(p),np.rad2deg(t))/10)*np.sin(t)
        
        int_val, err = dblquad(int_f,self.phi_min_rad,self.phi_max_rad,
                          lambda p: self.theta_min_rad, 
                          lambda p: self.theta_max_rad,
                          epsabs=self.tol,
                          epsrel=0.0)
        
        cf = -10*np.log10(int_val/(4*np.pi))
        
        hig_bound = -10*np.log10((int_val - err)/(4*np.pi))
        low_bound = -10*np.log10((int_val + err)/(4*np.pi))
        
        return cf, (low_bound,hig_bound)
    
    def _save_files(self, correction, par:AntennaPar, file_name: str):
        """
        
        """
        np.savez(file_name,
                 correction_factor = correction,
                 parameters = par)
    
if __name__ == '__main__':
    """
    
    """
    import matplotlib.pyplot as plt
    
    # Create normalizer object
    resolution = 5
    tolerance = 5e-1
    norm = BeamformingNormalizer(resolution,tolerance)
    
    # Antenna parameters
    element_pattern = "M2101"
    element_max_g = 5
    element_phi_deg_3db = 65
    element_theta_deg_3db = 65
    element_am = 30
    element_sla_v = 30
    n_rows = 8
    n_columns = 8
    horiz_spacing = 0.5
    vert_spacing = 0.5
    down_tilt = 0
    par = AntennaPar(element_pattern,
                     element_max_g,
                     element_phi_deg_3db,
                     element_theta_deg_3db,
                     element_am,
                     element_sla_v,
                     n_rows,
                     n_columns,
                     horiz_spacing,
                     vert_spacing,
                     down_tilt)
    
    # Set range of values & calculate correction factor
    norm.theta_vals_deg = np.array([90])
    c_chan = True
    file_name = 'main_test.npz'
    cf, err = norm.generate_correction_matrix(par,c_chan,file_name)
    err_low, err_high = zip(*np.ravel(err))
    
    plt.plot(norm.phi_vals_deg,cf,
             norm.phi_vals_deg,err_low,'r--',
             norm.phi_vals_deg,err_high,'r--')
    plt.ylabel(r"Correction factor [dB]")
    plt.xlabel(r"Azimuth angle $\phi$ [deg]")
    plt.title(r"Elevation angle $\theta$ = 90 deg")
    plt.show()
    
    # Set range of values & calculate correction factor
    norm = BeamformingNormalizer(resolution,tolerance)
    norm.phi_vals_deg = np.array([0])
    c_chan = True
    file_name = 'main_test.npz'
    cf, err = norm.generate_correction_matrix(par,c_chan,file_name)
    err_low, err_high = zip(*np.ravel(err))
    
    plt.plot(norm.theta_vals_deg,np.transpose(cf),
             norm.theta_vals_deg,np.transpose(err_low),'r--',
             norm.theta_vals_deg,np.transpose(err_high),'r--')
    plt.ylabel(r"Correction factor [dB]")
    plt.xlabel(r"Elevation angle $\theta$ [deg]")
    plt.title(r"Azimuth angle $\phi$ = 0 deg")
    plt.show()
    
    