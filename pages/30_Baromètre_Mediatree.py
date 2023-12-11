from io import StringIO

import pandas as pd
import streamlit as st
from streamlit_tags import st_tags
import plotly.io as pio
from datetime import datetime

import quotaclimat.data_analytics.bilan as mt_bilan
import quotaclimat.data_analytics.exploration as mt_exploration
from quotaclimat.data_processing.mediatree.read_format_deduplicate import (
    deduplicate_extracts, read_and_format_one)
from quotaclimat.utils.channels import (TOP_25_CHANNELS, TOP_CHANNELS_RADIO,
                                        TOP_CHANNELS_TV)
from quotaclimat.utils.plotly_theme import THEME

st.set_page_config(
    layout="wide",
)
st.write("### Bilan d'un événement sur les données Mediatree")
st.markdown(" Cette page permet de produire un rapport analytique de couverture de mots clé. Ces analyses support seulement les formats d'extraction de Mediatree. [Voici](https://github.com/dataforgoodfr/quotaclimat/tree/main/data_public/example_mediatree_extract) un exemple d'extration.")

uploaded_files = st.sidebar.file_uploader(
    "Uploader des fichiers excel mediatree", accept_multiple_files=True, type=["xlsx"]
)


# button_analysis = st.sidebar.button("Lancer l'analyse")


@st.cache_data()
def load_data(uploaded_files):
    # TODO add deduplication

    data = []

    progress_bar = st.sidebar.progress(0)

    if len(uploaded_files) > 0:

        for i, uploaded_file in enumerate(uploaded_files):

            uploaded_file.seek(0)
            df_imported = pd.read_excel(uploaded_file)
            # st.sidebar.write(uploaded_file.name)
            df_i = read_and_format_one(
                data=df_imported,
                path_file=uploaded_file.name,
                path_channels="data/channels.xlsx",
            )

            data.append(df_i)

            progress_bar.progress(float((i + 1) / len(uploaded_files)))

        data = pd.concat(data, axis=0, ignore_index=True)
        data_unique = deduplicate_extracts(data)
        return data_unique

    else:
        return None



def add_tab2_filtering_to_fig_title(fig):
    current_title = fig_volume.layout.title.text
    updated_title = current_title + 'filtré de 6h à 10h radio et 19h à 21h TV'
    fig.update_layout(title_text=updated_title)
    return fig

data = load_data(uploaded_files)
all_figs = []

