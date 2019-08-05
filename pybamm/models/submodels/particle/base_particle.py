#
# Base class for particles
#
import pybamm


class BaseParticle(pybamm.BaseSubModel):
    """Base class for molar conservation in particles.

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel
    domain : str
        The domain of the model either 'Negative' or 'Positive'


    **Extends:** :class:`pybamm.BaseSubModel`
    """

    def __init__(self, param, domain):
        super().__init__(param, domain)

    def _get_standard_concentration_variables(self, c_s, c_s_xav):

        c_s_surf = pybamm.surf(c_s, set_domain=True)

        c_s_surf_av = pybamm.x_average(c_s_surf)

        if self.domain == "Negative":
            c_scale = self.param.c_n_max
        elif self.domain == "Positive":
            c_scale = self.param.c_p_max

        variables = {
            self.domain + " particle concentration": c_s,
            self.domain + " particle concentration [mol.m-3]": c_s * c_scale,
            "X-average " + self.domain.lower() + " particle concentration": c_s_xav,
            "X-average "
            + self.domain.lower()
            + " particle concentration [mol.m-3]": c_s_xav * c_scale,
            self.domain + " particle surface concentration": c_s_surf,
            self.domain
            + " particle surface concentration [mol.m-3]": c_scale * c_s_surf,
            "X-averaged "
            + self.domain.lower()
            + " particle surface concentration": c_s_surf_av,
            "X-averaged "
            + self.domain.lower()
            + " particle surface concentration [mol.m-3]": c_scale * c_s_surf_av,
        }

        return variables

    def _get_standard_flux_variables(self, N_s, N_s_xav):
        variables = {
            self.domain + " particle flux": N_s,
            "X-average " + self.domain.lower() + " particle flux": N_s_xav,
        }

        return variables

    def _flux_law(self, c):
        raise NotImplementedError

    def _unpack(self, variables):
        raise NotImplementedError

    def set_initial_conditions(self, variables):
        c, _, _ = self._unpack(variables)

        if self.domain == "Negative":
            c_init = self.param.c_n_init

        elif self.domain == "Positive":
            c_init = self.param.c_p_init

        self.initial_conditions = {c: c_init}

    def set_events(self, variables):
        c_s_surf = variables[self.domain + " particle surface concentration"]
        tol = 0.01

        self.events[
            "Minumum " + self.domain.lower() + " particle surface concentration"
        ] = (pybamm.min(c_s_surf) - tol)

        self.events[
            "Maximum " + self.domain.lower() + " particle surface concentration"
        ] = (1 - tol) - pybamm.max(c_s_surf)
