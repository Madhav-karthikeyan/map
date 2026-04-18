import streamlit as st
import folium
from streamlit_folium import st_folium
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# ==========================
# CONFIG
# ==========================
st.set_page_config(layout="wide")
st.title("🌍 Climate Spatial Projection Explorer")

# ==========================
# LOAD DATA
# ==========================
@st.cache_data
def load_data():
    ds = xr.open_dataset("data/tas_sample.nc")
    temp = ds["tas"]

    # Convert Kelvin → Celsius if needed
    if temp.mean() > 100:
        temp = temp - 273.15

    return temp

temp = load_data()

# ==========================
# CLICKABLE MAP
# ==========================
st.subheader("📍 Select a Region")

m = folium.Map(location=[20, 0], zoom_start=2)

map_data = st_folium(m, width=700, height=400)

# Default location
lat, lon = 35.0, 139.0

if map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

st.write(f"Selected Location: {lat:.2f}, {lon:.2f}")

# ==========================
# REGION SELECTION (BOX)
# ==========================
box_size = st.sidebar.slider("Region Size (degrees)", 1, 10, 5)

lat_min, lat_max = lat - box_size, lat + box_size
lon_min, lon_max = lon - box_size, lon + box_size

region = temp.sel(
    lat=slice(lat_min, lat_max),
    lon=slice(lon_min, lon_max)
)

# ==========================
# TIME PERIODS
# ==========================
baseline = region.sel(time=slice("1980", "2010")).mean("time")

# ==========================
# SCENARIOS
# ==========================
scenario = st.sidebar.selectbox(
    "Scenario",
    ["SSP126", "SSP245", "SSP585"]
)

delta_map = {
    "SSP126": 1.0,
    "SSP245": 2.0,
    "SSP585": 4.0
}

delta = delta_map[scenario]

future_2040 = region.sel(time=slice("2030", "2050")).mean("time") + delta
future_2060 = region.sel(time=slice("2050", "2070")).mean("time") + delta * 1.5

# ==========================
# PLOTTING FUNCTION
# ==========================
def plot_map(data, title, vmin=None, vmax=None):
    fig, ax = plt.subplots(figsize=(5, 4))
    
    im = ax.pcolormesh(
        data.lon,
        data.lat,
        data,
        cmap="coolwarm",
        vmin=vmin,
        vmax=vmax
    )
    
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    plt.colorbar(im, ax=ax, label="°C")
    return fig

# ==========================
# DISPLAY MAPS
# ==========================
st.subheader("🗺 Spatial Temperature Maps")

col1, col2, col3 = st.columns(3)

with col1:
    st.pyplot(plot_map(baseline, "Historical"))

with col2:
    st.pyplot(plot_map(future_2040 - baseline, f"{scenario} 2040s Δ", vmin=0, vmax=5))

with col3:
    st.pyplot(plot_map(future_2060 - baseline, f"{scenario} 2060s Δ", vmin=0, vmax=7))

# ==========================
# CURRENT CONDITIONS (OPTIONAL)
# ==========================
if st.checkbox("Show Current Temperature Pattern"):
    current = region.isel(time=-1)

    st.subheader("🌡 Current Temperature")

    st.pyplot(plot_map(current, "Latest Temperature"))
