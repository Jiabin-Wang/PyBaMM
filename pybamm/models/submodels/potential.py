#
# Equation classes for the open-circuit potentials and reaction overpotentials
#
import pybamm


class Potential(pybamm.SubModel):
    """Compute open-circuit potentials and reaction overpotentials

    Parameters
    ----------
    set_of_parameters : parameter class
        The parameters to use for this submodel

    *Extends:* :class:`BaseModel`
    """

    def __init__(self, set_of_parameters):
        super().__init__(set_of_parameters)

    def set_open_circuit_potentials(self, c_n, c_p):
        """
        Compute open-circuit potentials (dimensionless and dimensionless). Note that for
        this submodel, we must specify explicitly which concentration we are using to
        calculate the open-circuit potential.

        Parameters
        ----------
        c_n : :class:`pybamm.Symbol`
            The negative-electrode concentration to use to calculate the
            negative-electrode OCP (e.g. negative particle surface concentration)
        c_p : :class:`pybamm.Symbol`
            The positive-electrode concentration to use to calculate the
            positive-electrode OCP (e.g. positive particle surface concentration)

        """
        # Load parameters and spatial variables
        param = self.set_of_parameters
        x_n = pybamm.standard_spatial_vars.x_n
        x_p = pybamm.standard_spatial_vars.x_p

        # Dimensionless
        ocp_n = pybamm.Broadcast(param.U_n(c_n), ["negative electrode"])
        ocp_p = pybamm.Broadcast(param.U_p(c_p), ["positive electrode"])
        ocp_n_av = pybamm.Integral(ocp_n, x_n) / param.l_n
        ocp_p_av = pybamm.Integral(ocp_p, x_p) / param.l_p
        ocp_n_left = pybamm.BoundaryValue(ocp_n, "left")
        ocp_p_right = pybamm.BoundaryValue(ocp_p, "right")
        ocv_av = ocp_p_av - ocp_n_av
        ocv = ocp_p_right - ocp_n_left

        # Dimensional
        ocp_n_dim = param.U_n_ref + param.potential_scale * ocp_n
        ocp_p_dim = param.U_p_ref + param.potential_scale * ocp_p
        ocp_n_av_dim = param.U_n_ref + param.potential_scale * ocp_n_av
        ocp_p_av_dim = param.U_p_ref + param.potential_scale * ocp_p_av
        ocp_n_left_dim = param.U_n_ref + param.potential_scale * ocp_n_left
        ocp_p_right_dim = param.U_p_ref + param.potential_scale * ocp_p_right
        ocv_av_dim = ocp_p_av_dim - ocp_n_av_dim
        ocv_dim = ocp_p_right_dim - ocp_n_left_dim

        # Variables
        self.variables.update(
            {
                "Negative electrode open circuit potential": ocp_n,
                "Positive electrode open circuit potential": ocp_p,
                "Average negative electrode open circuit potential": ocp_n_av,
                "Average positive electrode open circuit potential": ocp_p_av,
                "Average open circuit voltage": ocv_av,
                "Measured open circuit voltage": ocv,
                "Negative electrode open circuit potential [V]": ocp_n_dim,
                "Positive electrode open circuit potential [V]": ocp_p_dim,
                "Average negative electrode open circuit potential [V]": ocp_n_av_dim,
                "Average positive electrode open circuit potential [V]": ocp_p_av_dim,
                "Average open circuit voltage [V]": ocv_av_dim,
                "Measured open circuit voltage [V]": ocv_dim,
            }
        )

    def set_reaction_overpotentials(self, variables, compute_from):
        """
        Compute reaction overpotentials (dimensionless and dimensionless).

        Parameters
        ----------
        variables : dict
            Dictionary of {string: :class:`pybamm.Symbol`}, which can be read to find
            already-calculated variables
        compute_from : str
            Whether to use the current densities (invert Butler-Volmer) or potentials
            (direct calculation) to compute reaction overpotentials
        """
        # Load parameters and spatial variables
        param = self.set_of_parameters
        x_n = pybamm.standard_spatial_vars.x_n
        x_p = pybamm.standard_spatial_vars.x_p

        if compute_from == "current":
            int_curr_model = pybamm.interface.InterfacialCurrent(param)
            eta_r_n, eta_r_p = int_curr_model.get_inverse_butler_volmer(variables)
        elif compute_from == "potentials":
            phi_s = variables["Electrode potential"]
            phi_s_n, phi_s_s, phi_s_p = phi_s.orphans
            phi_e = variables["Electrolyte potential"]
            phi_e_n, phi_e_s, phi_e_p = phi_e.orphans
            ocp_n = variables["Negative electrode open circuit potential"]
            ocp_p = variables["Positive electrode open circuit potential"]

            eta_r_n = phi_s_n - phi_e_n - ocp_n
            eta_r_p = phi_s_p - phi_e_p - ocp_p

        # Derived and dimensional reaction overpotentials
        eta_r_n_av = pybamm.Integral(eta_r_n, x_n) / param.l_n
        eta_r_p_av = pybamm.Integral(eta_r_p, x_p) / param.l_p
        eta_r_av = eta_r_p_av - eta_r_n_av

        eta_r_n_dim = param.potential_scale * eta_r_n
        eta_r_p_dim = param.potential_scale * eta_r_p
        eta_r_n_av_dim = param.potential_scale * eta_r_n_av
        eta_r_p_av_dim = param.potential_scale * eta_r_p_av
        eta_r_av_dim = param.potential_scale * eta_r_av

        # Update variables
        self.variables.update(
            {
                "Negative reaction overpotential": eta_r_n,
                "Positive reaction overpotential": eta_r_p,
                "Average negative reaction overpotential": eta_r_n_av,
                "Average positive reaction overpotential": eta_r_p_av,
                "Average reaction overpotential": eta_r_av,
                "Negative reaction overpotential [V]": eta_r_n_dim,
                "Positive reaction overpotential [V]": eta_r_p_dim,
                "Average negative reaction overpotential [V]": eta_r_n_av_dim,
                "Average positive reaction overpotential [V]": eta_r_p_av_dim,
                "Average reaction overpotential [V]": eta_r_av_dim,
            }
        )
