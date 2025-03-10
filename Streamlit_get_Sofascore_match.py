import pandas as pd
import streamlit as st
import ScraperFC
import LanusStats as ls
from io import BytesIO

# Crear una instancia del objeto Sofascore
sofascore = ScraperFC.Sofascore()
sofascore_ls = ls.SofaScore()

# Configuración de la página de Streamlit
st.title("Scraping de Datos de Partidos de Fútbol")
st.write("Esta aplicación realiza scraping de datos de partidos de fútbol desde Sofascore y permite descargar los datos en un archivo Excel.")

# Pedir el match_id al usuario
match_id = st.text_input("Introduce el ID del partido:")

if st.button("Obtener Datos y Generar Excel"):
    try:
        # Obtener datos del partido
        match_stats = sofascore.scrape_team_match_stats(match_id)
        player_stats = sofascore.scrape_player_match_stats(match_id)
        average_positions = sofascore.scrape_player_average_positions(match_id)
        match_url = sofascore.get_match_url_from_id(match_id)
        match_shotmap_df = sofascore_ls.get_match_shotmap(match_url)
        match_momentum = sofascore.scrape_match_momentum(match_id)
        heatmap_data = sofascore.scrape_heatmaps(match_id)

        heatmap_list = [{"player": pid, "heatmap": heatmap} for pid, heatmap in heatmap_data.items()] if heatmap_data else []
        df_heatmaps = pd.DataFrame(heatmap_list) if heatmap_list else pd.DataFrame(columns=["player", "heatmap"])

        # Función para eliminar columnas duplicadas
        def remove_duplicate_columns(df):
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                cols[cols[cols == dup].index.tolist()] = [
                    f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))
                ]
            df.columns = cols
            return df

        # Limpiar DataFrames
        match_stats = remove_duplicate_columns(match_stats)
        player_stats = remove_duplicate_columns(player_stats)
        average_positions = remove_duplicate_columns(average_positions)
        match_shotmap_df = remove_duplicate_columns(match_shotmap_df)
        match_momentum = remove_duplicate_columns(match_momentum)
        df_heatmaps = remove_duplicate_columns(df_heatmaps)

        # Guardar en memoria en lugar de archivo local
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            match_stats.to_excel(writer, sheet_name='Team Stats', index=False)
            player_stats.to_excel(writer, sheet_name='Player Stats', index=False)
            average_positions.to_excel(writer, sheet_name='Average Positions', index=False)
            match_shotmap_df.to_excel(writer, sheet_name='Shotmap', index=False)
            match_momentum.to_excel(writer, sheet_name='Match Momentum', index=False)
            if not df_heatmaps.empty:
                df_heatmaps.to_excel(writer, sheet_name='Heatmap', index=False)
        
        output.seek(0)
        
        st.success("Datos obtenidos con éxito.")
        
        # Vista previa
        st.subheader("Vista Previa de los Datos")
        st.write("### Team Stats")
        st.dataframe(match_stats.head())

        st.write("### Player Stats")
        st.dataframe(player_stats.head())

        st.write("### Average Positions")
        st.dataframe(average_positions.head())

        st.write("### Shotmap")
        st.dataframe(match_shotmap_df.head())

        st.write("### Match Momentum")
        st.dataframe(match_momentum.head())

        if not df_heatmaps.empty:
            st.write("### Heatmap")
            st.dataframe(df_heatmaps.head())

        # Botón para descargar el archivo Excel
        st.download_button(
            label="Descargar Archivo Excel",
            data=output,
            file_name=f'Sofascore_{match_id}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Error al obtener datos para el partido {match_id}: {e}")