if data is not None:
    data_filtered = mt_bilan.get_filtered_data(data)

    st.sidebar.metric("Extraits trouvés", len(data))
    st.sidebar.metric("Extraits trouvés", len(data))
    tab1, tab2 = st.tabs(
        [
            "de 6h à 00h",
            "de 6h à 10h radio et 19h à 21h TV",
        ]
    )
    with tab1:
        with st.expander("Vue d'ensemble", expanded=False):
            st.markdown("## Analyse sur le total")
            for keyword in data_filtered.keyword.unique():
                media_time = mt_bilan.get_media_time(
                    data_filtered[data_filtered.keyword == keyword]
                )
                fig_volume = mt_bilan.plot_volume_mediatique(
                    media_time, keyword=keyword
                )
                st.plotly_chart(fig_volume, use_container_width=True)
                all_figs.append(fig_volume)
            st.markdown("## Classement")
            fig_clsmt_tv_c = mt_bilan.plot_classement_volume_mediatique_tv_continue(
                data_filtered
            )
            st.plotly_chart(fig_clsmt_tv_c, use_container_width=True)
            all_figs.append(fig_clsmt_tv_c)

            fig_clsmt_tv_g = mt_bilan.plot_classement_volume_mediatique_tv_generique(
                data_filtered
            )

            st.plotly_chart(fig_clsmt_tv_g, use_container_width=True)
            all_figs.append(fig_clsmt_tv_g)

            fig_clsmt_radio = mt_bilan.plot_classement_volume_mediatique_radio(
                data_filtered
            )
            st.plotly_chart(fig_clsmt_radio, use_container_width=True)
            all_figs.append(fig_clsmt_radio)

        with st.expander("Comparaison entre les sujets", expanded=False):
            st.markdown("## Classement")
            st.write("En cours de construction")

        with st.expander("Evolutions au cours du temps", expanded=False):
            st.markdown("## Volumes médiatiques")
            for keyword in data_filtered.keyword.unique():
                st.markdown("### %s" % keyword)
                data_filtered_kw = data_filtered[data_filtered.keyword == keyword]
                fig_time_volume = mt_bilan.media_volume_over_time(data_filtered_kw)
                st.plotly_chart(fig_time_volume)
                all_figs.append(fig_time_volume)

                st.markdown("## Classement")
                ranking = mt_bilan.get_ranking_evolution(data_filtered_kw)

                st.markdown("### TV d'info en continu")
                fig_ranking_tv_c = mt_bilan.show_ranking_chart(
                    ranking.query("media2=='TV - Information en continu'"),
                    "Evolution du classement des chaînes TV d'information en continu",
                    height=600,
                )
                st.plotly_chart(fig_ranking_tv_c)
                all_figs.append(fig_ranking_tv_c)

                st.markdown("### TV généraliste")
                fig_ranking_tv_g = mt_bilan.show_ranking_chart(
                    ranking.query("media2=='TV - Généraliste'"),
                    "Evolution du classement des chaînes TV généralistes",
                    height=600,
                )
                st.plotly_chart(fig_ranking_tv_g)
                all_figs.append(fig_ranking_tv_g)

                st.markdown("### Radio")
                fig_ranking_radio = mt_bilan.show_ranking_chart(
                    ranking.query("media2=='Radio'"),
                    "Evolution du classement des chaînes Radio",
                    height=800,
                )
                st.plotly_chart(fig_ranking_radio)
                all_figs.append(fig_ranking_radio)
    with tab2:
        data_filtered_radio = data_filtered.loc[
            data_filtered.channel_name.isin(TOP_CHANNELS_RADIO)
            & (data_filtered.date.dt.hour >= 6)
            & (data_filtered.date.dt.hour < 10)
        ]
        data_filtered_tv = data_filtered.loc[
            data_filtered.channel_name.isin(TOP_CHANNELS_TV)
            & (data_filtered.date.dt.hour >= 19)
            & (data_filtered.date.dt.hour < 21)
        ]
        data_filtered_high_audience = pd.concat([data_filtered_radio, data_filtered_tv])
        hour_a_day_tv = 2
        hour_a_day_radio = 4
        with st.expander("Vue d'ensemble", expanded=False):

            for keyword in data_filtered_high_audience.keyword.unique():

                media_time_ = mt_bilan.get_media_time(
                    data_filtered_high_audience[
                        data_filtered_high_audience.keyword == keyword
                    ],
                    heure_de_grande_ecoute=True,
                    hour_a_day=2,
                )
                fig_volume = mt_bilan.plot_volume_mediatique(
                    media_time_, keyword=keyword
                )
                st.plotly_chart(fig_volume, use_container_width=True)
                add_tab2_filtering_to_fig_title(fig_volume)
                all_figs.append(add_tab2_filtering_to_fig_title(fig_volume))

            st.markdown("## Classement")
            fig_clsmt_tv_c = mt_bilan.plot_classement_volume_mediatique_tv_continue(
                data_filtered_high_audience, hour_a_day=2
            )
            st.plotly_chart(fig_clsmt_tv_c, use_container_width=True)
            all_figs.append(add_tab2_filtering_to_fig_title(fig_clsmt_tv_c))
            fig_clsmt_tv_g = mt_bilan.plot_classement_volume_mediatique_tv_generique(
                data_filtered_high_audience, hour_a_day=2
            )
            st.plotly_chart(fig_clsmt_tv_g, use_container_width=True)
            all_figs.append(add_tab2_filtering_to_fig_title(fig_clsmt_tv_g))
            fig_clsmt_radio = mt_bilan.plot_classement_volume_mediatique_radio(
                data_filtered_high_audience, hour_a_day=4
            )
            st.plotly_chart(fig_clsmt_radio, use_container_width=True)
            all_figs.append(add_tab2_filtering_to_fig_title(fig_clsmt_radio))

        with st.expander("Evolutions au cours du temps", expanded=False):
            st.markdown("## Volumes médiatiques")
            for keyword in data_filtered_high_audience.keyword.unique():

                st.markdown("### %s" % keyword)
                data_filtered_kw_ = data_filtered_high_audience[
                    data_filtered_high_audience.keyword == keyword
                ]
                data_filtered_kw_tv = data_filtered_kw_[
                    data_filtered_kw_.channel_name.isin(TOP_CHANNELS_TV)
                ]
                data_filtered_kw_radio = data_filtered_kw_[
                    data_filtered_kw_.channel_name.isin(TOP_CHANNELS_RADIO)
                ]
                fig_time_volume_tv = mt_bilan.media_volume_over_time(
                    data_filtered_kw_tv,
                    hour_a_day=2,
                    title="Evolution du volume médiatique top TV %s" % keyword,
                )
                st.plotly_chart(fig_time_volume_tv)
                all_figs.append(add_tab2_filtering_to_fig_title(fig_time_volume_tv))
                fig_time_volume_radio = mt_bilan.media_volume_over_time(
                    data_filtered_kw_radio,
                    hour_a_day=4,
                    title="Evolution du volume médiatique top Radio %s" % keyword,
                )
                st.plotly_chart(fig_time_volume_radio)
                all_figs.append(add_tab2_filtering_to_fig_title(fig_time_volume_radio))


    # export the figures
    timestamp = datetime.now().strftime("%Y%m%d_%H:%M")

    html_filename = "report_%s.html"%timestamp
    with open(html_filename, "w") as f:
        for fig in all_figs:
            f.write(fig.to_html())
    with open(html_filename, 'r') as f:
        html_string = f.read()
        st.sidebar.download_button(
            label="Télécharger report",
            data=html_string,
            key="download_button",
            help="Clique pour télécharger le contenu de cette page.",
        )


else:

    st.info("Chargez un ou plusieurs fichiers Mediatree à droite pour lancer l'analyse")




