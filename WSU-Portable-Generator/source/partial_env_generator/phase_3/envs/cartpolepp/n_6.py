import math
import numpy as np
import os.path
from gym.utils import seeding

from .cartpoleplusplus import CartPoleBulletEnv


# Finds the coordinates of the tip of a unit vector after transformation by thx, thy, thz
# (assuming unit vector points from origin along positive z axis; i.e. [0,0,1])
def euler_to_spherical(angles):
    # input is a vector of three Euler angles in radians
    thx, thy, thz = angles

    x0, y0, z0 = [0, 0, 1]  # coordinates of tip of unit vector

    # Rotate about x axis (thx transformation)
    x1 = x0
    y1 = y0 * np.cos(thx) - z0 * np.sin(thx)
    z1 = y0 * np.sin(thx) + z0 * np.cos(thx)

    # Rotate about y-axis (thy transformation)
    x2 = z1 * np.sin(thy) + x1 * np.cos(thy)
    y2 = y1
    z2 = z1 * np.cos(thy) - x1 * np.sin(thy)

    # Rotate about z-axis (thz transformation)
    x3 = x2 * np.cos(thz) - y2 * np.sin(thz)
    y3 = x2 * np.sin(thz) + y2 * np.cos(thz)
    z3 = z2

    # Calculate azimuth
    # pi/2 adjustment is because pybullet's thz = 0 is along y-axis, not x-axis
    azimuth = -np.pi / 2 + np.arctan(y3 / x3)
    if x3 < 0:
        azimuth += np.pi

    # Calculate inclination
    dist = np.linalg.norm([x3, y3])
    inclination = np.arcsin(dist)  # technically D/1, since it's a unit vector

    # print("azimuth, inclination in degrees:", np.degrees(azimuth), np.degrees(inclination))

    return azimuth, inclination


