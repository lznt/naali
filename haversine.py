#!/usr/bin/env python

# Haversine formula example in Python
# Author: Wayne Dyck
# CalcLat calculates the Latitude in Meters and CalcLong calculates the Longitude in meters

#file haversine.py

import math

def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d
	

def calcLong(lon1, lon2, lat1, lat2):

	radius = 6371 # km
	
	dlat = 0
	dlon = math.radians(lon2-lon1)
	a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = radius * c	
	
	longitudeInMeters = d * 1000
	
	return longitudeInMeters

	

def calcLat(lat1, lat2):
	
	radius = 6371 # km
	
	dlat = math.radians(lat2-lat1)
	dlon = 0
	
	a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = radius * c
	
	latitudeInMeters = d * 1000
	
	return latitudeInMeters
	
