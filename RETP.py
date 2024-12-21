import streamlit as st
import pandas as pd
import folium
from folium.plugins import Fullscreen
from streamlit_folium import folium_static
from geopy.distance import geodesic

# Load the datasets
real_estate_data = pd.read_csv('2024 수도권 연립 다세대 실거래가.csv')
municipal_data = pd.read_csv('2024 수도권 동사무소주소.csv')
subway_data = pd.read_csv('수도권 지하철 위치.csv')

# Preprocessing
real_estate_data.rename(columns={'Latitude': '위도', 'Longitude': '경도'}, inplace=True)
subway_data.rename(columns={'Latitude': '위도', 'Longitude': '경도'}, inplace=True)
real_estate_data.dropna(subset=['위도', '경도'], inplace=True)
subway_data.dropna(subset=['위도', '경도'], inplace=True)

# Streamlit UI
st.title("2024 수도권 실거래가 데이터")

# Sidebar for selection with dynamic visibility and default "선택"
with st.sidebar:
    st.header("지역 선택(｡•̀ᴗ-)✧")

    # Default option for all levels
    default_option = "선택"

    # 1차 구분
    level1 = st.selectbox(
        "1차 구분", 
        options=[default_option] + list(real_estate_data['1차 구분'].dropna().unique())
    )

    # 2차 구분 (조건부 표시)
    if level1 != default_option:
        level2 = st.selectbox(
            "2차 구분", 
            options=[default_option] + list(
                real_estate_data[real_estate_data['1차 구분'] == level1]['2차 구분'].dropna().unique()
            )
        )
    else:
        level2 = default_option

    # 3차 구분 (조건부 표시)
    if level2 != default_option:
        level3 = st.selectbox(
            "3차 구분", 
            options=[default_option] + list(
                real_estate_data[
                    (real_estate_data['1차 구분'] == level1) & 
                    (real_estate_data['2차 구분'] == level2)
                ]['3차 구분'].dropna().unique()
            )
        )
    else:
        level3 = default_option

    # 4차 구분 (조건부 표시)
    if level3 != default_option:
        level4_options = list(
            real_estate_data[
                (real_estate_data['1차 구분'] == level1) & 
                (real_estate_data['2차 구분'] == level2) & 
                (real_estate_data['3차 구분'] == level3)
            ]['4차 구분'].dropna().unique()
        )
        if level4_options:
            level4 = st.selectbox("4차 구분", options=[default_option] + level4_options)
        else:
            level4 = default_option
    else:
        level4 = default_option

    # 5차 구분 (조건부 표시)
    if level4 != default_option:
        level5_options = list(
            real_estate_data[
                (real_estate_data['1차 구분'] == level1) & 
                (real_estate_data['2차 구분'] == level2) & 
                (real_estate_data['3차 구분'] == level3) & 
                (real_estate_data['4차 구분'] == level4)
            ]['5차 구분'].dropna().unique()
        )
        if level5_options:
            level5 = st.selectbox("5차 구분", options=[default_option] + level5_options)
        else:
            level5 = default_option
    else:
        level5 = default_option

# Filter the data based on selection
filtered_real_estate = real_estate_data.copy()

# Apply filters dynamically for each level
if level1 != default_option:
    filtered_real_estate = filtered_real_estate[filtered_real_estate['1차 구분'] == level1]
if level2 != default_option:
    filtered_real_estate = filtered_real_estate[filtered_real_estate['2차 구분'] == level2]
if level3 != default_option:
    filtered_real_estate = filtered_real_estate[filtered_real_estate['3차 구분'] == level3]
if level4 != default_option:
    filtered_real_estate = filtered_real_estate[filtered_real_estate['4차 구분'] == level4]
if level5 != default_option:
    filtered_real_estate = filtered_real_estate[filtered_real_estate['5차 구분'] == level5]

# Display filters and sliders
st.markdown("### ( ͡͡° ͜ ʖ ͡ °)표시할 정보 선택")

