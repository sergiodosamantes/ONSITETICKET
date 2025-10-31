import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sqlite3

DATABASE_FILE = 'servicedesk.db'

SCHAEFFLER_LOGO_URL = "https://companieslogo.com/img/orig/SHA0.DE_BIG-9a486b35.png?t=1720244493&download=true"

st.set_page_config(page_title="Dashboard de Satisfacción", layout="wide")

@st.cache_data
def load_data():
    """Carga y pre-procesa los datos de calificaciones desde SQLite."""
    try:
        with sqlite3.connect(DATABASE_FILE) as con:
            df = pd.read_sql_query("SELECT * FROM ratings", con)
            
        if df.empty:
            st.error("No se encontraron datos de calificaciones en la base de datos.")
            return pd.DataFrame()
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        return df
        
    except pd.io.sql.DatabaseError:
        st.error(f"No se encontró la tabla 'ratings' en la base de datos '{DATABASE_FILE}'. Asegúrate de que el backend (api.py) se haya ejecutado al menos una vez y haya recibido una calificación.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar los datos: {e}")
        return pd.DataFrame()

def setup_sidebar_filters(df):
    """Configura los filtros en la barra lateral y devuelve los valores seleccionados."""
    st.sidebar.header("Filtros")
    
    all_years = ["Todos"] + sorted(df['year'].unique().tolist())
    selected_year = st.sidebar.selectbox("Año", all_years)
    
    all_months = ["Todos"] + sorted(df['month'].unique().tolist())
    selected_month = st.sidebar.selectbox("Mes", all_months)

    min_date = df['date'].min() if not df.empty else datetime.date.today()
    max_date = df['date'].max() if not df.empty else datetime.date.today()
    
    date_range = st.sidebar.date_input(
        "Selecciona un rango de fechas",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    return selected_year, selected_month, date_range

def filter_dataframe(df, year, month, date_range):
    """Filtra el DataFrame basado en las selecciones del usuario."""
    filtered_df = df.copy()
    
    if year != "Todos":
        filtered_df = filtered_df[filtered_df['year'] == year]
        
    if month != "Todos":
        filtered_df = filtered_df[filtered_df['month'] == month]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
        
    return filtered_df

def plot_satisfaction_trend(df):
    """(NUEVO) Grafica la tendencia de satisfacción usando una media móvil."""
    st.subheader("Tendencia de Satisfacción (Media Móvil)")

    trend_df = df.dropna(subset=['value']).sort_values('timestamp')
    
    if trend_df.empty:
        st.info("No hay datos numéricos de calificación (happy, neutral, sad) para mostrar la tendencia.")
        return
        
    trend_df['rolling_avg'] = trend_df['value'].rolling(window=5, min_periods=1).mean()
    
    fig_line = px.line(
        trend_df, 
        x='timestamp', 
        y='rolling_avg', 
        title="Satisfacción Promedio a lo largo del tiempo",
        labels={'timestamp': 'Fecha', 'rolling_avg': 'Satisfacción Promedio (1=Triste, 3=Feliz)'}
    )

    fig_line.update_yaxes(range=[1, 3])
    st.plotly_chart(fig_line, use_container_width=True)

def plot_rating_distribution(df):
    """Grafica la distribución de calificaciones (pie chart)."""
    st.subheader("Distribución de Calificaciones")
    rating_counts = df['rating'].value_counts().reset_index()
    rating_counts.columns = ['rating', 'count']
    fig_pie = px.pie(
        rating_counts, 
        names='rating', 
        values='count', 
        color='rating',
        color_discrete_map={'happy':'green', 'neutral':'orange', 'sad':'red'},
        hole=.3
    )
    st.plotly_chart(fig_pie, use_container_width=True)

def plot_daily_ratings(df):
    """Grafica las calificaciones diarias (bar chart)."""
    st.subheader("Calificaciones a lo largo del tiempo")
    daily_counts = df.groupby(['date', 'rating']).size().reset_index(name='count')
    fig_bar = px.bar(
        daily_counts, 
        x='date', 
        y='count', 
        color='rating',
        barmode='group',
        labels={'date': 'Fecha', 'count': 'Número de Calificaciones'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def main():
    col1, col2 = st.columns([4, 1]) 
    
    with col1:
        st.title("Dashboard de Satisfacción del Usuario")
        st.markdown("Análisis de la experiencia del usuario de IT Service Desk.")
    
    with col2:
        st.image(SCHAEFFLER_LOGO_URL, width=450)
  
  
    df = load_data()

    if df.empty:
        st.warning("No hay datos de calificaciones para mostrar.")
        return

    selected_year, selected_month, date_range = setup_sidebar_filters(df)
    filtered_df = filter_dataframe(df, selected_year, selected_month, date_range)

    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
      
        plot_satisfaction_trend(filtered_df)
        
       
        col1, col2 = st.columns(2)
        with col1:
            plot_rating_distribution(filtered_df)
        with col2:
            plot_daily_ratings(filtered_df)

        st.subheader("Datos de Calificaciones (Filtrados)")
        st.dataframe(filtered_df)

if __name__ == "__main__":
    main()