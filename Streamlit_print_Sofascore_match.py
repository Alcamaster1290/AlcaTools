import pandas as pd
import streamlit as st
import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
import matplotlib.patheffects as path_effects
from mplsoccer import Pitch
import io

# Diccionario de traducción de términos en inglés a español
translation_dict = {
    'save': 'Atajada',
    'goal': 'Gol',
    'miss': 'Fuera',
    'post': 'Palo',
    'block': 'Bloqueo',
    'penalty': 'Penal',
    'own': 'Autogol',
    'right-foot': 'Pie derecho',
    'left-foot': 'Pie izquierdo',
    'head':'Cabeza',
    'corner':'T.Esquina',
    'regular': 'Regular',
    'assisted': 'Asistido',
    'fast-break': 'Contraataque',
    'throw-in-set-piece': 'Jugada tras saque de banda',
    'free-kick' : 'Tiro libre',
    'set-piece' : 'Jugada a balon parado',
    'other' : 'Otro',
}

def translate_term(term):
    return translation_dict.get(term, term)

def procesar_tiros_y_goles(df_shotmap, df_average_positions, selected_team, opponent_team, condicion):
    """
    Procesa los tiros y goles, y los muestra en Streamlit.
    
    Parámetros:
        df_shotmap (pd.DataFrame): DataFrame con los datos de los tiros.
        df_average_positions (pd.DataFrame): DataFrame con las posiciones promedio de los jugadores.
        selected_team (str): Nombre del equipo seleccionado.
        opponent_team (str): Nombre del equipo oponente.
        condicion (str): Condición del equipo seleccionado ("Local" o "Visitante").
    
    Retorna:
        dict: Diccionario con los DataFrames de tiros al arco y fuera del arco para ambos equipos.
    """
    # Aplicar colores basados en el tipo de tiro
    df_shotmap['color'] = df_shotmap['shotType'].apply(apply_color_based_on_shot_type)
    
    # Definir categorías de tiros
    shots_on_target = ['save', 'goal']  # Tiros al arco
    shots_off_target = ['miss', 'post', 'block']  # Tiros fuera del arco
    
    # Filtrar tiros al arco y fuera del arco
    df_shots_on_target = df_shotmap[df_shotmap['shotType'].isin(shots_on_target)]
    df_shots_off_target = df_shotmap[df_shotmap['shotType'].isin(shots_off_target)]
    
    # Separar tiros al arco y fuera del arco por equipo local y visitante
    df_shots_on_target_selected = df_shots_on_target[df_shots_on_target['isHome'] == (condicion == "Local")]
    df_shots_on_target_opponent = df_shots_on_target[df_shots_on_target['isHome'] != (condicion == "Local")]
    df_shots_off_target_selected = df_shots_off_target[df_shots_off_target['isHome'] == (condicion == "Local")]
    df_shots_off_target_opponent = df_shots_off_target[df_shots_off_target['isHome'] != (condicion == "Local")]
    
    # Procesar goles
    goals_df = df_shotmap[df_shotmap['shotType'] == 'goal']
    
    if not goals_df.empty:
        # Extraer y mostrar los goles
        st.subheader("Goles")
        goals_df = goals_df.sort_values(by='time')
        goles_por_equipo = {selected_team: [], opponent_team: []}

        for _, row in goals_df.iterrows():
            minute = f"{row['time']}'"
            if 'addedTime' in row and not pd.isna(row["addedTime"]):  # Verificar si hay tiempo añadido
                minute = f"{row['time']}+{int(row['addedTime'])}'"
            if row['situation'] == 'penalty':
                minute += " (Penal)"
            if row['goalType'] == 'own':
                minute += " (AG)"
            
            # Determinar el equipo según las condiciones
            if row["isHome"]:
                equipo = selected_team if condicion == "Local" else opponent_team
            else:
                equipo = opponent_team if condicion == "Local" else selected_team
            
            # Agregar al equipo correspondiente
            goles_por_equipo[equipo].append(f"{row['name']} - {minute}")
        
        e1, e2 = st.columns(2)
        
        # Mostrar goles en columnas
        equipos = [(selected_team if condicion == "Local" else opponent_team, e1), 
                   (opponent_team if condicion == "Local" else selected_team, e2)]

        for equipo, column in equipos:
            with column:
                for gol in goles_por_equipo[equipo]:
                    st.markdown(f"- {gol}")

    st.divider()

    # Devolver los DataFrames de tiros al arco y fuera para ambos equipos
    return {
        'tiros_al_arco_local': df_shots_on_target_selected,
        'tiros_al_arco_away': df_shots_on_target_opponent,
        'tiros_fuera_local': df_shots_off_target_selected,
        'tiros_fuera_away': df_shots_off_target_opponent
    }

