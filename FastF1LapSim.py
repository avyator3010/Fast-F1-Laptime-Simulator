# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 11:53:13 2026

@author: avyay
"""

import numpy as np
import os
import fastf1
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev

def load_fast_lap(year, gp, session_type="Q", cache_dir="cache"):
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)
    session = fastf1.get_session(year, gp, session_type)
    session.load(telemetry=True, laps=True, weather=False)
    fastest = session.laps.pick_fastest()
    print("Lap used:", fastest['Driver'], "-", fastest['LapTime'])
    tel = fastest.get_telemetry()
    return tel

tel = load_fast_lap(2025, "Silverstone")

x = tel["X"].to_numpy() / 10
y = tel["Y"].to_numpy() / 10

plt.plot(x, y)
plt.axis("equal")


def compute_curvature(x, y, smoothing=20.0):
    tck, u = splprep([x, y], s=smoothing, per=True)
    u1 = np.linspace(0, 1, 3000, endpoint=False)
    dx, dy = splev(u1, tck, der = 1)
    ddx, ddy = splev(u1, tck, der = 2)
    kappa = (dx*ddy - dy*ddx)/((dx**2 + dy**2)**1.5)
    v = np.sqrt(dx**2 + dy**2)
    U = 1/3000
    s = np.cumsum(v)*U
    return s, kappa

s, kappa = compute_curvature(x, y)

plt.figure()
plt.plot(s, kappa)
plt.xlabel("Distance along lap (m)")
plt.ylabel("Curvature(1/m)")

def resample_uniform(s, kappa, spacing = 0.5):
    s_uniform = np.arange(0, s[-1], spacing)
    kappa_uniform = np.interp(s_uniform, s, kappa)
    return s_uniform, kappa_uniform

s_uniform, kappa_uniform = resample_uniform(s, kappa)

def magic_formula(x, B, C, D, E):
    inner = B*x - E*(B*x - np.arctan(B*x))
    return D * np.sin(C * np.arctan(inner))

alpha_deg = np.linspace(0, 15, 200)
alpha_rad = np.radians(alpha_deg)

Fy = magic_formula(alpha_rad, B=10, C=1.4, D=3000, E= -1)

plt.figure()
plt.plot(alpha_deg, Fy)
plt.xlabel("slip angle (deg)")
plt.ylabel("lateral force (N)")

def peak_mu(Fz, mu0=1.7, Fz0=3000, k=0.00004):
    return mu0 - k*(Fz - Fz0)

Fz = 3000                          # test load, newtons
D = peak_mu(Fz) * Fz
Fy = magic_formula(alpha_rad, B=10, C=1.4, D=D, E=0.97)

m = 798          # mass, kg
g = 9.81
rho = 1.225      # air density
P = 683000  # engine power, watts
a_brake = 45.0   # braking deceleration, m/s^2

def max_corner_speed(k, m=798, g=9.81, rho=1.225, ClA=4.0, v_top=None, mu0=1.7):
    v = 30.0
    for _ in range(50):
        Fz = m*g + 0.5*rho*ClA*v**2
        mu = peak_mu(Fz, mu0=mu0)         
        denom = m*k - 0.5*mu*rho*ClA
        if denom <= 0:
            return v_top
        v_new = np.sqrt(mu*m*g / denom)
        if abs(v_new - v) < 0.01:
            break
        v = v_new
    if not np.isfinite(v_new):
        return v_top
    return min(v_new, v_top)

def simulate(ClA, CdA, a_brake, mu0):
    v_top = (2*P / (rho*CdA))**(1/3)

    speeds = []
    for k in kappa_uniform:
        denom = m*k - 0.5*peak_mu(m*g, mu0=mu0)*rho*ClA     # <- mu0 here too
        if denom > 0:
            speeds.append(max_corner_speed(k, ClA=ClA, v_top=v_top, mu0=mu0))
        else:
            speeds.append(v_top)
    speeds = np.array(speeds)

    v_back = speeds.copy()
    n = len(v_back)
    ds = 0.5
    for step in range(2*n):
        i = (n - 1 - step) % n
        i_next = (i + 1) % n
        v_next = v_back[i_next]
        v_max_here = np.sqrt(np.maximum(v_next**2 + 2*a_brake*ds, 0))
        v_back[i] = min(v_back[i], v_max_here)

    v_fwd = v_back.copy()
    for step in range(2*n):
        i = step % n
        i_prev = (i - 1) % n
        v_prev = v_fwd[i_prev]
        F_engine = P / v_prev
        F_drag = 0.5 * rho * CdA * v_prev**2
        a_acc = (F_engine - F_drag) / m
        v_max_here = np.sqrt(np.maximum(v_prev**2 + 2*a_acc*ds, 0))
        v_fwd[i] = min(v_fwd[i], v_max_here)

    return v_fwd

v_fwd = simulate(4.0, 1.1, 45, 1.7)

real_dist = tel["Distance"].to_numpy()
real_speed = tel["Speed"].to_numpy() / 3.6
real_on_grid = np.interp(s_uniform, real_dist, real_speed)

plt.figure()
plt.plot(s_uniform, v_fwd, label="my sim")
plt.plot(s_uniform, real_on_grid, label="Verstappen Pole Lap")
plt.xlabel("distance (m)")
plt.ylabel("speed (m/s)")
plt.legend()

ds_all = np.diff(s_uniform)
v_avg = 0.5 * (v_fwd[:-1] + v_fwd[1:])
lap_time = np.sum(ds_all / v_avg)
print("Lap time:", lap_time, "seconds")