subjects = {
    "전용면적(㎡)": {"min": 0, "step": 0.1, "type": float},
    "대지권면적(㎡)": {"min": 0, "step": 0.1, "type": float},
    "평당가(전용면적)": {"min": 0, "step": 100, "type": float},
    "평당가(대지권)": {"min": 0, "step": 100, "type": float},
    "거래금액(억원)": {"min": 0, "step": 0.1, "type": float},
    "층": {"min": -1, "step": 1, "type": int},
}

filters = {}

# Create a grid layout with 2 columns and 3 rows
ordered_subjects = [
    ("전용면적(㎡)", "대지권면적(㎡)"),
    ("평당가(전용면적)", "평당가(대지권)"),
    ("거래금액(억원)", "층"),
]

for row in ordered_subjects:
    col1, col2 = st.columns(2)  # Create two columns for each row

    for col, config in zip([col1, col2], row):
        with col:
            if st.checkbox(f"{config} 표시", value=True):
                if config in filtered_real_estate.columns:
                    max_val = filtered_real_estate[config].max() if not filtered_real_estate.empty else subjects[config]["min"]
                    default_value = (
                        (subjects[config]["type"](subjects[config]["min"]), 
                         subjects[config]["type"](max_val))
                        if level3 != default_option
                        else (subjects[config]["type"](subjects[config]["min"]), 
                              subjects[config]["type"](subjects[config]["min"]))
                    )
                    filters[config] = st.slider(
                        f"{config} 범위 설정",
                        min_value=subjects[config]["type"](subjects[config]["min"]),
                        max_value=subjects[config]["type"](max_val),
                        value=default_value,
                        step=subjects[config]["type"](subjects[config]["step"]),
                    )
                else:
                    st.warning(f"⚠️ '{config}' 컬럼이 데이터에 존재하지 않습니다.")

for col, (min_val, max_val) in filters.items():
    filtered_real_estate = filtered_real_estate[
        (filtered_real_estate[col] >= min_val) & (filtered_real_estate[col] <= max_val)
    ]

# Map visualization
map_center = [37.5665, 126.9780]  # Default center (Seoul City Hall coordinates)
if level3 == default_option or filtered_real_estate.empty:
    center_location = map_center
    zoom_start = 15  # Default zoom for neighborhoods
else:
    center_location = [filtered_real_estate['위도'].mean(), filtered_real_estate['경도'].mean()]
    zoom_start = 13  # Normal zoom when data is available

selection_map = folium.Map(location=center_location, zoom_start=zoom_start)

Fullscreen().add_to(selection_map)

# Add markers for real estate data
if level3 != default_option:
    for _, row in filtered_real_estate.iterrows():
        popup_content = "<br>".join([f"<b>{col}:</b> {row[col]}" for col in filters.keys()])
        popup = folium.Popup(popup_content, max_width=300)
        folium.Marker(
            location=[row['위도'], row['경도']],
            popup=popup,
            icon=folium.Icon(color="red", icon="home"),
        ).add_to(selection_map)

        # Find nearest subway stations (within 3 km)
        real_estate_location = (row['위도'], row['경도'])
        subway_data['distance'] = subway_data.apply(
            lambda x: geodesic(real_estate_location, (x['위도'], x['경도'])).meters, axis=1
        )
        nearest_subways = subway_data[subway_data['distance'] <= 3000].nsmallest(3, 'distance')
        if nearest_subways.empty:
            zoom_start = 16  # Adjust zoom if no subway stations nearby
        for _, subway_row in nearest_subways.iterrows():
            folium.Marker(
                location=[subway_row['위도'], subway_row['경도']],
                popup=folium.Popup(f"<b>지하철역:</b> {subway_row['지하철역']}<br><b>노선:</b> {subway_row['노선명']}", max_width=250),
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(selection_map)

folium_static(selection_map)

st.write("맵의 중심은 선택된 데이터를 기반으로 설정됩니다.( ͡ᵔ ͜ʖ ͡ᵔ )")
