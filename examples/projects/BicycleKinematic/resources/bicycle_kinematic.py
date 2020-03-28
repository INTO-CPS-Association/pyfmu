from math import cos, sin, atan, tan

from scipy.integrate import solve_ivp

from pyfmu.fmi2 import Fmi2Slave,Fmi2Causality, Fmi2Variability,Fmi2DataTypes,Fmi2Initial, Fmi2Status


class Bicycle_Kinematic(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "BicycleKinematic"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        # silience incorrect warnings about undeclared variables
        self.a = 0
        self.df = 0
        self.x = 0
        self.y = 0
        self.v = 0
        self.psi = 0
        self.beta = 0
        self.lf = 1
        self.lr = 1

        # model
        self.register_variable("a", "real", "input",
                            description='acceleration',start=0)
        self.register_variable("df", "real", "input",
                               description='steering angle',start=0)


        self.register_variable("x", "real", "output",
                               description='x position of the robot')
        self.register_variable("y", "real", "output",
                               description='y position of the robot')
        self.register_variable("psi", "real", "output",
                               description='inertial heading of the robot')
        self.register_variable("v", "real", "output",
                               description='velocity of the robot')

        self.register_variable('lf', 'real', 'parameter', 'fixed',
                               start=1, description='distance from CM to front wheel')
        self.register_variable('lr', 'real', 'parameter', 'fixed',
                               start=1, description='distance from CM to rear wheel')

        # Initial values
        self.x0 = 0
        self.y0 = 0
        self.psi0 = 0
        self.v0 = 0
        self.register_variable("x0", "real", "parameter", "fixed", start=0)
        self.register_variable("y0", "real", "parameter", "fixed", start=0)
        self.register_variable("psi0", "real", "parameter", "fixed", start=0)
        self.register_variable("v0", "real", "parameter", "fixed", start=0)

        # reference model
        self.register_variable("x_r", "real", "input", start=0)
        self.register_variable("y_r", "real", "input", start=0)
        self.register_variable("psi_r", "real", "input", start=0)
        self.register_variable("v_r", "real", "input", start=0)

    @staticmethod
    def _derivatives(t, state,params):
        print(t)
        df,a,lf,lr = params

        _,_,psi,v = state

        beta = atan((lr/(lr+lf)) * tan(df))

        x_d = v * cos(psi + beta)
        y_d = v * sin(psi + beta)
        psi_d = (v / lr) * sin(beta)
        v_d = a

        return [x_d,y_d,psi_d,v_d]

    def exit_initialization_mode(self):
        # outputs are have initial = calculated
        self.x = self.x0
        self.y = self.y0
        self.psi = self.psi0
        self.v = self.v0

    def do_step(self, current_time: float, step_size: float, no_prior_step : bool):

        #bundle the parameters in the function call
        def fun(t,state):
            params = (self.df,self.a,self.lf,self.lr)
            return Bicycle_Kinematic._derivatives(t,state,params)
            

        h0 = (self.x,self.y,self.psi,self.v)
        end = current_time+step_size
        t_span = (current_time,end)

        res = solve_ivp(
            fun,
            t_span,
            h0,
            max_step=step_size,
            t_eval=[end])
        
        x,y,psi,v = tuple(res.y)
        self.x = x[0]
        self.y = y[0]
        self.psi = psi[0]
        self.v = v[0]

        return Fmi2Status.ok


# validation
if __name__ == "__main__":
    model = Bicycle_Kinematic()
    model.v0 = 1
    model.exit_initialization_mode()
    
    model.do_step(0.0,1,True)
    test = 10