# Función para aplicar colores basados en el tipo de tiro
def apply_color_based_on_shot_type(shot_type):
    if shot_type == 'block':
        return 'coral'
    elif shot_type == 'miss':
        return 'darkred'
    elif shot_type == 'goal':
        return 'darkgreen'
    elif shot_type in ['save', 'post']:
        return 'darkgoldenrod'
    else:
        return 'gray'

def graficar_todos_los_tiros(df_local, df_visitante):
    """
    Grafica todos los tiros (al arco y fuera) diferenciados por equipo y color.
    Los goles se grafican con un tamaño mayor.
    
    Parámetros:
        df_local (pd.DataFrame): DataFrame con los tiros del equipo local.
        df_visitante (pd.DataFrame): DataFrame con los tiros del equipo visitante.
    """
    # Crear el campo de juego con color azul oscuro
    pitch = Pitch(
        pitch_type='opta',
        pitch_color='#112548',  # Color de la cancha en formato hexadecimal (azul oscuro)
        goal_type='box',
        linewidth=2,
        line_color='white',
        pitch_length=105,
        pitch_width=68
    )

    # Configuración de la figura
    fig, axs = pitch.grid(
        figheight=10, title_height=0, endnote_space=0,
        title_space=0, axis=False, grid_height=0.82,
        endnote_height=0.01, grid_width=0.8,
    )

    # Cambiar el fondo de la figura y el área del gráfico a negro
    fig.patch.set_facecolor('black')  # Fondo de la figura
    axs['pitch'].set_facecolor('black')  # Fondo del área del gráfico

    # Ajustar coordenadas para el equipo visitante (espejo)
    df_visitante['x'] = 100 - df_visitante['x']
    df_visitante['y'] = 100 - df_visitante['y']

    # Combinar dataframes para iterar y graficar ambos equipos
    df_local['team'] = 'Local'
    df_visitante['team'] = 'Visitante'
    df_combined = pd.concat([df_visitante, df_local])

    # Aplicar traducciones a las columnas relevantes en df_combined
    df_combined['shotType'] = df_combined['shotType'].apply(translate_term)
    df_combined['situation'] = df_combined['situation'].apply(translate_term)
    df_combined['bodyPart'] = df_combined['bodyPart'].apply(translate_term)
    df_combined['goalType'] = df_combined['goalType'].apply(translate_term)

    # Ajustar el tamaño de los puntos según el tipo de tiro
    df_combined['size'] = df_combined['shotType'].apply(lambda x: 300 if x == 'goal' else 200)

    # Dibujar hexbin y scatter
    hexmap = pitch.hexbin(
        x=df_combined['x'],
        y=df_combined['y'],
        ax=axs['pitch'],
        edgecolors='none',
        gridsize=(15, 8),
        cmap='PuBu',
        alpha=0.4
    )
    scatter = pitch.scatter(
        x=df_combined['x'],
        y=df_combined['y'],
        ax=axs['pitch'],
        color=df_combined['color'],
        s=df_combined['size'],  # Usar el tamaño definido en la columna 'size'
        edgecolors='black',
        zorder=2,
        alpha=.9
    )

    # Anotar los tiempos sobre el gráfico con borde negro
    for i, row in df_combined.iterrows():
        axs['pitch'].annotate(
            str(row['jerseyNumber']),
            (row['x'], row['y']),
            color='white',
            ha='center',
            va='center',
            fontsize=8,
            weight='bold',
            zorder=3,
            path_effects=[
                path_effects.withStroke(linewidth=1, foreground='black')
            ]
        )

    # Título del gráfico
    fig.suptitle(
        'Mapa de tiros del partido',  # Texto del título
        fontsize=28,  # Tamaño de la fuente
        color='yellow',  # Color del texto
        y=0.95,  # Posición vertical del título
        fontweight='bold',  # Grosor de la fuente
        path_effects=[  # Efecto de borde en el texto
            path_effects.withStroke(linewidth=3, foreground='black')
        ]
    )

    # Crear las listas de leyenda divididas por tiempo y equipo
    legend_local_0_45 = []
    legend_local_46_90 = []
    legend_visitante_0_45 = []
    legend_visitante_46_90 = []

    for _, row in df_combined.iterrows():
        color = row['color']
        jersey_number = int(row['jerseyNumber']) if not pd.isna(row['jerseyNumber']) else 'N/A'
        patch = mpatches.Patch(
            facecolor=color,
            edgecolor='black',
            label=f"{row['time']}' {row['name']} #{jersey_number} - {row['bodyPart']} | {row['situation']} | {row['shotType']}"
        )
        if row['team'] == 'Local' and 0 <= row['time'] <= 45:
            legend_local_0_45.append(patch)
        elif row['team'] == 'Local' and 46 <= row['time'] <= 90:
            legend_local_46_90.append(patch)
        elif row['team'] == 'Visitante' and 0 <= row['time'] <= 45:
            legend_visitante_0_45.append(patch)
        elif row['team'] == 'Visitante' and 46 <= row['time'] <= 90:
            legend_visitante_46_90.append(patch)

    # Ordenar las leyendas por 'time' de mayor a menor
    legend_local_0_45.sort(key=lambda x: int(x.get_label().split("'")[0]), reverse=True)
    legend_local_46_90.sort(key=lambda x: int(x.get_label().split("'")[0]), reverse=True)
    legend_visitante_0_45.sort(key=lambda x: int(x.get_label().split("'")[0]), reverse=True)
    legend_visitante_46_90.sort(key=lambda x: int(x.get_label().split("'")[0]), reverse=True)

    # Leyendas para cada categoría
    if legend_local_0_45:
        legend1 = axs['pitch'].legend(
            handles=legend_local_0_45,
            loc='upper left',
            title="Local 1.T.",
            frameon=True,
            fontsize=8,
            facecolor='white',  # Fondo de la leyenda
            edgecolor='white',  # Borde de la leyenda
            labelcolor='black',  # Color del texto de la leyenda
        )
        legend1.get_frame().set_alpha(0.5)  # Modificar la opacidad del fondo de la leyenda
        axs['pitch'].add_artist(legend1)

    if legend_local_46_90:
        legend2 = axs['pitch'].legend(
            handles=legend_local_46_90,
            loc='lower left',
            title="Local 2.T.",
            frameon=True,
            fontsize=8,
            facecolor='white',  # Fondo de la leyenda
            edgecolor='white',  # Borde de la leyenda
            labelcolor='black',  # Color del texto de la leyenda
        )
        legend2.get_frame().set_alpha(0.5)  # Modificar la opacidad del fondo de la leyenda
        axs['pitch'].add_artist(legend2)

    if legend_visitante_0_45:
        legend3 = axs['pitch'].legend(
            handles=legend_visitante_0_45,
            loc='upper right',
            title="Visitante 1.T.",
            frameon=True,
            fontsize=8,
            facecolor='white',  # Fondo de la leyenda
            edgecolor='white',  # Borde de la leyenda
            labelcolor='black',  # Color del texto de la leyenda
        )
        legend3.get_frame().set_alpha(0.5)  # Modificar la opacidad del fondo de la leyenda
        axs['pitch'].add_artist(legend3)

    if legend_visitante_46_90:
        legend4 = axs['pitch'].legend(
            handles=legend_visitante_46_90,
            loc='lower right',
            title="Visitante 2.T.",
            frameon=True,
            fontsize=8,
            facecolor='white',  # Fondo de la leyenda
            edgecolor='white',  # Borde de la leyenda
            labelcolor='black'  # Color del texto de la leyenda
        )
        legend4.get_frame().set_alpha(0.4)  # Modificar la opacidad del fondo de la leyenda
        axs['pitch'].add_artist(legend4)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    return fig