class CartPolePPNovel6(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.wind_force = 16
        elif self.difficulty == 'medium':
            self.wind_force = 18
        elif self.difficulty == 'hard':
            self.wind_force = 20

        ''' Load data '''
        # Import RANS-modeled density and velocity profiles
        with open(os.path.join(self.path, 'rans_profile.txt')) as file:
            rans_data = np.loadtxt(file, skiprows=9)  # Imports a text file generated using code from [3]

        z_rans = rans_data[:, 0]  # vertical coordinates
        r_rans = rans_data[:, 1]  # density profile
        u_rans = rans_data[:, 2]  # velocity profile

        """ Initialize turbulence """
        # Setup airflow parameters
        # height of wind tunnel, in meters
        self.h = 10.0
        # wind velocity at centerline of wind tunnel
        self.umax = self.wind_force
        # number of meshpoints in z direction for airflow calculations
        self.n = 200
        # angle in degrees around z-axis; 0 = +y direction
        self.windangle = np.radians(self.np_random.random() * 360.0)
        # density of fluid, in kg/m^3; default value represents dry air
        self.density = 1.225
        self.polewidth = 0.06
        self.polelength = 2.0
        self.cartlength = 0.2
        self.cartwidth = 1.0

        # differential height increment between mesh points, use to find area acted on by each flow vector
        self.dz = self.h / self.n

        # Scale RANS profile based on channel height, fluid density, umax
        scaled_z = z_rans * (self.h / 2)  # scales height of RANS profile to channel height
        scaled_r = r_rans * self.density  # scales max density to specified fluid density
        scaled_u = u_rans * (self.umax / np.amax(u_rans))  # scales entire velocity profile --> max velocity = umax

        # Interpolate z, r, u to uniformly spaced meshpoints
        self.z = np.linspace(0, self.h, self.n)  # creates n evenly spaced mesh points spanning the flow channel
        self.r = np.interp(self.z, scaled_z, scaled_r)
        self.u = np.interp(self.z, scaled_z, scaled_u)

        # Compute x and y components of velocity profile based on wind angle
        # x-components of velocity profile (negative sign because wind angle = 0 is +y direction)
        # y-components of velocity profile
        self.ux = self.u * np.sin(-self.windangle)
        self.uy = self.u * np.cos(self.windangle)

        return None

    def step(self, action):
        self.apply_wind()
        state, reward, done, info = super().step(action)
        return state, reward, done, info

    def apply_wind(self):
        p = self._p

        # Chris' Homebrew Calculation for blocks
        for block_num in self.blocks:
            # Constants
            block_drag = 0.5
            block_area = np.pi * (0.5 ** 2)
            block_height = 0.5
            force_reduction = 0.5

            # Get block posistion
            pos, _ = p.getBasePositionAndOrientation(block_num)
            block_top = int((pos[2] + block_height / 2) * self.n / self.h)
            block_bot = int((pos[2] - block_height / 2) * self.n / self.h)

            # Get directional velocties
            vx = self.ux[block_bot:block_top]
            vy = self.uy[block_bot:block_top]

            # Compute forces
            fx_block = np.sum(0.5 * self.density * (vx ** 2) * block_drag * block_area) * force_reduction
            fy_block = np.sum(0.5 * self.density * (vy ** 2) * block_drag * block_area) * force_reduction

            # Apply forces
            p.applyExternalForce(block_num, -1, (fx_block, fy_block, 0), (0, 0, 0), p.LINK_FRAME)

            continue

        # Get current position and velocity of pole
        # Position and orientation, the other two not used
        ori, _, _, _ = p.getJointStateMultiDof(self.cartpole, 1)

        # Convert quaternion orientation to spherical coordinates (azimuth and inclination)
        # Azimuth:     rotation angle about z-axis, with azimuth = 0 in the positive y-direction
        # Inclination: angle that the pole makes with vertical (z-axis)
        eulerangles = p.getEulerFromQuaternion(ori)  # converts quaternion to Euler angles about x,y,z axes
        azim, incl = euler_to_spherical(eulerangles)  # calls another script that converts to spherical coordinates, see documentation Section [C]
        # print(np.degrees(eulerangles))

        # Define pole area & drag coefficient (approximating pole as a cylinder, see documentation Section [D])
        a_pole = (self.polewidth * np.sqrt(2)) * self.dz  # cylinder diameter is polewidth * sqrt(2)
        cd_pole = 1  # taken from [4]

        # Compute velocity normal to pole and use to find drag force
        # (Drag force is perpendicular to flow streamlines; only force components normal to pole contribute to moment)
        v = np.array([[self.ux * np.cos(incl), np.cos(azim) * self.ux * np.sin(incl)],
                      [self.uy * np.cos(incl),
                       np.sin(azim) * self.uy * np.sin(incl)]])  # explained in documentation Section [E]

        ux_normal, uy_normal = np.linalg.norm(v, axis=1)  # computes magnitude of normal velocity vectors [E]

        Fx_normal = 0.5 * self.density * a_pole * cd_pole * ux_normal ** 2  # computes magnitude of force x-component normal to pole [F]
        Fy_normal = 0.5 * self.density * a_pole * cd_pole * uy_normal ** 2  # computes magnitude of force y-component normal to pole

        # Since direction of force components was lost by the u^2 term [F]:
        if np.amin(self.ux) < 0:
            Fx_normal *= -1
        if np.amin(self.uy) < 0:
            Fy_normal *= -1

        # Find vertical mesh points corresponding to pole location [H]
        z0 = 0.35 - (0.5 * self.polelength)  # vertical coordinate of pole base, pole CoM originally at 0.35
        ztip = z0 + self.polelength * np.cos(incl)  # current z-coordinate of pole tip
        nbase = int(z0 * self.n / self.h)  # computes mesh point in range(0:n) corresponding to base of pole
        ntip = int(ztip * self.n / self.h)  # computes mesh point in range(0:n) corresponding to tip of pole

        # Compute net moment on pole due to airflow [H]
        Mx = My = 0
        for i in range(nbase, ntip + 1):
            Mx += (-Fy_normal[i] * ((self.z[i] - z0) / np.cos(
                incl)))  # sums (Force * radial distance) to get net moment; negative because +y force creates -x moment
            My += (Fx_normal[i] * ((self.z[i] - z0) / np.cos(
                incl)))  # sums (Force * radial distance) to get net moment; positive because +x force creates +y moment

        # Calculate net force on pole due to drag [H]
        Fxnet = np.sum(Fx_normal[nbase:ntip + 1])  # x-component of net force
        Fynet = np.sum(Fy_normal[nbase:ntip + 1])  # y-component of net force

        # Find vertical mesh points corresponding to cart location [H]
        zcart = 0.08 + (0.5 * self.cartlength)  # vertical coordinate of cart upper surface, cart CoM stays at 0.08 m
        cbase = 0  # computes mesh point in range(0:n) corresponding to base of cart, which is zero
        ctop = int(zcart * self.n / self.h)  # computes mesh point in range(0:n) corresponding to upper surface of cart

        # Compare cart orientation to wind angle (drag force on cart is dependent on its rotation about z-axis) [G]
        #cori, _, _, _ = p.getJointStateMultiDof(self.cartpole, 0)
        cori = [0, 0, 0, 1]
        cartspin = p.getEulerFromQuaternion(cori)[2]  # gets cart's Euler angle about z-axis
        dtheta = cartspin - self.windangle  # difference between wind angle and cart's Euler angle about z-axis

        # Compute cart frontal area and drag coefficient as sinusoidal functions of dtheta (see documentation Section [G])
        amplitude = (np.sqrt(2) - 1) / 2
        wscale = (amplitude * np.sin(4 * dtheta - np.pi / 2) + (
                    1 + amplitude))  # varies between 1 (@dtheta = 90 deg) and sqrt(2) (@dtheta = 45 deg)
        a_cart = self.cartwidth * wscale * self.dz  # computes frontal area of cart (surface area normal to wind)
        cd_cart = 0.5 * np.cos(
            4 * dtheta) + 1.5  # drag coefficient varies between 1 (@dtheta = 45 deg) and 2 (@dtheta = 90 deg). [G]

        # Calculate drag force on cart [G]
        Fx_cart = np.sum(
            0.5 * self.density * a_cart * cd_cart * self.ux[cbase:ctop + 1] ** 2)  # x-component of drag force
        Fy_cart = np.sum(
            0.5 * self.density * a_cart * cd_cart * self.uy[cbase:ctop + 1] ** 2)  # y-component of drag force

        # Since u^2 term removes the sign of the force components:
        if np.amin(self.ux) < 0:
            Fx_cart *= -1
        if np.amin(self.uy) < 0:
            Fy_cart *= -1

        # Apply wind force to cart [H]
        _, ori, _, _, _, _ = p.getLinkState(self.cartpole, 0)
        cart_angle = p.getEulerFromQuaternion(ori)[2] # yaw

        # Adjust forces so it always apply in reference to world frame
        Fx_cart = Fx_cart * np.cos(cart_angle)
        Fy_cart = Fy_cart * np.sin(cart_angle) * -1
        p.applyExternalForce(self.cartpole, 0, (Fx_cart, Fy_cart, 0), (0, 0, 0), p.LINK_FRAME)  # wind force on cart

        # Apply wind force to pole
        _, ori, _, _, _, _ = p.getLinkState(self.cartpole, 1)
        pole_angle = p.getEulerFromQuaternion(ori)[2] # yaw

        # Adjust forces so it always apply in reference to world frame
        Fxnet = Fxnet * np.cos(pole_angle)
        Fynet = Fynet * np.sin(pole_angle) * -1

        # Apply either torque or force to pole (applying both is redundant) [H]
        #p.applyExternalTorque(self.pole, -1, (Mx, My, 0), p.LINK_FRAME)  # wind torque on pole
        p.applyExternalForce(self.cartpole, 1, (Fxnet, Fynet, 0), (0, 0, 0), p.LINK_FRAME)  # wind force on pole

        #print(Fxnet, Fynet)

        return None
