import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
import io
from google_analytics import inject_ga

st.set_page_config(page_title="AlcaTools by AlvaroCC", layout='wide')
inject_ga()

@st.cache_data
def load_player_stats(input_dir):
    player_stats_list = []
    for file in os.listdir(input_dir):
        if file.endswith(".xlsx"):  
            file_path = os.path.join(input_dir, file)
            try:
                df = pd.read_excel(file_path, sheet_name="Player Stats")
                df["source_file"] = file  
                df_filtered = df[["id", "shortName", "minutesPlayed", "position", "goalAssist", 
                                  "accuratePass", "keyPass", "accurateCross", "accurateLongBalls", "teamName"]].copy()
                df_filtered.rename(columns={"teamName": "Equipo"}, inplace=True)
                df_filtered["Equipo"].replace("Universidad Técnica de Cajamarca", "UTC", inplace=True)
                player_stats_list.append(df_filtered)
            except Exception as e:
                st.error(f"Error leyendo {file}: {e}")
    
    if player_stats_list:
        return pd.concat(player_stats_list, ignore_index=True).fillna(0)
    else:
        st.error("No se encontraron archivos Excel con la hoja 'Player Stats'.")
        st.stop()

@st.cache_data
def preprocess_data(df, min_minutes_played):
    df = df.groupby(["id", "shortName", "position", "Equipo"], as_index=False).sum()
    df = df[df["minutesPlayed"] >= min_minutes_played]
    return df[df["position"] == "M"].copy()

@st.cache_data
def normalize_per_90(df, metrics):
    df = df.copy()
    for metric in metrics:
        df[f"{metric}_per90"] = (df[metric] / df["minutesPlayed"]) * 90
    return df

def plot_metrics(df, metrics, metric_labels, per90=True):
    sns.set_theme(style="dark", rc={"axes.facecolor": "#121212", "figure.facecolor": "#121212", "axes.edgecolor": "none"})
    fig, axes = plt.subplots(len(metrics), 1, figsize=(20, 12))
    fig.patch.set_alpha(0)

    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        column = f"{metric}_per90" if per90 else metric

        cmap = sns.color_palette("Blues_r", as_cmap=True)  
        sns.swarmplot(
            x=df[column], 
            y=[label] * len(df),  
            ax=axes[i],
            hue=df[column],  
            palette=cmap,  
            alpha=0.7,  
            size=13,
            legend=None
        )

        mean_value = df[column].mean()
        top_players = df.nlargest(5, column)
        table_data = [[row["shortName"], row["Equipo"], f"{row[column]:.2f}" if per90 else f"{int(row[column])}"] for _, row in top_players.iterrows()]
        
        table = axes[i].table(
            cellText=table_data,
            colLabels=["Jugador", "Equipo", label[:16]],
            colColours=["#444444"] * 3,
            cellLoc='center',
            loc='right',
            bbox=[1.05, 0, 0.5, 1.4]  
        )
        
        for key, cell in table.get_celld().items():
            cell.set_edgecolor("black")
            font_size = 15 if key[0] == 0 else 12
            cell.set_fontsize(font_size)
            cell.set_text_props(weight='bold', color='yellow' if key[0] == 0 else 'black', fontsize=font_size)
        
        axes[i].axvline(mean_value, color="yellow", linestyle="dashed", linewidth=2, label="Promedio")
        axes[i].set_title(label, fontsize=14, color="white", loc="left", weight='bold')
        axes[i].set_xlim(left=0, right=df[column].max() + 1)
        axes[i].tick_params(axis='x', colors='white')
        axes[i].patch.set_alpha(0)

    title_text = "por 90 minutos jugados" if per90 else "valores totales"
    plt.suptitle(
        f"TOP 5 MEDIOCAMPISTAS | Estadísticas {title_text} | LIGA 1 PERÚ",
        fontsize=30, 
        color="white", 
        weight="bold",
        x=0.7
    )
    fig.subplots_adjust(hspace=0.8)
    return fig  

st.title("Análisis de Mediocampistas | Liga 1 Perú 2025")

input_dir = "Sofascore_2025/Liga 1 2025"

with st.form(key="filter_form"):
    num_semanas = 4
    max_minutes_played = 90 * num_semanas
    half_max_minutes_played = int(round(max_minutes_played / 2, 1))
    min_minutes_played = st.slider("Selecciona el mínimo de minutos jugados", 90, max_minutes_played, half_max_minutes_played, step=5)
    metric_choice = st.radio("Selecciona el tipo de métrica:", ["Totales","Por 90 minutos"])
    submit_button = st.form_submit_button(label="Imprimir gráfico")

if submit_button:
    metrics = ["keyPass", "accuratePass", "accurateLongBalls", "accurateCross"]
    metric_labels = ["Pases de Gol", "Pases Precisos", "Balones Largos Precisos", "Centros Precisos"]
    
    df = load_player_stats(input_dir)
    midfielders = preprocess_data(df, min_minutes_played)
    midfielders_per90 = normalize_per_90(midfielders, metrics)
    
    fig = plot_metrics(midfielders_per90 if metric_choice == "Por 90 minutos" else midfielders, metrics, metric_labels, per90=(metric_choice == "Por 90 minutos"))
    st.pyplot(fig)
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    buf.seek(0)
    st.download_button("Descargar gráfico", buf, file_name="top5_mediocentros_L1.png", mime="image/png")