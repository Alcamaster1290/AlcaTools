import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
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
            hue_norm=(df[column].min(), df[column].max()),  
            alpha=0.7,  
            size=11,
            legend=None
        )
        
        mean_value = df[column].mean()
        axes[i].axvline(mean_value, color="yellow", linestyle="dashed", linewidth=2, label="Promedio")
        axes[i].text(mean_value, -0.4, f"{mean_value:.2f}", color="yellow", weight='bold', fontsize=14, ha='center', va='bottom', transform=axes[i].get_xaxis_transform())
        axes[i].set_title(label, fontsize=14, color="white", loc="left", weight='bold')
        axes[i].set_ylabel("")
        axes[i].set_yticks([])
        axes[i].set_xlabel("")
        axes[i].set_xlim(left=0, right=df[column].max() + 1)
        axes[i].tick_params(axis='x', colors='white')
        axes[i].patch.set_alpha(0)
    
    title_text = "por 90 minutos jugados" if per90 else "valores totales"
    plt.suptitle(f"TOP 5 MEDIOCAMPISTAS | Estadísticas {title_text} | LIGA 1 PERÚ", fontsize=30, color="white", weight="bold", x=0.7)
    fig.subplots_adjust(hspace=0.8)
    return fig  


st.title("Análisis de Mediocampistas | Liga 1 Perú 2025")

input_dir = "Sofascore_2025/Liga 1 2025"

with st.form(key="filter_form"):
    num_semanas = 4
    max_minutes_played = 90 * num_semanas
    half_max_minutes_played = int(round(max_minutes_played / 2, 1))
    min_minutes_played = st.slider("Selecciona el mínimo de minutos jugados", 90, max_minutes_played, half_max_minutes_played, step=5)
    metric_choice = st.radio("Selecciona el tipo de métrica:", ["Por 90 minutos", "Totales"])
    submit_button = st.form_submit_button(label="Imprimir gráfico")

if submit_button:
    metrics = ["keyPass", "accuratePass", "accurateLongBalls", "accurateCross"]
    metric_labels = ["Pases de Gol", "Pases Precisos", "Balones Largos Precisos", "Centros Precisos"]
    
    df = load_player_stats(input_dir)
    midfielders = preprocess_data(df, min_minutes_played)
    midfielders_per90 = normalize_per_90(midfielders, metrics)
    
    if metric_choice == "Por 90 minutos":
        st.pyplot(plot_metrics(midfielders_per90, metrics, metric_labels, per90=True))
    else:
        st.pyplot(plot_metrics(midfielders, metrics, metric_labels, per90=False))