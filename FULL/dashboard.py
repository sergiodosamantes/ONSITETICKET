import streamlit as st
import pandas as pd
import plotly.express as px

RATINGS_FILE = 'ratings.csv'

st.set_page_config(page_title="Dashboard de Satisfacción", layout="wide")

st.title("📊 Dashboard de Satisfacción del Usuario")
st.markdown("Análisis de la experiencia del usuario en el Kiosco de IT Service Desk.")

try:
    # Cargar datos
    df = pd.read_csv(RATINGS_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    st.sidebar.header("Filtros")
    # Filtro de fecha
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range = st.sidebar.date_input(
        "Selecciona un rango de fechas",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filtrar dataframe
    start_date, end_date = date_range
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    if filtered_df.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
    else:
        # --- Visualizaciones ---
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de Pie (Distribución de Calificaciones)
            st.subheader("Distribución de Calificaciones")
            rating_counts = filtered_df['rating'].value_counts().reset_index()
            rating_counts.columns = ['rating', 'count']
            fig_pie = px.pie(rating_counts, names='rating', values='count', 
                             color='rating',
                             color_discrete_map={'happy':'green', 'neutral':'orange', 'sad':'red'},
                             hole=.3)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Gráfico de Barras (Calificaciones por Día)
            st.subheader("Calificaciones a lo largo del tiempo")
            daily_counts = filtered_df.groupby(['date', 'rating']).size().reset_index(name='count')
            fig_bar = px.bar(daily_counts, x='date', y='count', color='rating',
                             barmode='group',
                             labels={'date': 'Fecha', 'count': 'Número de Calificaciones'})
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Datos de Calificaciones")
        st.dataframe(filtered_df)

except FileNotFoundError:
    st.error(f"No se encontró el archivo '{RATINGS_FILE}'. Asegúrate de que el backend haya guardado alguna calificación.")
except Exception as e:
    st.error(f"Ocurrió un error al cargar los datos: {e}")