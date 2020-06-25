import math

from oomodelling.Model import Model

class BicycleDynamicModel(Model):
    def __init__(self):
        super().__init__()
        self.lf = self.parameter(1.105)  # distance from the the center of mass to the front (m)";
        self.lr = self.parameter(1.738)  # distance from the the center of mass to the rear (m)";
        self.m = self.parameter(1292.2)  # Vehicle's mass (kg)";
        self.Iz = self.parameter(1)  # Yaw inertial (kgm^2) (Not taken from the book)";
        self.Caf = self.input(lambda: 800.0)  # Front Tire cornering stiffness";
        self.Car = self.parameter(800.0)  # Rear Tire cornering stiffness";
        self.x = self.state(0.0)  # longitudinal displacement in the body frame";
        self.X = self.state(0.0)  # x coordinate in the reference frame";
        self.Y = self.state(0.0)  # x coordinate in the reference frame";
        self.vx = self.state(1.0)  # velocity along x";
        self.y = self.state(0.0)  # lateral displacement in the body frame";
        self.vy = self.state(0.0)  # velocity along y";
        self.psi = self.state(0.0)  # Yaw";
        self.dpsi = self.state(0.0)  # Yaw rate";
        self.a = self.input(lambda: 0.0)  # longitudinal acceleration";
        self.deltaf = self.input(lambda: 0.0) # steering angle at the front wheel";
        self.af = self.var(lambda: self.deltaf() - (self.vy() + self.lf*self.dpsi())/self.vx())  # Front Tire slip angle";
        self.ar = self.var(lambda: (self.vy() - self.lr*self.dpsi())/self.vx())  # Rear Tire slip angle";
        self.Fcf = self.var(lambda: self.Caf()*self.af())  # lateral tire force at the front tire in the frame of the front tire";
        self.Fcr = self.var(lambda: self.Car*(-self.ar()))  # lateral tire force at the rear tire in the frame of the rear tire";

        self.der('x', lambda: self.vx())
        self.der('y', lambda: self.vy())
        self.der('psi', lambda: self.dpsi())
        self.der('vx', lambda: self.dpsi()*self.vy() + self.a())
        self.der('vy', lambda: -self.dpsi()*self.vx() + (1/self.m)*(self.Fcf() * math.cos(self.deltaf()) + self.Fcr()))
        self.der('dpsi', lambda: (2/self.Iz)*(self.lf*self.Fcf() - self.lr*self.Fcr()))
        self.der('X', lambda: self.vx()*math.cos(self.psi()) - self.vy()*math.sin(self.psi()))
        self.der('Y', lambda: self.vx()*math.sin(self.psi()) + self.vy()*math.cos(self.psi()))

        self.save()
