#!/usr/bin/env python3
"""Independent Euler baseline from original Hines equations and source-extracted lookups.

This code does NOT call PySD. It is a second implementation for comparison,
not a substitute for a Vensim-run reference.
"""
import math

def times(spec):
    dt=spec["dt"]; n=round((spec["stop"]-spec["start"])/dt)
    return [round(spec["start"]+i*dt,10) for i in range(n+1)]

def lookup(points,x):
    if x<=points[0][0]: return points[0][1]
    for (a,b),(c,d) in zip(points,points[1:]):
        if x<=c: return b+(d-b)*(x-a)/(c-a)
    return points[-1][1]

def delay(spec):
    stock=spec["input"]*spec["tau"]
    rows=[]
    for i,t in enumerate(times(spec)):
        inflow=spec["input"];outflow=stock/spec["tau"]
        rows.append({"time":t,"material":stock,"inflow":inflow,"outflow":outflow})
        if i<len(times(spec))-1: stock+=spec["dt"]*(inflow-outflow)
    return rows

def capacity(spec):
    ratio=spec["desired"]/spec["capacity"]
    util=lookup(spec["lookup"],ratio)
    return [{"time":t,"production":spec["capacity"]*util,
             "utilization":util,"indicated_utilization":ratio}
            for t in times(spec)]

def backlog(spec,variant):
    inventory=spec["initial_inventory"]
    backlog=spec["orders"]*spec["tau"]
    rows=[]; ts=times(spec)
    for i,t in enumerate(ts):
        orders=spec["orders"];producing=spec["production"]
        indicated=backlog/spec["tau"]
        if variant=="flow":
            maximum=inventory/spec["min_ship"]
            ratio=indicated/maximum if abs(maximum)>=1e-6 else 10.
            shipping=maximum*lookup(spec["lookup"],ratio)
        else:
            ratio=inventory/spec["initial_inventory"]
            shipping=indicated*lookup(spec["lookup"],ratio)
        rows.append({"time":t,"inventory":inventory,"backlog":backlog,
                     "orders":orders,"producing":producing,"shipping":shipping})
        if i<len(ts)-1:
            inventory+=spec["dt"]*(producing-shipping)
            backlog+=spec["dt"]*(orders-shipping)
    return rows

def baseline(name,spec):
    if name=="delay.mdl":return delay(spec)
    if name=="CapUtil.mdl":return capacity(spec)
    return backlog(spec,"flow" if name=="invbakf.mdl" else "level")