# Ejemplo de uso en Streamlit
uploaded_file = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Leer el archivo Excel
        xls = pd.ExcelFile(uploaded_file)

        # Asignar cada hoja a un DataFrame
        df_team_stats = pd.read_excel(xls, sheet_name='Team Stats')
        df_player_stats = pd.read_excel(xls, sheet_name='Player Stats')
        df_average_positions = pd.read_excel(xls, sheet_name='Average Positions')
        df_shotmap = pd.read_excel(xls, sheet_name='Shotmap')
        df_match_momentum = pd.read_excel(xls, sheet_name='Match Momentum')
        
        # Verificar si la hoja 'Heatmap' existe antes de intentar leerla
        if 'Heatmap' in xls.sheet_names:
            df_heatmaps = pd.read_excel(xls, sheet_name='Heatmap')
        else:
            df_heatmaps = pd.DataFrame()  # DataFrame vacío si no existe la hoja

        # Procesar los tiros y goles
        selected_team = "Equipo Local"  # Cambiar por el nombre del equipo seleccionado
        opponent_team = "Equipo Visitante"  # Cambiar por el nombre del equipo oponente
        condicion = "Local"  # Cambiar por "Local" o "Visitante"

        resultados = procesar_tiros_y_goles(df_shotmap, df_average_positions, selected_team, opponent_team, condicion)

        # Combinar todos los tiros (al arco y fuera) para ambos equipos
        df_tiros_local = pd.concat([resultados['tiros_al_arco_local'], resultados['tiros_fuera_local']])
        df_tiros_visitante = pd.concat([resultados['tiros_al_arco_away'], resultados['tiros_fuera_away']])

        # Graficar todos los tiros
        fig = graficar_todos_los_tiros(df_tiros_local, df_tiros_visitante)

        # Botón para descargar la imagen
        if fig:
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            st.download_button(
                label="Descargar imagen",
                data=buf,
                file_name="mapa_de_tiros.png",
                mime="image/png"
            )

    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")